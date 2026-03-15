from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Allow running this script from any CWD by ensuring `backend/` is on sys.path.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from fastapi.testclient import TestClient

from app.config.db import require_supabase
from app.main import app
from app.services.geocode import geocode_address


def _pick_property_rows(*, limit: int = 100) -> list[dict[str, Any]]:
    supabase = require_supabase()

    # Schema varies across deployments; keep this tolerant.
    try:
        response = supabase.table("user_properties").select("*").limit(limit).execute()
    except Exception as e:
        raise RuntimeError(f"Failed to query user_properties: {e}")

    rows = response.data or []
    if not rows:
        raise RuntimeError("user_properties is empty; cannot smoke test")

    return list(rows)


def _extract_property_id(row: dict[str, Any]) -> str | None:
    for key in ("property_id", "id"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _build_address(row: dict[str, Any]) -> str | None:
    # Prefer a single full address field if present.
    for key in ("formatted_address", "full_address", "address"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Otherwise attempt to assemble.
    street = (
        row.get("street_address")
        or row.get("street")
        or row.get("line1")
        or row.get("address1")
        or ""
    )
    city = row.get("city") or ""
    state = row.get("state") or ""
    postal = row.get("zip") or row.get("zipcode") or row.get("postal_code") or ""

    parts = [str(street).strip(), str(city).strip(), str(state).strip(), str(postal).strip()]
    parts = [p for p in parts if p]
    if not parts:
        return None

    # Join as: "street, city, state zip"
    if len(parts) >= 2:
        street_part = parts[0]
        city_part = parts[1] if len(parts) > 1 else ""
        state_part = parts[2] if len(parts) > 2 else ""
        zip_part = parts[3] if len(parts) > 3 else ""

        tail = " ".join([p for p in (state_part, zip_part) if p]).strip()
        if city_part and tail:
            return f"{street_part}, {city_part}, {tail}"
        if city_part:
            return f"{street_part}, {city_part}"
        if tail:
            return f"{street_part}, {tail}"

    return ", ".join(parts)


def _extract_lat_lon(row: dict[str, Any]) -> tuple[float, float] | None:
    for lat_key, lon_key in (("latitude", "longitude"), ("lat", "lon"), ("lat", "lng")):
        lat = row.get(lat_key)
        lon = row.get(lon_key)
        if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
            return float(lat), float(lon)
    return None


def _print_json(title: str, payload: Any) -> None:
    print(f"\n--- {title} ---")
    print(json.dumps(payload, indent=2, default=str)[:2000])


def main() -> int:
    client = TestClient(app)

    MONTHS = 24

    rows = _pick_property_rows(limit=120)
    print(f"Loaded user_properties rows: {len(rows)}")

    # Find a property_id that yields non-empty chart series.
    picked_row: dict[str, Any] | None = None
    picked_payload: dict[str, Any] | None = None
    picked_property_id: str | None = None

    attempted_market_trends = 0
    for row in rows:
        property_id = _extract_property_id(row)
        if not property_id:
            continue

        attempted_market_trends += 1
        r = client.get("/api/market-trends", params={"property_id": property_id, "months": MONTHS})
        if r.status_code != 200:
            continue

        data = r.json() if r.content else {}
        price_trend = data.get("priceTrend") or []
        revenue_expenses = data.get("revenueExpenses") or []

        # Require median sale price series at minimum; prefer also having ratio series.
        if not revenue_expenses:
            continue

        picked_row = row
        picked_payload = data
        picked_property_id = property_id

        # Prefer a row that also has sale-to-list ratio so BOTH graphs render.
        if price_trend:
            break

    if not picked_row or not picked_payload or not picked_property_id:
        raise RuntimeError(
            "Could not find any user_properties row that returns non-empty /api/market-trends. "
            "Check that user_properties has valid US addresses and that Redfin data exists for their cities."
        )

    row = picked_row
    property_id = picked_property_id

    print("Picked user_properties row keys:", sorted(row.keys())[:25], "...")
    print("Resolved property_id:", property_id)
    print("Market-trends attempts:", attempted_market_trends)

    attempted = 0
    failed = 0

    # 1) Dashboard market trends (graphs)
    if property_id:
        attempted += 1
        r = client.get("/api/market-trends", params={"property_id": property_id, "months": MONTHS})
        print("\nGET /api/market-trends status:", r.status_code)
        print("cache-control:", r.headers.get("cache-control"))
        if r.status_code != 200:
            _print_json("market-trends error", r.json())
            failed += 1
        else:
            data = r.json()
            print("priceTrend points:", len(data.get("priceTrend", [])))
            print("revenueExpenses points:", len(data.get("revenueExpenses", [])))
            _print_json("market-trends sample", {k: (v[:2] if isinstance(v, list) else v) for k, v in data.items()})
    else:
        print("\nSkipping /api/market-trends: no property_id field in user_properties row")

    # 2) Median house price
    city = (row.get("city") or "").strip() if isinstance(row.get("city"), str) else ""
    state = (row.get("state") or "").strip() if isinstance(row.get("state"), str) else ""

    if not city or not state:
        address = _build_address(row)
        if address:
            geo = geocode_address(address)
            if geo:
                _lat, _lon, geo_city, geo_state = geo
                city = (geo_city or "").strip()
                state = (geo_state or "").strip()

    if city and state:
        attempted += 1
        r = client.get("/api/median-house-price", params={"city": city, "state": state})
        print("\nGET /api/median-house-price status:", r.status_code, f"({city}, {state})")
        if r.status_code != 200:
            _print_json("median-house-price error", r.json())
            failed += 1
        else:
            _print_json("median-house-price", r.json())
    else:
        print("\nSkipping /api/median-house-price: could not resolve city/state")

    # 3) Noise estimate by address
    address = _build_address(row)
    if address:
        attempted += 1
        r = client.get("/api/noise-estimate/address", params={"address": address})
        print("\nGET /api/noise-estimate/address status:", r.status_code)
        if r.status_code != 200:
            _print_json("noise-estimate/address error", r.json())
            failed += 1
        else:
            _print_json("noise-estimate/address", r.json())
    else:
        print("\nSkipping /api/noise-estimate/address: no address available")

    # 4) Noise estimate by coordinates
    coords = _extract_lat_lon(row)
    if coords is None and address:
        geo = geocode_address(address)
        if geo:
            coords = (float(geo[0]), float(geo[1]))

    if coords:
        attempted += 1
        lat, lon = coords
        r = client.get("/api/noise-estimate/coordinates", params={"lat": lat, "lon": lon})
        print("\nGET /api/noise-estimate/coordinates status:", r.status_code)
        if r.status_code != 200:
            _print_json("noise-estimate/coordinates error", r.json())
            failed += 1
        else:
            _print_json("noise-estimate/coordinates", r.json())
    else:
        print("\nSkipping /api/noise-estimate/coordinates: no coords")

    print(f"\nAttempted: {attempted} | Failed: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
