from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.models.crime import CrosswalkRecord
from app.services.supabase_client import SupabaseConfigError, get_supabase
from app.utils.logging import get_logger

if TYPE_CHECKING:
    from supabase import Client

logger = get_logger(__name__)

CROSSWALK_TABLE_NAME = "leaic_crosswalk"


class CrimeCrosswalkError(RuntimeError):
    """Raised when crosswalk lookups fail."""


def _resolve_client(supabase_client: Optional["Client"]) -> "Client":
    return supabase_client or get_supabase()


def resolve_crosswalk_for_fips(
    *,
    place_fips: Optional[str],
    county_fips: Optional[str],
    supabase_client: Optional["Client"] = None,
) -> Optional[CrosswalkRecord]:
    """Return first matching ORI record for place/county FIPS."""
    records = resolve_crosswalk_for_fips_list(
        place_fips=place_fips,
        county_fips=county_fips,
        supabase_client=supabase_client,
    )
    return records[0] if records else None


def resolve_crosswalk_for_fips_list(
    *,
    place_fips: Optional[str],
    county_fips: Optional[str],
) -> list[CrosswalkRecord]:
    """Return all matching ORI records for place/county FIPS using fips_place/fips_county columns."""
    client = get_supabase()
    logger.debug(
        "Resolving crosswalk list for place_fips=%s county_fips=%s",
        place_fips,
        county_fips,
    )
    filters: dict[str, list[str]] = {}
    if place_fips:
        filters["fplace"] = [place_fips]
    if county_fips:
        filters["fips"] = [county_fips]

    if not filters:
        logger.warning(
            "Crosswalk lookup failed for place_fips=%s county_fips=%s",
            place_fips,
            county_fips,
        )
        return []

    records = _fetch_crosswalk_any(client, filters, return_all=True)
    if records:
        logger.info("Crosswalk matches found count=%s", len(records))
        return records

    logger.warning(
        "Crosswalk lookup failed for place_fips=%s county_fips=%s",
        place_fips,
        county_fips,
    )
    return []


def _fetch_crosswalk_any(
    client: "Client",
    filters_by_column: Optional[dict[str, list[str]]],
    agency_type: str = None,
    return_all: bool = False,
) -> list[CrosswalkRecord]:
    normalized_filters = {
        column.lower(): [
            str(candidate).strip()
            for candidate in values
            if str(candidate).strip()
        ]
        for column, values in (filters_by_column or {}).items()
    }
    or_clauses = [
        f"{column}.eq.{candidate}"
        for column, values in normalized_filters.items()
        for candidate in values
    ]
    if not or_clauses:
        logger.debug(
            "Skipping crosswalk query due to empty filters",
        )
        return []

    logger.debug(
        "Querying crosswalk table=%s filters=%s",
        CROSSWALK_TABLE_NAME,
        normalized_filters,
    )
    try:
        query = (
            client
            .table(CROSSWALK_TABLE_NAME)
            .select("ori9, name, agcytype")
            .neq("ori9", "-1")
            .or_(",".join(or_clauses))
        )
        
        response = query.execute()
    except SupabaseConfigError as exc:
        raise CrimeCrosswalkError(str(exc)) from exc
    except Exception as exc:
        raise CrimeCrosswalkError(f"Supabase crosswalk lookup failed: {exc}") from exc

    rows = response.data or []
    results: list[CrosswalkRecord] = []
    for row in rows:
        ori = str(row.get("ori9", "")).strip()
        agency_name = str(row.get("name", "")).strip()
        agency_type_result = str(row.get("agcytype", "")).strip()
        if ori and agency_name:
            results.append(CrosswalkRecord(
                ori=ori,
                agency_name=agency_name,
                agency_type=agency_type_result,
            ))

    return results


def resolve_crosswalk_for_zip(
    *,
    zip_code: Optional[str],
    supabase_client: Optional["Client"] = None,
) -> list[CrosswalkRecord]:
    """Search ORI records using address_zip (zip code)."""
    if not (zip_code and zip_code.strip()):
        return []
    client = _resolve_client(supabase_client)
    filters = {"address_zip": [zip_code.strip()]}

    records = _fetch_crosswalk_any(client, filters, return_all=True)
    if records:
        logger.info("Crosswalk zip matches found count=%s", len(records))
        return records
    logger.warning("Crosswalk lookup by zip failed for zip_code=%s", zip_code)
    return []


def resolve_crosswalk_for_city(
    *,
    city: Optional[str],
    state_abbr: Optional[str] = None,
    supabase_client: Optional["Client"] = None,
) -> list[CrosswalkRecord]:
    """Search ORI records using address_city and optional address_state."""
    if not (city and city.strip()):
        return []
    client = _resolve_client(supabase_client)
    city_value = city.strip().upper()
    filters: dict[str, list[str]] = {"address_city": [city_value]}
    if state_abbr and state_abbr.strip():
        filters["address_state"] = [state_abbr.strip().upper()]

    records = _fetch_crosswalk_any(client, filters, return_all=True)
    if records:
        logger.info("Crosswalk city matches found count=%s", len(records))
        return records
    logger.warning("Crosswalk lookup by city failed for city=%s state=%s", city, state_abbr)
    return []


__all__ = [
    "CrimeCrosswalkError",
    "CROSSWALK_TABLE_NAME",
    "resolve_crosswalk_for_fips",
    "resolve_crosswalk_for_fips_list",
    "resolve_crosswalk_for_zip",
    "resolve_crosswalk_for_city",
]
