import os
import sys
import tempfile
import time
import gzip
import re
from typing import Optional
import random

import pandas as pd
import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError, ReadTimeout

# Allow running from any directory
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from app.config.db import require_supabase
from app.core.redfin_trends import redfin_trends_table_candidates


REDFIN_URL = (
    "https://redfin-public-data.s3.us-west-2.amazonaws.com/"
    "redfin_market_tracker/city_market_tracker.tsv000.gz"
)


# --------------------------------------------------
# STEP 1 — Download Redfin
# --------------------------------------------------
def download_redfin(url: str) -> str:
    print("⬇ Downloading Redfin dataset...")

    # Use a stable cache path so re-runs can resume after a network reset.
    cache_dir = os.path.join(tempfile.gettempdir(), "housmart")
    os.makedirs(cache_dir, exist_ok=True)
    tmp_path = os.path.join(cache_dir, "city_market_tracker.tsv000.gz")

    session = requests.Session()

    def _get_total_size_from_headers(response: requests.Response) -> int:
        content_range = response.headers.get("Content-Range")
        if content_range:
            # Example: "bytes 1048576-2097151/12345678"
            match = re.match(r"^bytes\s+\d+-\d+/(\d+)$", content_range)
            if match:
                return int(match.group(1))
        return int(response.headers.get("content-length") or 0)

    max_attempts = 10
    chunk_size = 4 * 1024 * 1024

    attempt = 0
    total_size: Optional[int] = None

    while True:
        existing = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
        headers = {}
        if existing > 0:
            headers["Range"] = f"bytes={existing}-"
            print(f"↩ Resuming at {existing:,} bytes")

        try:
            with session.get(url, headers=headers, stream=True, timeout=(15, 300)) as response:
                # 416 means the requested range is not satisfiable (already complete).
                if response.status_code == 416 and existing > 0:
                    break

                response.raise_for_status()

                # If we asked to resume but the server ignored Range, restart from scratch.
                if existing > 0 and response.status_code == 200:
                    existing = 0

                total_size = _get_total_size_from_headers(response)
                downloaded = existing
                mode = "ab" if existing > 0 else "wb"

                with open(tmp_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if not chunk:
                            continue
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rDownloading: {percent:.2f}%", end="")

                if total_size and downloaded >= total_size:
                    break

        except (ChunkedEncodingError, ConnectionError, ReadTimeout) as e:
            attempt += 1
            if attempt >= max_attempts:
                raise
            backoff = min(60, 2 ** attempt)
            print(f"\n⚠ Download interrupted ({type(e).__name__}). Retrying in {backoff}s...")
            time.sleep(backoff)
            continue

    # Quick integrity check: ensure the gzip header can be read.
    try:
        with gzip.open(tmp_path, "rb") as f:
            f.read(1)
    except OSError:
        # If the file is corrupt/incomplete, retry once from scratch.
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return download_redfin(url)

    # If we know the expected total size, ensure we didn't append extra bytes.
    # (Extra trailing bytes can corrupt gzip parsing.)
    try:
        if total_size and total_size > 0:
            final_size = os.path.getsize(tmp_path)
            if final_size > total_size:
                print(f"\n⚠ Downloaded file larger than expected ({final_size:,} > {total_size:,}); truncating...")
                with open(tmp_path, "rb+") as f:
                    f.truncate(total_size)
    except OSError:
        # Non-fatal; extraction will validate later.
        pass

    print("\n✅ Download Complete")
    return tmp_path


# --------------------------------------------------
# STEP 2 — Extract + Prepare Data
# --------------------------------------------------
def prepare_dataframe(gz_path: str) -> tuple[pd.DataFrame, str]:

    print("📦 Extracting dataset...")

    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        df = pd.read_csv(f, sep="\t")

    # Redfin TSV headers sometimes include wrapping quotes, e.g. "AVG_SALE_TO_LIST".
    # Normalize aggressively so downstream column checks are stable.
    df.columns = df.columns.astype(str).str.strip().str.strip('"').str.strip().str.lower()

    # The raw file contains multiple property types and other dimensions.
    # We only need a single canonical row per region.
    if "region_type" in df.columns:
        df = df[df["region_type"].astype(str).str.lower() == "place"]

    if "property_type" in df.columns:
        df = df[df["property_type"].astype(str).str.strip() == "All Residential"]

    base_cols = ["city", "state", "period_end", "median_sale_price"]

    # Redfin exports vary by dataset version. The city market tracker uses:
    #   AVG_SALE_TO_LIST (plus *_MOM, *_YOY)
    # Some older exports used sale_to_list_ratio.
    ratio_source_col = None
    for candidate in ("sale_to_list_ratio", "avg_sale_to_list"):
        if candidate in df.columns:
            ratio_source_col = candidate
            base_cols.append(candidate)
            break

    df = df[base_cols]

    df.rename(
        columns={
            "period_end": "period",
            "median_sale_price": "median_price",
            # Map Redfin column name to our canonical name.
            **({ratio_source_col: "sale_to_list_ratio"} if ratio_source_col else {}),
        },
        inplace=True,
    )

    df.dropna(inplace=True)

    # Normalize
    df["city"] = df["city"].astype(str).str.strip()
    df["state"] = df["state"].astype(str).str.strip()
    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    df["median_price"] = pd.to_numeric(df["median_price"], errors="coerce")

    if "sale_to_list_ratio" in df.columns:
        df["sale_to_list_ratio"] = pd.to_numeric(df["sale_to_list_ratio"], errors="coerce")

    df.dropna(inplace=True)

    # --------------------------------------------------
    # Keep last 36 months (inclusive) for trends
    # --------------------------------------------------
    latest_period = df["period"].max()
    if pd.isna(latest_period):
        raise ValueError("No valid 'period' values found in Redfin dataset")

    # 36 monthly points inclusive -> subtract 35 months.
    start_period = latest_period - pd.DateOffset(months=35)

    print(f"📅 Latest period found: {latest_period.date()}")
    print(f"🗓 Keeping periods since: {start_period.date()}")

    df = df[df["period"] >= start_period]

    earliest_period_str = df["period"].min().strftime("%Y-%m-%d")

    df["period"] = df["period"].dt.strftime("%Y-%m-%d")
    df["median_price"] = df["median_price"].round().astype("int64")

    if "sale_to_list_ratio" in df.columns:
        df["sale_to_list_ratio"] = df["sale_to_list_ratio"].round(2)

    print(f"✅ Filtered dataset: {len(df)} rows")

    return df, earliest_period_str


# --------------------------------------------------
# STEP 3 — Upload to Supabase
# --------------------------------------------------
def upload_to_supabase(df: pd.DataFrame, earliest_period: str):

    total = len(df)

    print(f"🚀 Uploading {total} records to Supabase...")

    supabase = require_supabase()
    table_candidates = redfin_trends_table_candidates()

    # Enforce a bounded retention window: keep only the last N months we ingest.
    # Delete anything older than the earliest period in this ingest.
    for table_name in table_candidates:
        try:
            supabase.table(table_name).delete().lt("period", earliest_period).execute()
            break
        except Exception:
            continue

    # Clear overlapping recent data to avoid duplicates.
    # NOTE: This deletes ALL cities/states from earliest_period onward.
    for table_name in table_candidates:
        try:
            print(f"🧹 Clearing existing rows in {table_name} since {earliest_period}...")
            supabase.table(table_name).delete().gte("period", earliest_period).execute()
            dest_table = table_name
            break
        except Exception:
            dest_table = None
            continue

    if not dest_table:
        raise RuntimeError(
            f"No Redfin trends destination table found. Tried: {', '.join(table_candidates)}"
        )

    batch_size = 500
    uploaded = 0
    ratio_enabled = "sale_to_list_ratio" in df.columns

    for start in range(0, total, batch_size):

        batch_df = df.iloc[start:start+batch_size]

        batch = []
        for row in batch_df.itertuples(index=False):
            payload = {
                "city": row.city,
                "state": row.state,
                "period": row.period,
                "median_price": int(row.median_price),
            }
            # Include ratio if present and supported by the destination table.
            if ratio_enabled and hasattr(row, "sale_to_list_ratio"):
                payload["sale_to_list_ratio"] = float(row.sale_to_list_ratio)
            batch.append(payload)

        try:
            supabase.table(dest_table).insert(batch).execute()
        except Exception as e:
            # If the Supabase table schema doesn't include sale_to_list_ratio, retry without it.
            if ratio_enabled and "sale_to_list_ratio" in str(e):
                print("\n⚠ Insert failed with sale_to_list_ratio; retrying batch without ratio column")
                ratio_enabled = False
                batch_no_ratio = []
                for item in batch:
                    item = dict(item)
                    item.pop("sale_to_list_ratio", None)
                    batch_no_ratio.append(item)
                supabase.table(dest_table).insert(batch_no_ratio).execute()
            else:
                raise

        uploaded += len(batch)

        percent = (uploaded / total) * 100
        print(f"\rUploading: {percent:.2f}%", end="")

    print("\n✅ Upload Complete")


def upload_to_supabase_scoped(
    df: pd.DataFrame,
    *,
    earliest_period: str,
    city: str,
    state: str,
):
    """Upload a subset of rows for one city/state without wiping the entire table.

    This is intended for verification / smoke-ingest scenarios.
    """

    total = len(df)
    print(f"🚀 Uploading {total} scoped records to Supabase for {city}, {state}...")

    supabase = require_supabase()
    table_candidates = redfin_trends_table_candidates()

    dest_table = None
    for table_name in table_candidates:
        try:
            # Enforce bounded retention for this city/state slice.
            (
                supabase.table(table_name)
                .delete()
                .eq("city", city)
                .eq("state", state)
                .lt("period", earliest_period)
                .execute()
            )
            print(f"🧹 Clearing existing scoped rows in {table_name} since {earliest_period} for {city}, {state}...")
            (
                supabase.table(table_name)
                .delete()
                .eq("city", city)
                .eq("state", state)
                .gte("period", earliest_period)
                .execute()
            )
            dest_table = table_name
            break
        except Exception:
            continue

    if not dest_table:
        raise RuntimeError(
            f"No Redfin trends destination table found. Tried: {', '.join(table_candidates)}"
        )

    batch_size = 500
    uploaded = 0
    ratio_enabled = "sale_to_list_ratio" in df.columns

    for start in range(0, total, batch_size):
        batch_df = df.iloc[start : start + batch_size]
        batch: list[dict] = []
        for row in batch_df.itertuples(index=False):
            payload = {
                "city": row.city,
                "state": row.state,
                "period": row.period,
                "median_price": int(row.median_price),
            }
            if ratio_enabled and hasattr(row, "sale_to_list_ratio"):
                payload["sale_to_list_ratio"] = float(row.sale_to_list_ratio)
            batch.append(payload)

        try:
            supabase.table(dest_table).insert(batch).execute()
        except Exception as e:
            if ratio_enabled and "sale_to_list_ratio" in str(e):
                print("\n⚠ Scoped insert failed with sale_to_list_ratio; retrying batch without ratio column")
                ratio_enabled = False
                batch_no_ratio = []
                for item in batch:
                    item = dict(item)
                    item.pop("sale_to_list_ratio", None)
                    batch_no_ratio.append(item)
                supabase.table(dest_table).insert(batch_no_ratio).execute()
            else:
                raise

        uploaded += len(batch)
        percent = (uploaded / total) * 100
        print(f"\rUploading scoped: {percent:.2f}%", end="")

    print("\n✅ Scoped upload complete")


# --------------------------------------------------
# MAIN INGEST FLOW
# --------------------------------------------------
def ingest_redfin():

    # Download + parse can fail if a previous resumed download produced a corrupted gzip.
    # Retry once with a clean download (delete cached file and start over).
    last_error: Exception | None = None
    gz_path: str | None = None

    for attempt in range(2):
        if gz_path:
            try:
                os.remove(gz_path)
            except OSError:
                pass
            gz_path = None

        gz_path = download_redfin(REDFIN_URL)

        try:
            df, earliest_period = prepare_dataframe(gz_path)
            upload_to_supabase(df, earliest_period=earliest_period)
            last_error = None
            break
        except (gzip.BadGzipFile, OSError, pd.errors.ParserError) as e:
            last_error = e
            print(f"\n⚠ Failed to extract Redfin gzip ({type(e).__name__}: {e}).")
            if attempt == 0:
                print("🔁 Retrying with a fresh download...")
                continue
            raise
        finally:
            # Always clean up local gzip (we rely on Supabase as the store of truth).
            if gz_path:
                try:
                    os.remove(gz_path)
                except OSError:
                    pass

    if last_error is not None:
        raise last_error


def ingest_redfin_sample(*, seed: int | None = None) -> dict:
    """Extract Redfin, pick a random city/state slice, and upload only that slice.

    Returns metadata about what was uploaded.
    """
    if seed is not None:
        random.seed(int(seed))

    gz_path = None
    try:
        gz_path = download_redfin(REDFIN_URL)
        df, earliest_period = prepare_dataframe(gz_path)

        if df.empty:
            raise RuntimeError("Prepared Redfin dataframe is empty")

        # Pick a city/state pair from the prepared dataframe.
        row = df.sample(n=1).iloc[0]
        city = str(row["city"]).strip()
        state = str(row["state"]).strip()
        if not city or not state:
            raise RuntimeError("Failed to select a valid city/state from prepared dataframe")

        df_scope = df[(df["city"] == city) & (df["state"] == state)].copy()
        df_scope = df_scope.sort_values("period")

        print(f"🎯 Sample ingest selected: {city}, {state} ({len(df_scope)} rows)")
        upload_to_supabase_scoped(df_scope, earliest_period=earliest_period, city=city, state=state)

        return {
            "city": city,
            "state": state,
            "rows": int(len(df_scope)),
            "earliest_period": earliest_period,
            "has_ratio": bool("sale_to_list_ratio" in df_scope.columns),
        }
    finally:
        if gz_path:
            try:
                os.remove(gz_path)
            except OSError:
                pass


if __name__ == "__main__":
    ingest_redfin()