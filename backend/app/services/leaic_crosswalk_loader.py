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
    batch: list[Dict[str, Optional[str]]] = []

    with open(tsv_path, "r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            # Insert every row, every column, no filtering or normalization
            record = {k.lower(): (v.strip() if v is not None else None) for k, v in row.items()}            
            batch.append(record)
            if len(batch) >= batch_size:
                _flush_batch(batch, client)
                inserted += len(batch)
                batch.clear()
        if batch:
            _flush_batch(batch, client)
            inserted += len(batch)

    logger.info("Crosswalk load complete: inserted=%s", inserted)
    return {"inserted": inserted}


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

    print(f"Inserted/updated rows: {stats}")


if __name__ == "__main__":
    main()
