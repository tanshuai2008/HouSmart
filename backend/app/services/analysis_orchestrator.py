from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional
from uuid import UUID

from app.core.crime_scoring import compute_crime_safety_score
from app.core.rent_estimate import fetch_rent_estimate
from app.services.analysis_repository import AnalysisRepository
from app.services.census_service import CensusService
from app.services.fbi_crime_data import FbiCrimeDataClient
from app.services.flood_service import get_flood_zone_by_address, save_flood_zone_to_db
from app.services.geocode_client import GeocodeClient
from app.services.median_house_price import get_median_house_price
from app.services.noise_estimator import estimate_noise_from_address, estimate_noise_from_coordinates
from app.services.onboarding_service import get_onboarding_answers_by_user_id
from app.services.poi_service import POIService
from app.services.school_scores_service import fetch_school_scores
from app.services.transit_service import get_transit_score_by_address, save_transit_score_to_db

logger = logging.getLogger(__name__)
_crime_geocode_client = GeocodeClient()
_crime_fbi_client = FbiCrimeDataClient()

# Staged rollout switch:
# - "user_properties_only": only writes user_properties (+run row state)
# - "property_facts_only": writes user_properties + property_facts (+run row state)
# - "full": runs complete pipeline and writes all target tables
ANALYSIS_STAGE_MODE = "full"


def _source_label(payload: dict[str, Any], default: str) -> str:
    api_used = payload.get("api_used")
    if isinstance(api_used, str) and api_used.strip():
        return api_used
    source = payload.get("source")
    if isinstance(source, str) and source.strip():
        return source
    return default


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> Optional[int]:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_fips(value: Any, width: int) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    return digits.zfill(width)


def _extract_school_score(school_payload: dict[str, Any]) -> Optional[float]:
    # Prefer the new school service aggregate score, then legacy fallbacks.
    score = _to_float(
        school_payload.get("property_school_score")
        or school_payload.get("school_score")
        or school_payload.get("housmart_school_score")
    )
    if score is not None:
        return score

    schools = school_payload.get("schools")
    if not isinstance(schools, list):
        return None

    valid_scores = [
        _to_float(s.get("housmart_school_score"))
        for s in schools
        if isinstance(s, dict)
        and _to_float(s.get("housmart_school_score")) is not None
        and _to_float(s.get("s_academic")) is not None
        and s.get("level") in {"Elementary", "Middle", "High"}
    ]
    if not valid_scores:
        return None

    return round(sum(valid_scores) / len(valid_scores), 1)


def _extract_total_schools(school_payload: dict[str, Any]) -> Optional[int]:
    total = _to_int(school_payload.get("total_schools_found"))
    if total is not None:
        return total

    schools = school_payload.get("schools")
    if isinstance(schools, list):
        return len(schools)
    return None


def _tenant_quality_label(bachelor_percentage: Optional[float]) -> Optional[str]:
    if bachelor_percentage is None:
        return None
    if bachelor_percentage >= 40:
        return "High"
    if bachelor_percentage >= 25:
        return "Medium"
    return "Low"


def _compute_affordability_index(rent: Optional[float], median_income: Optional[float]) -> Optional[float]:
    if not rent or not median_income or median_income <= 0:
        return None
    return round((rent * 12.0 / median_income) * 100.0, 3)


def _compute_rent_to_price(rent: Optional[float], median_price: Optional[float]) -> Optional[float]:
    if not rent or not median_price or median_price <= 0:
        return None
    return round((rent * 12.0 / median_price) * 100.0, 3)


