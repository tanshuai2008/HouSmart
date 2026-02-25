from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

# Support running this file directly (e.g., `python backend/app/services/median_house_price.py`).
# When executed as a script, Python won't automatically add the backend root to sys.path,
# so `import app...` would fail.
_BACKEND_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT_FOR_IMPORTS))

from app.utils.cache_utils import get_cached, set_cache

_REDFIN_DEFAULT_URL = (
    "https://redfin-public-data.s3.us-west-2.amazonaws.com/"
    "redfin_market_tracker/city_market_tracker.tsv000.gz"
)

# Override for testing/offline usage. Can be either:
# - an https URL (downloaded + cached to disk)
# - a local file path to a TSV/CSV (read directly; no download)
# NOTE: we resolve this from the environment at runtime (not import-time) so
# CLI args and env var changes take effect within the same process.

TIMEOUT = 15

BACKEND_DIR = Path(__file__).resolve().parents[2]
REDFIN_CACHE_FILE = BACKEND_DIR / "redfin_city_market_tracker.tsv000.gz"

# Total wall-clock time budget for downloading the Redfin dataset.
# If it can't be fetched within this window, we skip Redfin.
REDFIN_MAX_DOWNLOAD_SECONDS = float(os.getenv("HOUSMART_REDFIN_MAX_SECONDS", "25"))

# Local TSVs can be multi-GB; loading the entire file into memory is slow and
# memory-hungry. For sufficiently large local files we stream-scan in chunks,
# cache per city/state in JSON, and keep RAM usage bounded.
REDFIN_LOCAL_STREAM_MB = float(os.getenv("HOUSMART_REDFIN_LOCAL_STREAM_MB", "200"))
REDFIN_STREAM_CHUNK_ROWS = int(os.getenv("HOUSMART_REDFIN_STREAM_CHUNK_ROWS", "200000"))

_REDFIN_DF: pd.DataFrame | None = None
_REDFIN_LAST_ERROR: str | None = None


def _normalize_redfin_col(col: str) -> str:
    # Redfin files are commonly published with UPPERCASE headers.
    # Normalize to a stable lowercase schema used by the rest of the service.
    return str(col).strip().strip("\"").strip().lower()


def _is_http_source(source: Any) -> bool:
    return str(source).lower().startswith("http")


def _effective_redfin_data_url() -> str:
    """Return the effective Redfin source.

    Rules:
    - If env var is missing/blank -> use default Redfin URL.
    - If env var is an http(s) URL -> use it.
    - If env var is a local path and it exists -> use it.
    - If env var is a local path but missing -> fall back to default URL.
    """

    env_val = os.getenv("HOUSMART_REDFIN_DATA_URL")
    raw = str(env_val or "").strip()
    if not raw:
        return _REDFIN_DEFAULT_URL
    if _is_http_source(raw):
        return raw
    try:
        if Path(raw).exists():
            return raw
    except OSError:
        pass
    return _REDFIN_DEFAULT_URL


def _redfin_source_path() -> Path:
    effective = _effective_redfin_data_url()
    return Path(effective) if not _is_http_source(effective) else REDFIN_CACHE_FILE


def _should_stream_local_file(path: Path) -> bool:
    try:
        if _is_http_source(_effective_redfin_data_url()):
            return False
        if not path.exists():
            return False
        return (path.stat().st_size / (1024 * 1024)) >= REDFIN_LOCAL_STREAM_MB
    except OSError:
        return False


def _iter_redfin_chunks(path: Path):
    wanted = {"city", "state", "state_code", "period_end", "median_sale_price"}
    reader = pd.read_csv(
        path,
        sep="\t",
        usecols=lambda c: _normalize_redfin_col(c) in wanted,
        chunksize=max(10_000, REDFIN_STREAM_CHUNK_ROWS),
        low_memory=False,
    )
    for chunk in reader:
        chunk = chunk.rename(columns={c: _normalize_redfin_col(c) for c in chunk.columns})
        if "state_code" in chunk.columns:
            chunk["state"] = chunk["state_code"]
        # ensure stable string dtype for comparisons
        if "city" in chunk.columns:
            chunk["city"] = chunk["city"].astype("string")
        if "state" in chunk.columns:
            chunk["state"] = chunk["state"].astype("string")
        yield chunk


