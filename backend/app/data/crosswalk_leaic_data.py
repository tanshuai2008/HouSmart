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
    column_variants = _column_variants(column)
    rows = []
    last_exc: Optional[Exception] = None
    any_query_succeeded = False
    for column_name in column_variants:
        try:
            response = (
                client
                .table(CROSSWALK_TABLE_NAME)
                .select("*")
                .eq(column_name, value)
                .limit(50)
                .execute()
            )
            any_query_succeeded = True
            rows = response.data or []
            if rows:
                logger.debug(
                    "Crosswalk matched using column variant %s=%s",
                    column_name,
                    value,
                )
                break
        except SupabaseConfigError as exc:
            raise CrimeCrosswalkError(str(exc)) from exc
        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            if "column" in msg:
                logger.warning(
                    "Crosswalk query failed for column variant %s=%s; trying next variant: %s",
                    column_name,
                    value,
                    exc,
                )
                continue
            raise CrimeCrosswalkError(f"Supabase crosswalk lookup failed: {exc}") from exc
    # Raise schema error only when every attempted variant failed due missing column.
    # If any variant query executed successfully (even with zero rows), return None
    # so caller can try county-level fallback.
    if not rows and not any_query_succeeded and last_exc and "column" in str(last_exc).lower():
        raise CrimeCrosswalkError(
            f"Supabase crosswalk lookup failed: no matching FIPS column found for {column}"
        ) from last_exc
    if not rows:
        return None

    def _normalize_agency_type(row: dict) -> str:
        raw = (
            row.get("agency_type")
            or row.get("subtype1")
            or row.get("SUBTYPE1")
            or row.get("type")
            or ""
        )
        text = str(raw).strip().lower()
        if text in {"0", "city"}:
            return "city"
        if text in {"1", "county"}:
            return "county"
        return text

    selected_row = None
    for row in rows:
        if _normalize_agency_type(row) == agency_type:
            selected_row = row
            break
    if selected_row is None:
        selected_row = rows[0]

    resolved_type = _normalize_agency_type(selected_row) or agency_type
    resolved_ori = str(
        selected_row.get("ori")
        or selected_row.get("ori9")
        or selected_row.get("ori7")
        or selected_row.get("ORI")
        or selected_row.get("ORI9")
        or selected_row.get("ORI7")
        or ""
    ).strip()
    resolved_name = str(
        selected_row.get("agency_name")
        or selected_row.get("name")
        or selected_row.get("NAME")
        or selected_row.get("agency")
        or ""
    ).strip()

    if not resolved_ori:
        logger.warning("Crosswalk row found but ORI is empty for %s=%s", column, value)
        return None

    return CrosswalkRecord(
        ori=resolved_ori,
        agency_name=resolved_name,
        agency_type=resolved_type,
    )


def _column_variants(column: str) -> tuple[str, ...]:
    if column == "county_fips":
        return (
            "county_fips",
            "countyfips",
            "fips",
            "fips_county",
            "county",
            "FIPS",
            "FIPS_COUNTY",
        )
    if column == "place_fips":
        return (
            "place_fips",
            "placefips",
            "fplace",
            "place",
            "FPLACE",
        )
    return (column,)


__all__ = [
    "CrimeCrosswalkError",
    "CROSSWALK_TABLE_NAME",
    "resolve_crosswalk_for_fips",
]
