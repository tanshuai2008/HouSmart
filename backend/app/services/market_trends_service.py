from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from app.config.db import require_supabase
from app.core.redfin_trends import redfin_trends_table_candidates
from app.services.census_service import CensusService


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
    s = state.strip()
    if not s:
        return ""
    if len(s) == 2 and s.isalpha():
        return s.upper()
    return _US_STATE_ABBR.get(s.lower(), s)


def _state_variants(state: str | None) -> list[str]:
    """Return likely state representations found in Supabase.

    Redfin `city_market_tracker` commonly stores full state names (e.g. "California"),
    while other services may provide abbreviations (e.g. "CA").

    We prefer exact matches to avoid substring collisions ("CA" matches "North Carolina").
    """
    if not isinstance(state, str) or not state.strip():
        return []

    s = state.strip()
    candidates: list[str] = []

    # Abbreviation path
    if len(s) == 2 and s.isalpha():
        abbr = s.upper()
        candidates.append(abbr)
        full = _US_STATE_NAME_BY_ABBR.get(abbr)
        if full:
            candidates.append(full)
        return candidates

    # Full name path
    full_norm = " ".join(s.split()).strip()
    candidates.append(full_norm)
    abbr = _US_STATE_ABBR.get(full_norm.lower())
    if abbr:
        candidates.append(abbr)
    # Title-cased variant (matches typical Redfin formatting)
    candidates.append(full_norm.title())

    # De-dup, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _pick_first_non_empty(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _build_address_from_row(row: dict) -> str | None:
    address = _pick_first_non_empty(
        row.get("formatted_address"),
        row.get("full_address"),
        row.get("address"),
    )
    if address:
        return address

    # Common alternative schemas: street + city/state/zip.
    street = _pick_first_non_empty(row.get("street"), row.get("street_address"), row.get("line1"))
    city = _pick_first_non_empty(row.get("city"))
    state = _pick_first_non_empty(row.get("state"))
    zip_code = _pick_first_non_empty(row.get("zip"), row.get("zip_code"), row.get("postal_code"))

    parts = [p for p in [street, city, state, zip_code] if isinstance(p, str) and p.strip()]
    if not parts:
        return None
    return ", ".join(parts)


def _get_property_location(property_id: str) -> dict:
    """Resolve property address/city/state from Supabase `user_properties`.

    Requirements:
    - The dashboard graphs must be property-specific for the signed-in user's property.
    - We therefore resolve the address from `user_properties` and use that address to
      retrieve the matching Redfin city/state trend rows.
    """

    supabase = require_supabase()

    # Schema varies across deployments. Some DBs use (id), others use (property_id).
    # Also, a missing column causes a hard API error, so we must try each query independently.
    rows: list[dict] = []
    last_error: Exception | None = None

    for col in ("id", "property_id"):
        try:
            resp = (
                supabase.table("user_properties")
                .select("*")
                .eq(col, property_id)
                .limit(1)
                .execute()
            )
            rows = resp.data or []
            if rows:
                break
        except Exception as e:
            last_error = e
            continue

    if not rows and last_error is not None:
        raise MarketTrendsError(f"Unable to query user_properties for property id={property_id}: {last_error}")

    if not rows:
        raise MarketTrendsError(f"Property id={property_id} not found in user_properties")

    row = rows[0] or {}
    address = _build_address_from_row(row)
    if not address:
        raise MarketTrendsError(f"Property id={property_id} is missing an address in user_properties")

    # Prefer geocoding-derived city/state from the address for consistency.
    city = _pick_first_non_empty(row.get("city"))
    state = _pick_first_non_empty(row.get("state"))
    try:
        loc = CensusService.get_location_data(address)
        if isinstance(loc, dict):
            city = _pick_first_non_empty(loc.get("city"), city)
            state = _pick_first_non_empty(loc.get("state"), state)
    except Exception:
        # Non-fatal: use stored city/state if present.
        pass

    return {
        "address": address,
        "city": city,
        "state": state,
        "source": "user_properties",
    }


