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
    client = _resolve_client(supabase_client)
    logger.debug(
        "Resolving crosswalk for place_fips=%s county_fips=%s",
        place_fips,
        county_fips,
    )
    if place_fips:
        record = _fetch_crosswalk(client, "place_fips", place_fips, "city")
        if record:
            logger.info(
                "Crosswalk city match found: ori=%s agency=%s",
                record.ori,
                record.agency_name,
            )
            return record
        logger.debug("No city crosswalk row found for place_fips=%s", place_fips)
    if county_fips:
        record = _fetch_crosswalk(client, "county_fips", county_fips, "county")
        if record:
            logger.info(
                "Crosswalk county match found: ori=%s agency=%s",
                record.ori,
                record.agency_name,
            )
            return record
        logger.debug("No county crosswalk row found for county_fips=%s", county_fips)
    logger.warning(
        "Crosswalk lookup failed for place_fips=%s county_fips=%s",
        place_fips,
        county_fips,
    )
    return None


def _fetch_crosswalk(
    client: "Client",
    column: str,
    value: str,
    agency_type: str,
) -> Optional[CrosswalkRecord]:
    logger.debug(
        "Querying crosswalk table=%s column=%s value=%s agency_type=%s",
        CROSSWALK_TABLE_NAME,
        column,
        value,
        agency_type,
    )
    try:
        response = (
            client
            .table(CROSSWALK_TABLE_NAME)
            .select("ori, agency_name, agency_type")
            .eq(column, value)
            .eq("agency_type", agency_type)
            .limit(1)
            .execute()
        )
    except SupabaseConfigError as exc:
        raise CrimeCrosswalkError(str(exc)) from exc
    except Exception as exc:
        raise CrimeCrosswalkError(f"Supabase crosswalk lookup failed: {exc}") from exc

    rows = response.data or []
    if not rows:
        return None
    row = rows[0]
    return CrosswalkRecord(
        ori=str(row.get("ori", "")).strip(),
        agency_name=str(row.get("agency_name", "")).strip(),
        agency_type=str(row.get("agency_type", agency_type)).strip() or agency_type,
    )


__all__ = [
    "CrimeCrosswalkError",
    "CROSSWALK_TABLE_NAME",
    "resolve_crosswalk_for_fips",
]
