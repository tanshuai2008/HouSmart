from __future__ import annotations

from datetime import date
from typing import Any

from app.core.redfin_trends import redfin_trends_table_candidates
from app.services.census_service import CensusService
from app.services.supabase_client import get_supabase


class MarketTrendsError(RuntimeError):
    pass


_US_STATE_ABBR: dict[str, str] = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
}

_US_STATE_NAME_BY_ABBR: dict[str, str] = {abbr: name.title() for name, abbr in _US_STATE_ABBR.items()}


def _normalize_state(state: str | None) -> str:
    if not isinstance(state, str):
        return ""
    value = state.strip()
    if not value:
        return ""
    if len(value) == 2 and value.isalpha():
        return value.upper()
    return _US_STATE_ABBR.get(value.lower(), value)


def _state_variants(state: str | None) -> list[str]:
    if not isinstance(state, str) or not state.strip():
        return []

    value = state.strip()
    candidates: list[str] = []

    if len(value) == 2 and value.isalpha():
        abbr = value.upper()
        candidates.append(abbr)
        full = _US_STATE_NAME_BY_ABBR.get(abbr)
        if full:
            candidates.append(full)
        return candidates

    normalized = " ".join(value.split()).strip()
    candidates.append(normalized)
    abbr = _US_STATE_ABBR.get(normalized.lower())
    if abbr:
        candidates.append(abbr)
    candidates.append(normalized.title())

    out: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate and candidate not in seen:
            seen.add(candidate)
            out.append(candidate)
    return out