def _safe_select_redfin_trends_from_table(
    *, table_name: str, city: str, state: str, limit: int
) -> tuple[list[dict], bool]:
    """Return (rows, has_ratio_column) from a specific table."""

    supabase = require_supabase()

    state_candidates = _state_variants(state)
    city_clean = (city or "").strip()

    # 1) Prefer exact city + exact state (most precise; avoids substring collisions).
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

    # 1b) Case-insensitive exact city match (handles city casing like "RENTON" vs "Renton").
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

    # 2) Exact city + exact state, but without ratio column (if schema missing).
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

    # 2b) Case-insensitive exact city match, without ratio.
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

    # 3) Fallback: fuzzy city match, but keep state exact (full name preferred).
    # Fetch extra rows so we can de-dupe months reliably even if multiple places match.
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

    # 4) Last-chance: fuzzy city + fuzzy state (kept for backwards compatibility).
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


def _safe_select_redfin_trends(city: str, state: str, limit: int) -> tuple[list[dict], bool]:
    """Return (rows, has_ratio_column).

    Tries the thin trends table first and falls back to the legacy table.
    """

    for table_name in redfin_trends_table_candidates():
        rows, has_ratio = _safe_select_redfin_trends_from_table(
            table_name=table_name, city=city, state=state, limit=limit
        )
        if rows:
            return rows, has_ratio

    return [], False


def get_market_trends_for_property(property_id: str, months: int = 36) -> dict:
    """Build the dashboard market trend series for a given property.

    Returns a payload matching the frontend chart expectations.

    Notes:
    - Requires Supabase credentials.
    - Requires a Redfin trends table (`redfin_city_monthly_trends` preferred; falls back to `redfin_median_prices`).
    - `sale_to_list_ratio` is optional; if missing, `priceTrend` will be empty.
    """

    prop = _get_property_location(property_id)

    city = (prop.get("city") or "").strip()
    state = _normalize_state(prop.get("state"))
    if not city or not state:
        raise MarketTrendsError(
            f"Property id={property_id} is missing city/state (got city={city!r}, state={state!r})"
        )

    rows_desc, has_ratio = _safe_select_redfin_trends(city=city, state=state, limit=months)

    # We query desc for efficiency; charts want chronological.
    rows = list(reversed(rows_desc))

    def period_label(period: str | None) -> str:
        if not isinstance(period, str) or not period:
            return ""
        # Render as YYYY-MM for cleaner x-axis labels.
        return period[:7]

    # De-dupe any accidental duplicates per month. This can happen if the underlying
    # table contains duplicates or if a fuzzy query matched multiple cities.
    rows_by_month: dict[str, dict] = {}
    for row in rows:
        period = period_label(row.get("period"))
        if not period:
            continue
        rows_by_month[period] = row

    months_sorted = sorted(rows_by_month.keys())
    rows = [rows_by_month[m] for m in months_sorted]

    # Enforce requested window: keep only the most recent N months.
    if months and len(rows) > months:
        rows = rows[-months:]

    revenue_expenses = []
    for row in rows:
        period = period_label(row.get("period"))
        median_price = row.get("median_price")
        if not period or median_price is None:
            continue
        revenue_expenses.append({"month": period, "revenue": int(median_price), "expenses": 0})

    price_trend = []
    if has_ratio:
        for row in rows:
            period = period_label(row.get("period"))
            ratio = row.get("sale_to_list_ratio")
            if not period or ratio is None:
                continue
            try:
                ratio_f = float(ratio)
            except (TypeError, ValueError):
                continue

            # Redfin exports commonly express this as ~0.98–1.03 (i.e., 98%–103%).
            # The frontend chart is labeled in percent and uses a ~97–103 domain.
            ratio_pct = ratio_f * 100.0 if ratio_f <= 2.0 else ratio_f

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

