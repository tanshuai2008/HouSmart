from __future__ import annotations

import gzip
from datetime import date
from pathlib import Path

import pandas as pd

from app.scripts.ingest_redfin import prepare_dataframe


def _write_gz_tsv(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        df.to_csv(f, sep="\t", index=False)


def test_prepare_dataframe_filters_and_keeps_last_36_per_city_state(tmp_path: Path):
    # Build a tiny synthetic Redfin-like dataset.
    rows: list[dict] = []

    def add(
        *,
        city: str,
        state: str,
        period_end: str,
        median_sale_price: int,
        avg_sale_to_list: float,
        region_type: str = "place",
        property_type: str = "All Residential",
    ) -> None:
        rows.append(
            {
                "city": city,
                "state": state,
                "region_type": region_type,
                "property_type": property_type,
                "period_end": period_end,
                "median_sale_price": median_sale_price,
                "AVG_SALE_TO_LIST": avg_sale_to_list,
            }
        )

    # City A has 40 months -> should be truncated to 36 most recent.
    # Use first-of-month dates for predictable ordering.
    for i in range(40):
        y = 2022 + ((i + 0) // 12)
        m = ((i + 0) % 12) + 1
        add(
            city="Alpha",
            state="CA",
            period_end=f"{y:04d}-{m:02d}-01",
            median_sale_price=500_000 + i,
            avg_sale_to_list=0.975 + (i * 0.0001),
        )

    # City B has 10 months -> should keep all 10.
    for i in range(10):
        y = 2024
        m = i + 1
        add(
            city="Beta",
            state="TX",
            period_end=f"{y:04d}-{m:02d}-01",
            median_sale_price=300_000 + i,
            avg_sale_to_list=1.0123,
        )

    # Noise rows that must be filtered out.
    add(
        city="Gamma",
        state="WA",
        period_end="2024-01-01",
        median_sale_price=123,
        avg_sale_to_list=1.0,
        region_type="county",
    )
    add(
        city="Delta",
        state="WA",
        period_end="2024-01-01",
        median_sale_price=123,
        avg_sale_to_list=1.0,
        property_type="Condo/Co-op",
    )

    raw = pd.DataFrame(rows)
    gz_path = tmp_path / "city_market_tracker.tsv000.gz"
    _write_gz_tsv(gz_path, raw)

    df, earliest_period = prepare_dataframe(str(gz_path))

    # Only place + All Residential
    assert set(df["city"].unique()).issubset({"Alpha", "Beta"})
    assert "Gamma" not in set(df["city"].unique())
    assert "Delta" not in set(df["city"].unique())

    # Truncation per place
    alpha = df[(df["city"] == "Alpha") & (df["state"] == "CA")]
    beta = df[(df["city"] == "Beta") & (df["state"] == "TX")]
    assert len(alpha) == 36
    assert len(beta) == 10

    # Ensure Alpha kept the most recent 36 months.
    # Original Alpha months ran from 2022-01-01 .. 2025-04-01 (40 months).
    # Keeping last 36 means dropping the earliest 4 months: 2022-01..2022-04.
    alpha_periods = sorted(alpha["period"].tolist())
    assert alpha_periods[0] == "2022-05-01"
    assert alpha_periods[-1] == "2025-04-01"

    # Columns are normalized
    assert set(["city", "state", "period", "median_price"]).issubset(df.columns)
    assert "sale_to_list_ratio" in df.columns

    # Types/formatting
    assert isinstance(earliest_period, str)
    # earliest_period should be the earliest kept across both places.
    assert earliest_period == "2022-05-01"

    # median_price coerced to int64 (or pandas nullable equivalent)
    assert pd.api.types.is_integer_dtype(df["median_price"].dtype)

    # ratio rounded to 2 decimals
    assert all(isinstance(x, float) for x in df["sale_to_list_ratio"].head(3).tolist())
