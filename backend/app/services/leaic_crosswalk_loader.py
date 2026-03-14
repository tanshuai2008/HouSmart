from __future__ import annotations

import argparse
import csv
from typing import Dict, Optional

from dotenv import load_dotenv

from app.services.supabase_client import get_supabase
from app.utils.logging import get_logger

try:
    from supabase import Client
except ImportError:  # pragma: no cover
    Client = None  # type: ignore

load_dotenv()
logger = get_logger(__name__)

SKIP_VALUES = {"", "-1", "888", "888888888", None}
CITY_SUBTYPE = "0"
COUNTY_SUBTYPE = "1"
CROSSWALK_TABLE = "leaic_crosswalk"


def load_crosswalk_from_tsv(
    tsv_path: str,
    *,
    batch_size: int = 500,
    supabase_client: Optional[Client] = None,
) -> Dict[str, int]:
    client = supabase_client or get_supabase()
    inserted = 0
    skipped = 0
    batch: list[Dict[str, Optional[str]]] = []

    with open(tsv_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            normalized = _normalize_row(row)
            if not normalized:
                skipped += 1
                continue
            batch.append(normalized)
            if len(batch) >= batch_size:
                _flush_batch(batch, client)
                inserted += len(batch)
                batch.clear()
        if batch:
            _flush_batch(batch, client)
            inserted += len(batch)

    logger.info("Crosswalk load complete: inserted=%s, skipped=%s", inserted, skipped)
    return {"inserted": inserted, "skipped": skipped}


def _flush_batch(batch: list[Dict[str, Optional[str]]], client: Client) -> None:
    try:
        (
            client
            .table(CROSSWALK_TABLE)
            .upsert(batch)
            .execute()
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Supabase upsert failed: %s", exc)
        raise


def _normalize_row(row: Dict[str, str]) -> Optional[Dict[str, Optional[str]]]:
    ori = _clean_ori(row)
    if not ori:
        return None

    agency_name = (row.get("NAME") or "").strip()
    if not agency_name:
        return None

    subtype = (row.get("SUBTYPE1") or "").strip()
    if subtype == CITY_SUBTYPE:
        agency_type = "city"
    elif subtype == COUNTY_SUBTYPE:
        agency_type = "county"
    else:
        return None

    place_fips = _clean_place_fips(row.get("FPLACE"))
    county_fips = _clean_county_fips(row)
    state_abbr = _clean_state(row)

    normalized = {
        "ori": ori,
        "agency_name": agency_name,
        "agency_type": agency_type,
        "place_fips": place_fips,
        "county_fips": county_fips,
        "state_abbr": state_abbr,
    }
    normalized.update({key.lower(): _clean_raw_value(value) for key, value in row.items()})
    return normalized


def _clean_ori(row: Dict[str, str]) -> Optional[str]:
    for key in ("ORI9", "ORI7"):
        value = row.get(key)
        if value and value not in SKIP_VALUES:
            cleaned = value.strip().upper()
            if cleaned:
                return cleaned
    return None


def _clean_place_fips(value: Optional[str]) -> Optional[str]:
    if not value or value in SKIP_VALUES:
        return None
    digits = value.strip().split(".")[0]
    if not digits or digits.startswith("99"):
        return None
    return digits.zfill(5)


def _clean_county_fips(row: Dict[str, str]) -> Optional[str]:
    composite = row.get("FIPS")
    if composite and composite not in SKIP_VALUES:
        return composite.strip().zfill(5)
    state = row.get("FIPS_ST")
    county = row.get("FIPS_COUNTY")
    if state and county and state not in SKIP_VALUES and county not in SKIP_VALUES:
        return state.strip().zfill(2) + county.strip().zfill(3)
    return None


def _clean_state(row: Dict[str, str]) -> Optional[str]:
    state = row.get("ADDRESS_STATE") or row.get("STATENAME")
    if not state or state in SKIP_VALUES:
        return None
    cleaned = state.strip().upper()
    if len(cleaned) == 2:
        return cleaned
    return cleaned[:2]


def _clean_raw_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Load LEAIC crosswalk TSV data into Supabase")
    parser.add_argument("--tsv_path",default="app/data/ICPSR_35158-V2/ICPSR_35158/DS0001/35158-0001-Data.tsv", help="Path to the ICPSR TSV file (e.g., 35158-0001-Data.tsv)")
    parser.add_argument("--batch-size", type=int, default=500, help="Number of rows per Supabase upsert")
    args = parser.parse_args()

    try:
        stats = load_crosswalk_from_tsv(
            args.tsv_path,
            batch_size=args.batch_size,
        )
    except Exception as exc:  # pragma: no cover
        logger.error("Crosswalk load failed: %s", exc)
        raise

    print(f"Inserted/updated rows: {stats['inserted']}")
    print(f"Skipped rows: {stats['skipped']}")


if __name__ == "__main__":
    main()