def _pick_first_non_empty(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _build_address_from_row(row: dict[str, Any]) -> str | None:
    address = _pick_first_non_empty(
        row.get("formatted_address"),
        row.get("full_address"),
        row.get("address"),
    )
    if address:
        return address

    street = _pick_first_non_empty(row.get("street"), row.get("street_address"), row.get("line1"))
    city = _pick_first_non_empty(row.get("city"))
    state = _pick_first_non_empty(row.get("state"))
    zip_code = _pick_first_non_empty(row.get("zip"), row.get("zip_code"), row.get("postal_code"))
    parts = [part for part in (street, city, state, zip_code) if part]
    return ", ".join(parts) if parts else None


def _get_property_location(property_id: str) -> dict[str, Any]:
    supabase = get_supabase()

    rows: list[dict[str, Any]] = []
    last_error: Exception | None = None
    for col in ("id", "property_id"):
        try:
            resp = supabase.table("user_properties").select("*").eq(col, property_id).limit(1).execute()
            rows = resp.data or []
            if rows:
                break
        except Exception as exc:
            last_error = exc

    if not rows and last_error is not None:
        raise MarketTrendsError(f"Unable to query user_properties for property id={property_id}: {last_error}")
    if not rows:
        raise MarketTrendsError(f"Property id={property_id} not found in user_properties")

    row = rows[0] or {}
    address = _build_address_from_row(row)
    if not address:
        raise MarketTrendsError(f"Property id={property_id} is missing an address in user_properties")

    city = _pick_first_non_empty(row.get("city"))
    state = _pick_first_non_empty(row.get("state"))
    try:
        loc = CensusService.get_location_data(address)
        if isinstance(loc, dict):
            city = _pick_first_non_empty(loc.get("city"), city)
            state = _pick_first_non_empty(loc.get("state"), state)
    except Exception:
        pass

    return {
        "address": address,
        "city": city,
        "state": state,
        "source": "user_properties",
    }


def _safe_select_redfin_trends_from_table(
    *, table_name: str, city: str, state: str, limit: int
) -> tuple[list[dict[str, Any]], bool]:
    supabase = get_supabase()
    state_candidates = _state_variants(state)
    city_clean = (city or "").strip()

    for st in state_candidates:
        try:
            resp = (
                supabase.table(table_name)
                .select("period,median_price,sale_to_list_ratio")
                .eq("city", city_clean)
                .eq("state", st)
                .order("period", desc=True)
                .limit(limit)
                .execute()
            )
            rows = resp.data or []
            if rows:
                return rows, True
        except Exception:
            pass

    for st in state_candidates:
        try:
            resp = (
                supabase.table(table_name)
                .select("period,median_price,sale_to_list_ratio")
                .ilike("city", city_clean)
                .eq("state", st)
                .order("period", desc=True)
                .limit(limit)
                .execute()
            )
            rows = resp.data or []
            if rows:
                return rows, True
        except Exception:
            pass

    for st in state_candidates:
        try:
            resp = (
                supabase.table(table_name)
                .select("period,median_price")
                .eq("city", city_clean)
                .eq("state", st)
                .order("period", desc=True)
                .limit(limit)
                .execute()
            )
            rows = resp.data or []
            if rows:
                return rows, False
        except Exception:
            pass

    for st in state_candidates:
        try:
            resp = (
                supabase.table(table_name)
                .select("period,median_price")
                .ilike("city", city_clean)
                .eq("state", st)
                .order("period", desc=True)
                .limit(limit)
                .execute()
            )
            rows = resp.data or []
            if rows:
                return rows, False
        except Exception:
            pass

    fuzzy_limit = max(limit * 4, limit)
    for st in state_candidates:
        try:
            resp = (
                supabase.table(table_name)
                .select("period,median_price,sale_to_list_ratio")
                .ilike("city", f"%{city_clean}%")
                .eq("state", st)
                .order("period", desc=True)
                .limit(fuzzy_limit)
                .execute()
            )
            rows = resp.data or []
            if rows:
                return rows, True
        except Exception:
            pass

    state_norm = _normalize_state(state)
    try:
        resp = (
            supabase.table(table_name)
            .select("period,median_price,sale_to_list_ratio")
            .ilike("city", f"%{city_clean}%")
            .ilike("state", f"%{state_norm}%")
            .order("period", desc=True)
            .limit(fuzzy_limit)
            .execute()
        )
        rows = resp.data or []
        if rows:
            return rows, True
    except Exception:
        pass

    try:
        resp = (
            supabase.table(table_name)
            .select("period,median_price")
            .ilike("city", f"%{city_clean}%")
            .ilike("state", f"%{state_norm}%")
            .order("period", desc=True)
            .limit(fuzzy_limit)
            .execute()
        )
        return (resp.data or []), False
    except Exception:
        return [], False


def _safe_select_redfin_trends(city: str, state: str, limit: int) -> tuple[list[dict[str, Any]], bool]:
    for table_name in redfin_trends_table_candidates():
        rows, has_ratio = _safe_select_redfin_trends_from_table(
            table_name=table_name,
            city=city,
            state=state,
            limit=limit,
        )
        if rows:
            return rows, has_ratio
    return [], False


def get_market_trends_for_property(property_id: str, months: int = 36) -> dict[str, Any]:
    prop = _get_property_location(property_id)

    city = (prop.get("city") or "").strip()
    state = _normalize_state(prop.get("state"))
    if not city or not state:
        raise MarketTrendsError(
            f"Property id={property_id} is missing city/state (got city={city!r}, state={state!r})"
        )

    rows_desc, has_ratio = _safe_select_redfin_trends(city=city, state=state, limit=months)
    rows = list(reversed(rows_desc))

    def period_label(period: str | None) -> str:
        if not isinstance(period, str) or not period:
            return ""
        return period[:7]

    rows_by_month: dict[str, dict[str, Any]] = {}
    for row in rows:
        period = period_label(row.get("period"))
        if period:
            rows_by_month[period] = row

    months_sorted = sorted(rows_by_month.keys())
    rows = [rows_by_month[month] for month in months_sorted]
    if months and len(rows) > months:
        rows = rows[-months:]

    revenue_expenses = []
    for row in rows:
        period = period_label(row.get("period"))
        median_price = row.get("median_price")
        if period and median_price is not None:
            revenue_expenses.append({"month": period, "revenue": int(median_price), "expenses": 0})

    price_trend = []
    if has_ratio:
        for row in rows:
            period = period_label(row.get("period"))
            ratio = row.get("sale_to_list_ratio")
            if not period or ratio is None:
                continue
            try:
                ratio_value = float(ratio)
            except (TypeError, ValueError):
                continue
            ratio_pct = ratio_value * 100.0 if ratio_value <= 2.0 else ratio_value
            price_trend.append({"month": period, "property": ratio_pct, "market": 0.0})

    return {
        "property": {
            "property_id": property_id,
            "address": prop.get("address"),
            "city": city,
            "state": state,
            "source": prop.get("source"),
        },
        "as_of": date.today().isoformat(),
        "priceTrend": price_trend,
        "revenueExpenses": revenue_expenses,
        "notes": {
            "requires_historical_redfin_rows": True,
            "has_sale_to_list_ratio": bool(price_trend),
        },
    }
