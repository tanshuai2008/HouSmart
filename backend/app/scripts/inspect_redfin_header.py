from __future__ import annotations

import gzip
import os
import sys
import tempfile
from pathlib import Path

# Allow running from any directory
_BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.scripts.ingest_redfin import REDFIN_URL, download_redfin


def main() -> int:
    path = os.path.join(tempfile.gettempdir(), "housmart", "city_market_tracker.tsv000.gz")
    if not os.path.exists(path):
        print("cache miss; downloading Redfin gzip...")
        path = download_redfin(REDFIN_URL)

    print("path:", path)
    print("exists:", os.path.exists(path))

    if not os.path.exists(path):
        return 1

    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        header = f.readline().rstrip("\n")

    cols = header.split("\t")
    lower = [c.lower() for c in cols]

    print("num_cols:", len(cols))

    names = [
        "sale_to_list_ratio",
        "sale_to_list",
        "sale_to_list_ratio_avg",
        "sale_to_list_ratio_all",
        "sale_to_list_ratio_mom",
        "sale_to_list_ratio_yoy",
    ]

    for n in names:
        print(n, "in cols?", n in lower)

    ratioish = [c for c in cols if ("sale_to_list" in c.lower()) or ("list" in c.lower() and "ratio" in c.lower())]

    # Also show any columns with 'ratio' for debugging.
    ratio_cols = [c for c in cols if "ratio" in c.lower()]

    print("ratio-ish (first 80):")
    for c in ratioish[:80]:
        print(" -", c)

    print("\nratio columns (first 120):")
    for c in ratio_cols[:120]:
        print(" -", c)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