def _build_user_scores(
    *,
    amenity_score: Optional[float],
    transit_score: Optional[float],
    noise_score: Optional[str],
    school_score: Optional[float],
    safety_score: Optional[float],
    flood_score: Optional[float],
    onboarding: Optional[dict[str, Any]],
) -> dict[str, Any]:
    priorities = (onboarding or {}).get("priorities_ranking_ques") or []

    weights = {
        "amenity": 1.0,
        "transit": 1.0,
        "noise": 1.0,
        "school": 1.0,
        "safety": 1.0,
        "flood": 1.0,
    }

    if isinstance(priorities, list) and priorities:
        boost = [1.2, 1.15, 1.1, 1.05]
        for idx, key in enumerate(priorities[:4]):
            k = str(key).lower()
            for metric in weights:
                if metric in k:
                    weights[metric] = boost[idx]

    # Keep flood score numeric, and noise score as categorical text from endpoint.
    flood_normalized = None if flood_score is None else flood_score
    noise_normalized = (noise_score or "").strip() or None

    # Keep onboarding read in place for next scoring-version expansion; current v1 stores raw endpoint-derived scores.
    return {
        "amenity_score": amenity_score,
        "transit_score": transit_score,
        "noise_score": noise_normalized,
        "school_score": school_score,
        "safety_score": safety_score,
        "flood_score": flood_normalized,
        "scoring_version": "v1",
    }


