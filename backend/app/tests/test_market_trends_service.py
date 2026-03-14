from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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

    def select(self, _cols: str):
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

    def execute(self):
        return FakeResponse(self._supabase._execute(self._table, self._filters))


class FakeSupabase:
    def __init__(self, *, user_properties: list[dict] | None, redfin: list[dict]):
        self._user_properties = user_properties
        self._redfin = redfin

    def table(self, name: str) -> _Query:
        if name == "user_properties" and self._user_properties is None:
            raise RuntimeError("user_properties does not exist")
        return _Query(self, name)

    def _execute(self, table: str, filters: list[tuple[str, str, Any]]):
        if table == "user_properties":
            rows = list(self._user_properties or [])
        elif table in ("redfin_median_prices", "redfin_city_monthly_trends"):
            rows = list(self._redfin)
        else:
            rows = []

        def match(row: dict) -> bool:
            for op, col, value in filters:
                if op == "eq" and row.get(col) != value:
                    return False
                if op == "ilike":
                    needle = str(value).strip("%").lower()
                    if needle not in str(row.get(col, "")).lower():
                        return False
            return True

        return [row for row in rows if match(row)]


def test_market_trends_uses_user_properties_by_id(monkeypatch: pytest.MonkeyPatch):
    fake = FakeSupabase(
        user_properties=[
            {
                "id": "p1",
                "formatted_address": "1 Main St, Seattle, WA",
                "city": "Seattle",
                "state": "WA",
            }
        ],
        redfin=[
            {"period": "2024-01-31", "median_price": 900000, "sale_to_list_ratio": 0.992, "city": "Seattle", "state": "WA"},
            {"period": "2024-02-29", "median_price": 910000, "sale_to_list_ratio": 0.995, "city": "Seattle", "state": "WA"},
        ],
    )

    monkeypatch.setattr(svc, "get_supabase", lambda: fake)

    payload = svc.get_market_trends_for_property("p1", months=36)

    assert payload["property"]["source"] == "user_properties"
    assert payload["property"]["address"] == "1 Main St, Seattle, WA"
    assert payload["revenueExpenses"]
    assert payload["priceTrend"]
    assert payload["priceTrend"][0]["property"] == pytest.approx(99.2)


def test_market_trends_uses_user_properties_by_property_id(monkeypatch: pytest.MonkeyPatch):
    fake = FakeSupabase(
        user_properties=[
            {
                "property_id": "p2",
                "address": "2 Main St",
                "city": "San Francisco",
                "state": "California",
            }
        ],
        redfin=[
            {"period": "2024-01-31", "median_price": 1500000, "city": "San Francisco", "state": "CA"},
        ],
    )

    monkeypatch.setattr(svc, "get_supabase", lambda: fake)

    payload = svc.get_market_trends_for_property("p2", months=36)

    assert payload["property"]["address"] == "2 Main St"
    assert payload["revenueExpenses"][0]["revenue"] == 1500000


def test_market_trends_requires_user_properties_table(monkeypatch: pytest.MonkeyPatch):
    fake = FakeSupabase(user_properties=None, redfin=[])
    monkeypatch.setattr(svc, "get_supabase", lambda: fake)

    with pytest.raises(svc.MarketTrendsError):
        svc.get_market_trends_for_property("p3", months=36)


def test_market_trends_requires_user_properties_row(monkeypatch: pytest.MonkeyPatch):
    fake = FakeSupabase(user_properties=[], redfin=[])
    monkeypatch.setattr(svc, "get_supabase", lambda: fake)

    with pytest.raises(svc.MarketTrendsError):
        svc.get_market_trends_for_property("missing", months=36)


def test_market_trends_uses_address_to_fill_missing_city_state(monkeypatch: pytest.MonkeyPatch):
    fake = FakeSupabase(
        user_properties=[
            {
                "id": "p4",
                "formatted_address": "4 Main St, Seattle, WA",
                "city": "",
                "state": "",
            }
        ],
        redfin=[
            {"period": "2024-01-31", "median_price": 900000, "city": "Seattle", "state": "WA"},
        ],
    )

    class FakeCensus:
        @staticmethod
        def get_location_data(_address: str) -> dict[str, str]:
            return {"city": "Seattle", "state": "WA"}

    monkeypatch.setattr(svc, "get_supabase", lambda: fake)
    monkeypatch.setattr(svc, "CensusService", FakeCensus, raising=False)

    payload = svc.get_market_trends_for_property("p4", months=36)

    assert payload["property"]["city"] == "Seattle"
    assert payload["property"]["state"] == "WA"
    assert payload["revenueExpenses"]
