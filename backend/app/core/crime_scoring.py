from __future__ import annotations

import argparse
import json
from math import exp
from typing import Any, Dict, List, Optional, Tuple

from app.data.croswalk_leasc_data import CrimeCrosswalkError, resolve_crosswalk_for_fips
from app.models.crime import (
    CrimeCategoryBreakdown,
    CrimeSafetyScoreResult,
    ORIMetadataResult,
)
from app.services.fbi_crime_data import FbiCrimeDataClient
from app.services.geocode_client import GeocodeClient
from app.utils.errors import CrimeSafetyServiceError, CrosswalkNotFoundError, ExternalAPIError
from app.utils.logging import get_logger

logger = get_logger(__name__)


CRIME_WEIGHTS: Dict[str, float] = {
    "violent_crime": 10.0,
    "rape": 9.5,
    "robbery": 8.0,
    "aggravated-assault": 7.0,
    "burglary": 6.0,
    "larceny": 3.0,
    "motor-vehicle-theft": 5.0,
    "arson": 6.0,
    "property_crime": 4.0,
    "homicide": 10.0,
}

CRIME_OFFENSE_CODES: Dict[str, str] = {
    "violent_crime": "V",
    "rape": "RPE",
    "robbery": "ROB",
    "aggravated-assault": "ASS",
    "burglary": "BUR",
    "larceny": "LAR",
    "motor-vehicle-theft": "MVT",
    "arson": "ARS",
    "property_crime": "P",
    "homicide": "HOM",
}


def fetch_ori_metadata(
    address: str,
    *,
    geocode_client: Optional[GeocodeClient] = None,
    supabase_client=None,
) -> ORIMetadataResult:
    normalized_address = address.strip()
    if not normalized_address:
        raise CrimeSafetyServiceError("address is required")

    geocoder = geocode_client or GeocodeClient()

    try:
        location = geocoder.geocode(normalized_address)
    except ExternalAPIError as exc:
        logger.error("Geocode failed address='%s': %s", normalized_address, exc)
        raise

    logger.info(
        "Geocode success address='%s' normalized='%s' place_fips=%s county_fips=%s population=%s",
        normalized_address,
        location.normalized_address,
        location.place_fips,
        location.county_fips,
        location.census_population,
    )
    try:
        agency = resolve_crosswalk_for_fips(
            place_fips=location.place_fips,
            county_fips=location.county_fips,
            supabase_client=supabase_client,
        )
    except CrimeCrosswalkError as exc:
        raise CrimeSafetyServiceError(str(exc)) from exc
    if agency is None:
        raise CrosswalkNotFoundError(
            "Unable to resolve ORI for the supplied address; ensure crosswalk data is populated"
        )

    return {
        "normalized_address": location.normalized_address,
        "place_fips": location.place_fips,
        "county_fips": location.county_fips,
        "census_population": location.census_population,
        "agency": {
            "ori": agency.ori,
            "name": agency.agency_name,
            "type": agency.agency_type,
        },
        "crime_offense_codes": dict(CRIME_OFFENSE_CODES),
        "crime_weights": dict(CRIME_WEIGHTS),
    }


def compute_crime_safety_score(
    address: str,
    *,
    from_month: str = "01-2025",
    to_month: str = "12-2025",
    geocode_client: Optional[GeocodeClient] = None,
    fbi_client: Optional[FbiCrimeDataClient] = None,
    supabase_client=None,
) -> CrimeSafetyScoreResult:
    metadata = fetch_ori_metadata(
        address,
        geocode_client=geocode_client,
        supabase_client=supabase_client,
    )
    fbi = fbi_client or FbiCrimeDataClient()
    agency_name = metadata["agency"]["name"]
    breakdowns: List[CrimeCategoryBreakdown] = []
    skipped_offenses: List[str] = []
    months_analyzed = 0
    local_index = 0.0
    national_index = 0.0

    for alias, offense_code in metadata["crime_offense_codes"].items():
        weight = metadata["crime_weights"].get(alias, 1.0)
        try:
            payload = fbi.fetch_summarized_data(
                ori=metadata["agency"]["ori"],
                offense_code=offense_code,
                from_month=from_month,
                to_month=to_month,
            )
        except CrimeSafetyServiceError as exc:
            logger.warning("FBI fetch failed for offense=%s: %s", alias, exc)
            skipped_offenses.append(alias)
            continue

        parsed = _build_rate_breakdown(
            payload=payload,
            alias=alias,
            offense_code=offense_code,
            weight=weight,
            agency_name=agency_name,
        )
        if not parsed:
            logger.debug("Skipping offense=%s due to insufficient rate data", alias)
            skipped_offenses.append(alias)
            continue
        breakdown, months = parsed
        breakdowns.append(breakdown)
        months_analyzed = max(months_analyzed, months)
        local_index += breakdown["weighted_local_rate"]
        national_index += breakdown["weighted_national_rate"]

    if not breakdowns:
        message = "Crime data is not available for the supplied address"
        logger.warning(
            "%s (skipped=%s)",
            message,
            ",".join(skipped_offenses) or "none",
        )
        return _empty_score_result(metadata, from_month, to_month, message)
    if national_index <= 0:
        logger.warning("National offense data unavailable; returning empty score")
        return _empty_score_result(metadata, from_month, to_month, "Crime data is not available for the supplied address")

    crime_ratio = local_index / national_index if national_index else 0.0
    safety_score = max(0.0, min(100.0, 100.0 * exp(-0.75 * crime_ratio)))
    safety_category = _classify_score(safety_score)

    logger.info(
        "Crime score computed ori=%s local_index=%.2f national_index=%.2f ratio=%.2f score=%.2f valid_offenses=%s skipped_offenses=%s",
        metadata["agency"]["ori"],
        local_index,
        national_index,
        crime_ratio,
        safety_score,
        len(breakdowns),
        len(skipped_offenses),
    )

    return {
        "normalized_address": metadata["normalized_address"],
        "agency": metadata["agency"],
        "date_range": {"from": from_month, "to": to_month},
        "months_analyzed": months_analyzed,
        "local_crime_index": local_index,
        "national_crime_index": national_index,
        "relative_crime_ratio": crime_ratio,
        "safety_score": safety_score,
        "safety_category": safety_category,
        "offense_breakdown": breakdowns,
        "data_available": True,
        "message": None,
    }


