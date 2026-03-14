from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pytest

import app.services.market_trends_service as svc


@dataclass
class FakeResponse:
    data: Any


class _Query:
    def __init__(self, supabase: "FakeSupabase", table: str):
        self._supabase = supabase
        self._table = table
        self._filters: list[tuple[str, str, Any]] = []
        self._select: str | None = None
        self._single = False

    def select(self, cols: str):
        self._select = cols
        return self

    def eq(self, col: str, value: Any):
        self._filters.append(("eq", col, value))
        return self

    def ilike(self, col: str, value: Any):
        self._filters.append(("ilike", col, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        return FakeResponse(self._supabase._execute(self._table, self._filters, single=self._single))


class FakeSupabase:
    def __init__(self, *, user_properties: list[dict] | None, properties: list[dict], redfin: list[dict]):
        self._user_properties = user_properties
        self._properties = properties
        self._redfin = redfin

    def table(self, name: str) -> _Query:
        if name == "user_properties" and self._user_properties is None:
            raise RuntimeError("user_properties does not exist")
        return _Query(self, name)

    def _execute(self, table: str, filters: list[tuple[str, str, Any]], *, single: bool):
        if table == "user_properties":
            rows = list(self._user_properties or [])
        elif table == "properties":
            rows = list(self._properties)
        elif table in ("redfin_median_prices", "redfin_city_monthly_trends"):
            rows = list(self._redfin)
        else:
            rows = []

        def match(row: dict) -> bool:
            for op, col, value in filters:
                if op == "eq":
                    if row.get(col) != value:
                        return False
                elif op == "ilike":
                    # Very small ilike simulation: "%(x)%" means substring match (case-insensitive).
                    v = str(row.get(col, ""))
                    needle = str(value).strip("%")
                    if needle.lower() not in v.lower():
                        return False
            return True

        filtered = [r for r in rows if match(r)]
        if single:
            return filtered[0] if filtered else None
        return filtered


def test_market_trends_uses_user_properties_by_id(monkeypatch):
    fake = FakeSupabase(
        user_properties=[
            {
                "id": "p1",
                "formatted_address": "1 Main St, Seattle, WA",
                "city": "Seattle",
                "state": "WA",
            }
        ],
        properties=[],
        redfin=[
            {"period": "2024-01-31", "median_price": 900000, "sale_to_list_ratio": 99.2, "city": "Seattle", "state": "WA"},
            {"period": "2024-02-29", "median_price": 910000, "sale_to_list_ratio": 99.5, "city": "Seattle", "state": "WA"},
        ],
    )

    monkeypatch.setattr(svc, "require_supabase", lambda: fake)

    payload = svc.get_market_trends_for_property("p1", months=36)

    assert payload["property"]["source"] == "user_properties"
    assert payload["property"]["address"] == "1 Main St, Seattle, WA"
    assert payload["revenueExpenses"]
    assert payload["priceTrend"]
    assert payload["revenueExpenses"][0]["month"].startswith("2024-")


def test_market_trends_uses_user_properties_by_property_id(monkeypatch):
    fake = FakeSupabase(
        user_properties=[
            {
                "property_id": "p2",
                "address": "2 Main St",
                "city": "San Francisco",
                "state": "California",
            }
        ],
        properties=[],
        redfin=[
            {"period": "2024-01-31", "median_price": 1500000, "city": "San Francisco", "state": "CA"},
        ],
    )

    monkeypatch.setattr(svc, "require_supabase", lambda: fake)

    payload = svc.get_market_trends_for_property("p2", months=36)
    assert payload["property"]["source"] == "user_properties"
    assert payload["property"]["address"] == "2 Main St"
    # State normalization should allow match against CA.
    assert payload["revenueExpenses"][0]["revenue"] == 1500000


def test_market_trends_requires_user_properties_table(monkeypatch):
    fake = FakeSupabase(
        user_properties=None,
        properties=[
            {"id": "p3", "formatted_address": "3 Main St, Austin, TX", "city": "Austin", "state": "TX"}
        ],
        redfin=[
            {"period": "2024-01-31", "median_price": 500000, "city": "Austin", "state": "TX"},
        ],
    )

    monkeypatch.setattr(svc, "require_supabase", lambda: fake)

    with pytest.raises(svc.MarketTrendsError):
        svc.get_market_trends_for_property("p3", months=36)


def test_market_trends_requires_user_properties_row(monkeypatch):
    fake = FakeSupabase(
        user_properties=[],
        properties=[],
        redfin=[],
    )
    monkeypatch.setattr(svc, "require_supabase", lambda: fake)

    with pytest.raises(svc.MarketTrendsError):
        svc.get_market_trends_for_property("missing", months=36)


def test_market_trends_uses_address_to_fill_missing_city_state(monkeypatch):
    fake = FakeSupabase(
        user_properties=[
            {
                "id": "p4",
                "formatted_address": "4 Main St, Seattle, WA",
                "city": "",
                "state": "",
            }
        ],
        properties=[],
        redfin=[
            {"period": "2024-01-31", "median_price": 900000, "city": "Seattle", "state": "WA"},
        ],
    )

    class FakeCensus:
        @staticmethod
        def get_location_data(_address: str) -> dict:
            return {"city": "Seattle", "state": "WA"}

    # Patch both supabase and census lookup.
    monkeypatch.setattr(svc, "require_supabase", lambda: fake)
    monkeypatch.setattr(svc, "CensusService", FakeCensus, raising=False)

    payload = svc.get_market_trends_for_property("p4", months=36)
    assert payload["property"]["city"] == "Seattle"
    assert payload["property"]["state"] == "WA"
    assert payload["revenueExpenses"]
