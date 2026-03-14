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


def resolve_crosswalk_for_fips_list(
    *,
    place_fips: Optional[str],
    county_fips: Optional[str],
    supabase_client: Optional["Client"] = None,
) -> list[CrosswalkRecord]:
    client = _resolve_client(supabase_client)
    records: list[CrosswalkRecord] = []
    seen: set[str] = set()

    if place_fips:
        for column_name in _column_variants("place_fips"):
            for record in _query_crosswalk_rows(client, column_name, place_fips):
                if record.ori not in seen:
                    records.append(record)
                    seen.add(record.ori)
    if county_fips:
        for column_name in _column_variants("county_fips"):
            for record in _query_crosswalk_rows(client, column_name, county_fips):
                if record.ori not in seen:
                    records.append(record)
                    seen.add(record.ori)
    return records


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
    rows: list[dict] = []
    last_exc: Optional[Exception] = None
    any_query_succeeded = False
    for column_name in column_variants:
        try:
            matched_rows = _query_crosswalk_rows_raw(client, column_name, value)
            any_query_succeeded = True
            rows = matched_rows
            if rows:
                logger.debug("Crosswalk matched using column variant %s=%s", column_name, value)
                break
        except CrimeCrosswalkError as exc:
            last_exc = exc
            if "no matching fips column found" in str(exc).lower():
                continue
            raise
    # Raise schema error only when every attempted variant failed due missing column.
    # If any variant query executed successfully (even with zero rows), return None
    # so caller can try county-level fallback.
    if not rows and not any_query_succeeded and last_exc and "column" in str(last_exc).lower():
        raise CrimeCrosswalkError(
            f"Supabase crosswalk lookup failed: no matching FIPS column found for {column}"
        ) from last_exc
    if not rows:
        return None

    selected_row = None
    for row in rows:
        if _normalize_agency_type(row) == agency_type:
            selected_row = row
            break
    if selected_row is None:
        selected_row = rows[0]

    return _row_to_crosswalk_record(selected_row, fallback_agency_type=agency_type)


def _query_crosswalk_rows(client: "Client", column_name: str, value: str) -> list[CrosswalkRecord]:
    return [
        record
        for row in _query_crosswalk_rows_raw(client, column_name, value)
        if (record := _row_to_crosswalk_record(row)) is not None
    ]


def _query_crosswalk_rows_raw(client: "Client", column_name: str, value: str) -> list[dict]:
    try:
        response = (
            client
            .table(CROSSWALK_TABLE_NAME)
            .select("*")
            .eq(column_name, value)
            .limit(50)
            .execute()
        )
        return response.data or []
    except SupabaseConfigError as exc:
        raise CrimeCrosswalkError(str(exc)) from exc
    except Exception as exc:
        if "column" in str(exc).lower():
            raise CrimeCrosswalkError(
                f"Supabase crosswalk lookup failed: no matching FIPS column found for {column_name}"
            ) from exc
        raise CrimeCrosswalkError(f"Supabase crosswalk lookup failed: {exc}") from exc


def _normalize_agency_type(row: dict) -> str:
    raw = (
        row.get("agency_type")
        or row.get("agcytype")
        or row.get("subtype1")
        or row.get("SUBTYPE1")
        or row.get("type")
        or ""
    )
    text = str(raw).strip().lower()
    if text in {"0", "city", "municipal police", "local police"}:
        return "city"
    if text in {"1", "county", "sheriff"}:
        return "county"
    return text


def _row_to_crosswalk_record(
    row: dict,
    *,
    fallback_agency_type: Optional[str] = None,
) -> Optional[CrosswalkRecord]:
    resolved_ori = str(
        row.get("ori")
        or row.get("ori9")
        or row.get("ori7")
        or row.get("ORI")
        or row.get("ORI9")
        or row.get("ORI7")
        or ""
    ).strip()
    resolved_name = str(
        row.get("agency_name")
        or row.get("name")
        or row.get("NAME")
        or row.get("address_name")
        or row.get("agency")
        or ""
    ).strip()
    resolved_type = _normalize_agency_type(row) or (fallback_agency_type or "")

    if not resolved_ori:
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
    "resolve_crosswalk_for_fips_list",
]