def _stream_find_latest_redfin(city: str, state: str) -> dict[str, Any] | None:
    """Scan a local Redfin TSV in chunks and return the latest row for city/state."""

    global _REDFIN_LAST_ERROR

    path = _redfin_source_path()
    city_l = city.strip().lower()
    state_l = state.strip().lower()

    best_period: str | None = None
    best_price: int | None = None

    try:
        for chunk in _iter_redfin_chunks(path):
            if chunk.empty:
                continue
            if not {"city", "state", "period_end", "median_sale_price"}.issubset(chunk.columns):
                continue

            # Filter in-chunk. `period_end` is ISO (YYYY-MM-DD) in Redfin datasets,
            # so string max corresponds to latest date.
            mask = (chunk["city"].str.lower() == city_l) & (
                chunk["state"].str.lower() == state_l
            )
            sub = chunk.loc[mask, ["period_end", "median_sale_price"]]
            if sub.empty:
                continue

            # Find latest row in this chunk.
            # Compare period_end as strings for speed (format is YYYY-MM-DD).
            sub = sub.dropna(subset=["period_end"]).copy()
            if sub.empty:
                continue
            sub["period_end"] = sub["period_end"].astype("string")
            idx = sub["period_end"].astype(str).idxmax()
            row = sub.loc[idx]
            period = None if pd.isna(row["period_end"]) else str(row["period_end"])

            if not period:
                continue

            price_val: int | None = None
            try:
                if pd.notna(row["median_sale_price"]):
                    price_val = int(row["median_sale_price"])
            except (TypeError, ValueError):
                price_val = None

            if best_period is None or period > best_period:
                best_period = period
                best_price = price_val

        if best_period is None:
            return None

        return {
            "city": city,
            "state": state,
            "median_sale_price": best_price,
            "period": best_period,
        }
    except Exception as exc:
        _REDFIN_LAST_ERROR = str(exc)
        return None


def _redfin_cache_key(*, city: str, state: str) -> str:
    return f"redfin_city:{state.strip().upper()}:{city.strip().lower()}"


def _download_redfin_dataset_if_needed() -> bool:
    global _REDFIN_LAST_ERROR

    # Local file path mode: no download.
    effective = _effective_redfin_data_url()
    if not _is_http_source(effective):
        return Path(effective).exists()

    if REDFIN_MAX_DOWNLOAD_SECONDS <= 0:
        return False
    if REDFIN_CACHE_FILE.exists():
        return True

    tmp_path = REDFIN_CACHE_FILE.with_suffix(REDFIN_CACHE_FILE.suffix + ".part")
    start = time.monotonic()
    try:
        with requests.get(effective, stream=True, timeout=TIMEOUT) as res:
            res.raise_for_status()
            with tmp_path.open("wb") as f:
                for chunk in res.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
                    if (time.monotonic() - start) > REDFIN_MAX_DOWNLOAD_SECONDS:
                        raise TimeoutError(
                            f"Redfin download exceeded {REDFIN_MAX_DOWNLOAD_SECONDS}s"
                        )
        tmp_path.replace(REDFIN_CACHE_FILE)
        return True
    except Exception as exc:
        _REDFIN_LAST_ERROR = str(exc)
        return False
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass


def _load_redfin_df() -> pd.DataFrame:
    """Load Redfin dataset into memory once (optional)."""

    global _REDFIN_DF
    if _REDFIN_DF is not None:
        return _REDFIN_DF

    ok = _download_redfin_dataset_if_needed()
    if not ok:
        _REDFIN_DF = pd.DataFrame(
            columns=["city", "state", "period_end", "median_sale_price"]
        )
        return _REDFIN_DF

    try:
        wanted = {"city", "state", "state_code", "period_end", "median_sale_price"}
        source = _redfin_source_path()
        df = pd.read_csv(
            source,
            sep="\t",
            usecols=lambda c: _normalize_redfin_col(c) in wanted,
            low_memory=False,
        )

        # Normalize columns to the expected schema.
        df = df.rename(columns={c: _normalize_redfin_col(c) for c in df.columns})
        if "city" in df.columns:
            df["city"] = df["city"].astype("string")

        # Prefer 2-letter state codes when available (Redfin often provides both
        # `STATE` as full name and `STATE_CODE` as abbreviation).
        if "state_code" in df.columns:
            df["state"] = df["state_code"].astype("string")
        elif "state" in df.columns:
            df["state"] = df["state"].astype("string")
        _REDFIN_DF = df
        return df
    except Exception:
        _REDFIN_DF = pd.DataFrame(
            columns=["city", "state", "period_end", "median_sale_price"]
        )
        return _REDFIN_DF