async def analyze_property_for_user(*, user_id: UUID, address: str) -> dict[str, Any]:
    clean_address = address.strip()
    if not clean_address:
        raise ValueError("address is required")

    rent_data = fetch_rent_estimate(address=clean_address)
    subject = rent_data.get("subject_property") or {}

    logger.debug(
        "analysis_stage=%s rent_estimate_keys=%s subject_property_keys=%s comparables_count=%s",
        ANALYSIS_STAGE_MODE,
        list(rent_data.keys()),
        list(subject.keys()),
        len(rent_data.get("comparables") or []),
    )

    normalized_address = (
        subject.get("formattedAddress")
        or subject.get("formatted_address")
        or subject.get("address")
        or clean_address
    )
    latitude = _to_float(subject.get("latitude") or subject.get("lat"))
    longitude = _to_float(subject.get("longitude") or subject.get("lon") or subject.get("lng"))
    state_fips = _normalize_fips(subject.get("stateFips") or subject.get("state_fips"), 2)
    county_fips = _normalize_fips(subject.get("countyFips") or subject.get("county_fips"), 5)

    property_row = AnalysisRepository.upsert_user_property(
        user_id=str(user_id),
        address=clean_address,
        normalized_address=normalized_address,
        latitude=latitude,
        longitude=longitude,
        rent=_to_float(rent_data.get("rent")),
        rent_currency=rent_data.get("currency") or "USD",
        property_type=subject.get("propertyType") or subject.get("property_type"),
        bedrooms=_to_int(subject.get("bedrooms")),
        bathrooms=_to_float(subject.get("bathrooms")),
        square_footage=_to_int(subject.get("squareFootage") or subject.get("square_footage")),
        year_built=_to_int(subject.get("yearBuilt") or subject.get("year_built")),
        last_sale_date=subject.get("lastSaleDate") or subject.get("last_sale_date"),
        last_sale_price=_to_float(subject.get("lastSalePrice") or subject.get("last_sale_price")),
        state_fips=state_fips,
        county_fips=county_fips,
    )
    logger.debug(
        "user_properties_mapped user_id=%s property_id=%s address=%s normalized_address=%s lat=%s lng=%s rent=%s currency=%s property_type=%s bedrooms=%s bathrooms=%s sqft=%s year_built=%s last_sale_date=%s last_sale_price=%s",
        str(user_id),
        property_row.get("property_id"),
        clean_address,
        normalized_address,
        latitude,
        longitude,
        _to_float(rent_data.get("rent")),
        rent_data.get("currency") or "USD",
        subject.get("propertyType") or subject.get("property_type"),
        _to_int(subject.get("bedrooms")),
        _to_float(subject.get("bathrooms")),
        _to_int(subject.get("squareFootage") or subject.get("square_footage")),
        _to_int(subject.get("yearBuilt") or subject.get("year_built")),
        subject.get("lastSaleDate") or subject.get("last_sale_date"),
        _to_float(subject.get("lastSalePrice") or subject.get("last_sale_price")),
    )

    property_id = property_row["property_id"]
    run = AnalysisRepository.create_run(property_id=property_id)
    run_id = run["run_id"]

    if ANALYSIS_STAGE_MODE == "user_properties_only":
        AnalysisRepository.set_run_status(run_id=run_id, status="completed")
        logger.info(
            "analysis_stage user_properties_only completed run_id=%s property_id=%s",
            run_id,
            property_id,
        )
        return {
            "run_id": run_id,
            "property_id": property_id,
            "status": "completed",
        }

    try:
        location_payload = CensusService.get_location_data(clean_address) or {}
        lat_for_amenity = latitude if latitude is not None else _to_float(location_payload.get("latitude"))
        lng_for_amenity = longitude if longitude is not None else _to_float(location_payload.get("longitude"))

        def _safe_call(fn, *args, default=None, label: str = "unknown"):
            try:
                return fn(*args)
            except Exception as exc:
                logger.warning("analysis_safe_call_failed label=%s error=%s", label, exc)
                return default if default is not None else {}

        def _compute_crime_for_analyze(input_address: str) -> dict[str, Any]:
            # Match /api/crime_score route behavior by reusing shared clients.
            return compute_crime_safety_score(
                input_address,
                geocode_client=_crime_geocode_client,
                fbi_client=_crime_fbi_client,
            )

        median_price_payload = _safe_call(
            get_median_house_price, clean_address, default={}, label="median_property_price"
        ) or {}
        income_payload = _safe_call(
            CensusService.get_income_by_address, clean_address, default={}, label="median_income"
        ) or {}
        education_payload = _safe_call(
            CensusService.get_education_by_address, clean_address, default={}, label="education_level"
        ) or {}
        crime_payload = _compute_crime_for_analyze(clean_address) or {}
        amenity_payload = (
            _safe_call(
                POIService().compute_all_categories,
                lat_for_amenity,
                lng_for_amenity,
                default={},
                label="amenity_score",
            ) or {}
            if lat_for_amenity is not None and lng_for_amenity is not None
            else {}
        )
        noise_payload = _safe_call(
            estimate_noise_from_address, clean_address, default={}, label="noise_estimate_score"
        ) or {}
        school_payload = _safe_call(
            fetch_school_scores, clean_address, default={}, label="school_scores"
        ) or {}

        async def _safe_async_call(coro, label: str) -> dict[str, Any]:
            try:
                return await coro
            except Exception as exc:
                logger.warning("analysis_safe_async_call_failed label=%s error=%s", label, exc)
                return {}

        # Lat/Lng-first orchestration: use resolved subject property coordinates when available.
        if latitude is not None and longitude is not None:
            logger.debug(
                "analysis_geospatial_mode=lat_lng_first lat=%s lng=%s address=%s",
                latitude,
                longitude,
                clean_address,
            )

            raw_flood_payload, transit_payload, noise_payload_from_coords = await asyncio.gather(
                _safe_async_call(save_flood_zone_to_db(latitude, longitude), "flood_risk_score_by_coords"),
                _safe_async_call(save_transit_score_to_db(latitude, longitude), "transit_score_by_coords"),
                _safe_async_call(asyncio.to_thread(estimate_noise_from_coordinates, latitude, longitude), "noise_score_by_coords"),
            )

            flood_payload = {
                "address": clean_address,
                "property_lat": latitude,
                "property_lng": longitude,
                "fld_zone": raw_flood_payload.get("fld_zone"),
                "risk_label": raw_flood_payload.get("risk_label"),
                "flood_score": raw_flood_payload.get("flood_score"),
                "source": raw_flood_payload.get("source"),
            }
            # Prefer coordinate-based noise result when available.
            if noise_payload_from_coords:
                noise_payload = {
                    "address": clean_address,
                    "noise_level": noise_payload_from_coords.get("noise_level"),
                    "noise_index": noise_payload_from_coords.get("noise_index"),
                    "estimated_noise_db": noise_payload_from_coords.get("estimated_noise_db"),
                    "distance_to_road_m": noise_payload_from_coords.get("distance_to_road_m"),
                    "source": noise_payload_from_coords.get("source"),
                    "api_used": noise_payload_from_coords.get("api_used"),
                }
        else:
            logger.debug("analysis_geospatial_mode=address_fallback address=%s", clean_address)
            flood_payload, transit_payload = await asyncio.gather(
                _safe_async_call(get_flood_zone_by_address(clean_address), "flood_risk_score"),
                _safe_async_call(get_transit_score_by_address(clean_address), "transit_score"),
            )

        rent_value = _to_float(property_row.get("rent"))
        median_price = _to_float(
            median_price_payload.get("median_price")
            or median_price_payload.get("median_sale_price")
        )
        median_income = _to_float(income_payload.get("median_income"))
        bachelor_pct = _to_float(education_payload.get("bachelor_percentage"))

        facts_payload = {
            "median_property_price": median_price,
            "median_income": median_income,
            "median_income_currency": "USD",
            "bachelor_percentage": bachelor_pct,
            "rent_to_price": _compute_rent_to_price(rent_value, median_price),
            "affordability_index": _compute_affordability_index(rent_value, median_income),
            "tenant_quality_index": _tenant_quality_label(bachelor_pct),
            "local_crime_index": _to_float(crime_payload.get("local_crime_index")),
            "national_crime_index": _to_float(crime_payload.get("national_crime_index")),
            "flood_zone": flood_payload.get("fld_zone"),
            "flood_risk_label": flood_payload.get("risk_label"),
            "transit_radius_meters": _to_int(transit_payload.get("radius_meters")),
            "nearest_stop_distance": _to_float(transit_payload.get("nearest_stop_meters")),
            "bus_stop_count": _to_int(transit_payload.get("bus_stop_count")),
            "rail_station_count": _to_int(transit_payload.get("rail_station_count")),
            "distance_to_road": _to_float(noise_payload.get("distance_to_road_m")),
            "noise_index": _to_float(noise_payload.get("noise_index")),
            "estimated_noise_db": _to_float(noise_payload.get("estimated_noise_db")),
            "total_schools": _extract_total_schools(school_payload),
        }

        AnalysisRepository.upsert_property_facts(
            property_id=property_id,
            run_id=run_id,
            payload=facts_payload,
        )
        logger.debug(
            "property_facts_mapped run_id=%s property_id=%s payload=%s",
            run_id,
            property_id,
            facts_payload,
        )

        if ANALYSIS_STAGE_MODE == "property_facts_only":
            AnalysisRepository.set_run_status(run_id=run_id, status="completed")
            logger.info(
                "analysis_stage property_facts_only completed run_id=%s property_id=%s",
                run_id,
                property_id,
            )
            return {
                "run_id": run_id,
                "property_id": property_id,
                "status": "completed",
            }

        AnalysisRepository.replace_comparables(
            property_id=property_id,
            run_id=run_id,
            comparables=rent_data.get("comparables") or [],
        )

        onboarding = get_onboarding_answers_by_user_id(user_id)
        user_scores = _build_user_scores(
            amenity_score=_to_float(amenity_payload.get("composite_score")),
            transit_score=_to_float(transit_payload.get("transit_score")),
            noise_score=(noise_payload.get("noise_level") or None),
            school_score=_extract_school_score(school_payload),
            safety_score=_to_float(crime_payload.get("safety_score")),
            flood_score=_to_float(flood_payload.get("flood_score")),
            onboarding=onboarding,
        )

        AnalysisRepository.upsert_user_scores(
            user_id=str(user_id),
            property_id=property_id,
            run_id=run_id,
            payload=user_scores,
        )

        source_map = {
            "rent": _source_label(rent_data, "unknown"),
            "median_property_price": _source_label(median_price_payload, "supabase"),
            "income": _source_label(income_payload, "unknown"),
            "education": _source_label(education_payload, "unknown"),
            "crime": "fbi_api",
            "amenity": _source_label((amenity_payload.get("_meta") or {}), "unknown"),
            "noise": _source_label(noise_payload, "unknown"),
            "school_scores": "supabase",
            "flood": _source_label(flood_payload, "unknown"),
            "transit": _source_label(transit_payload, "unknown"),
        }
        logger.info("analysis_sources run_id=%s property_id=%s sources=%s", run_id, property_id, source_map)

        AnalysisRepository.set_run_status(run_id=run_id, status="completed")

        return {
            "run_id": run_id,
            "property_id": property_id,
            "status": "completed",
            "source_map": source_map,
        }
    except Exception as exc:
        AnalysisRepository.set_run_status(run_id=run_id, status="failed", error_message=str(exc))
        raise