def _build_rate_breakdown(
    *,
    payload: Dict[str, Any],
    alias: str,
    offense_code: str,
    weight: float,
    agency_name: str,
) -> Optional[Tuple[CrimeCategoryBreakdown, int]]:
    offenses = payload.get("offenses") or {}
    rates = offenses.get("rates") or {}
    local_key = _detect_agency_rate_key(rates, agency_name)
    local_series = rates.get(local_key) if local_key else None
    national_series = rates.get("United States Offenses")

    local_avg, month_count = _average_rate(local_series)
    national_avg, _ = _average_rate(national_series)
    if local_avg is None or national_avg is None or national_avg <= 0:
        return None

    rate_ratio = local_avg / national_avg
    breakdown: CrimeCategoryBreakdown = {
        "alias": alias,
        "offense_code": offense_code,
        "weight": weight,
        "local_rate_per_100k": local_avg,
        "national_rate_per_100k": national_avg,
        "rate_ratio": rate_ratio,
        "months_with_data": month_count,
        "weighted_local_rate": local_avg * weight,
        "weighted_national_rate": national_avg * weight,
    }
    return breakdown, month_count


def _detect_agency_rate_key(rates: Dict[str, Any], agency_name: str) -> Optional[str]:
    expected_key = f"{agency_name} Offenses"
    if expected_key in rates:
        return expected_key
    for key in rates.keys():
        if key.endswith(" Offenses") and key != "United States Offenses":
            logger.debug("Using fallback rate key='%s' for agency='%s'", key, agency_name)
            return key
    logger.debug("No agency rate key found for agency='%s'", agency_name)
    return None


def _average_rate(series: Any) -> Tuple[Optional[float], int]:
    if not isinstance(series, dict):
        return None, 0
    values = [float(value) for value in series.values() if isinstance(value, (int, float)) and value > 0]
    if not values:
        return None, 0
    return sum(values) / len(values), len(values)


def _classify_score(score: float) -> str:
    if score > 75:
        return "Green"
    if score >= 40:
        return "Yellow"
    return "Red"


def _empty_score_result(
    metadata: ORIMetadataResult,
    from_month: str,
    to_month: str,
    message: str,
) -> CrimeSafetyScoreResult:
    return {
        "normalized_address": metadata["normalized_address"],
        "agency": metadata["agency"],
        "date_range": {"from": from_month, "to": to_month},
        "months_analyzed": 0,
        "local_crime_index": 0.0,
        "national_crime_index": 0.0,
        "relative_crime_ratio": 0.0,
        "safety_score": 0.0,
        "safety_category": "No Data",
        "offense_breakdown": [],
        "data_available": False,
        "message": message,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute crime safety score for an address")
    parser.add_argument("address", help="Full mailing address")
    parser.add_argument("--from-month", default="01-2025", help="Start month in MM-YYYY format")
    parser.add_argument("--to-month", default="12-2025", help="End month in MM-YYYY format")
    args = parser.parse_args()

    result = compute_crime_safety_score(
        args.address,
        from_month=args.from_month,
        to_month=args.to_month,
    )
    print(json.dumps(result, indent=2))


__all__ = [
    "CRIME_OFFENSE_CODES",
    "CRIME_WEIGHTS",
    "fetch_ori_metadata",
    "compute_crime_safety_score",
]


if __name__ == "__main__":
    main()