def get_redfin_median_price(city: str, state: str) -> dict[str, Any]:
    """Return latest Redfin median sale price for a given city+state, with JSON cache."""

    if not city or not str(city).strip():
        return {"error": "City is required"}
    if not state or not str(state).strip():
        return {"error": "State is required"}

    city = str(city).strip()
    state = str(state).strip().upper()
    key = _redfin_cache_key(city=city, state=state)

    cached = get_cached(key)
    if isinstance(cached, dict) and not cached.get("error"):
        cached.setdefault("source", "Redfin Data Center")
        # Always refresh retrieved_from.url to reflect the current effective source
        # (local path vs default URL) even when serving from cache.
        cached["retrieved_from"] = {
            "url": _effective_redfin_data_url(),
            "dataset": "",
        }
        set_cache(key, cached)
        return cached

    # If the user provided a large local TSV, stream-scan it (no download) and
    # rely on JSON cache for subsequent calls.
    source_path = _redfin_source_path()
    if _should_stream_local_file(source_path):
        latest_row = _stream_find_latest_redfin(city, state)
        if latest_row is None:
            detail = f" ({_REDFIN_LAST_ERROR})" if _REDFIN_LAST_ERROR else ""
            return {"error": f"No Redfin data found for this location{detail}"}

        result: dict[str, Any] = {
            "city": city,
            "state": state,
            "median_sale_price": latest_row.get("median_sale_price"),
            "period": latest_row.get("period"),
            "source": "Redfin Data Center",
            "retrieved_from": {
                "url": _effective_redfin_data_url(),
                "dataset": "redfin_market_tracker/city_market_tracker.tsv000.gz",
            },
        }
        set_cache(key, result)
        return result

    df = _load_redfin_df()
    if df.empty:
        detail = f" ({_REDFIN_LAST_ERROR})" if _REDFIN_LAST_ERROR else ""
        return {"error": f"Redfin dataset unavailable{detail}"}

    try:
        city_data = df[
            (df["city"].str.lower() == city.lower())
            & (df["state"].str.lower() == state.lower())
        ]
        if city_data.empty:
            return {"error": "No Redfin data found for this location"}

        latest = city_data.sort_values("period_end", ascending=False).iloc[0]

        price: int | None = None
        try:
            if pd.notna(latest["median_sale_price"]):
                price = int(latest["median_sale_price"])
        except (TypeError, ValueError):
            price = None

        period = None if pd.isna(latest["period_end"]) else str(latest["period_end"])

        result: dict[str, Any] = {
            "city": city,
            "state": state,
            "median_sale_price": price,
            "period": period,
            "source": "Redfin Data Center",
            "retrieved_from": {
                "url": _effective_redfin_data_url(),
                "dataset": "",
            },
        }
        set_cache(key, result)
        return result
    except Exception as exc:
        return {"error": str(exc)}


def get_median_house_price(city: str, state: str) -> dict[str, Any]:
    """API-friendly alias (median price comes from Redfin in the new flow)."""

    return get_redfin_median_price(city, state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch Redfin median sale price for a city (supports local TSV via HOUSMART_REDFIN_DATA_URL)."
    )
    parser.add_argument("--city", "-c", type=str, default=None, help="City name (e.g., Seattle)")
    parser.add_argument(
        "--state",
        "-s",
        type=str,
        default=None,
        help="2-letter state code (e.g., WA)",
    )
    parser.add_argument(
        "--data",
        type=str,
        default=None,
        help=(
            "Override Redfin data source for this run. "
            "Can be a local path like C:/.../city_market_tracker.tsv000 or an https URL. "
            "(Sets HOUSMART_REDFIN_DATA_URL for this process.)"
        ),
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Print the full raw service response instead of simplified fields.",
    )
    args = parser.parse_args()

    # Non-interactive dataset selection:
    # - If --data is provided:
    #     - blank -> use default Redfin URL (by unsetting/blanking env var)
    #     - non-blank -> use that path/URL
    # - If --data is not provided: keep existing env var (blank/unset falls back to default URL).
    if args.data is not None:
        data_val = str(args.data).strip()
        if data_val:
            os.environ["HOUSMART_REDFIN_DATA_URL"] = data_val
        else:
            os.environ.pop("HOUSMART_REDFIN_DATA_URL", None)

    city_in = (args.city or input("Enter city: ")).strip()
    state_in = (args.state or input("Enter state code (e.g., WA): ")).strip()

    resp = get_redfin_median_price(city_in, state_in)
    if args.raw or (not isinstance(resp, dict)) or resp.get("error"):
        print(resp)
    else:
        # Simplified output as requested.
        today = _dt.date.today().isoformat()
        place_name = f"{resp.get('city')}, {resp.get('state')}"
        out = {
            "date": today,
            "place_name": place_name,
            "period": resp.get("period"),
            "median_price": resp.get("median_sale_price"),
        }
        print(out)