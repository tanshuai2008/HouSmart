from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


# Allow running from any directory
_BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))


from app.config.db import require_supabase
from app.services.census_service import CensusService
from app.services.market_trends_service import _normalize_state


def _safe(val: Any) -> str:
    if val is None:
        return ""
    return str(val).replace("\n", " ").strip()


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

    street = _pick_first_non_empty(row.get("street"), row.get("street_address"), row.get("line1"))
    city = _pick_first_non_empty(row.get("city"))
    state = _pick_first_non_empty(row.get("state"))
    zip_code = _pick_first_non_empty(row.get("zip"), row.get("zip_code"), row.get("postal_code"))
    parts = [p for p in [street, city, state, zip_code] if isinstance(p, str) and p.strip()]
    if not parts:
        return None
    return ", ".join(parts)


def main() -> None:
    """Print property_ids that will produce non-empty market trends.

    This uses whatever data is already uploaded in Supabase:
    - `user_properties` for property ids + addresses
    - `redfin_city_monthly_trends` for trend rows

    Output includes ready-to-open dashboard URLs.
    """

    frontend_base = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000").rstrip("/")

    sb = require_supabase()

    # Pull some recent user_properties (increase this if matches are rare).
    props_resp = sb.table("user_properties").select("*").limit(200).execute()
    props = props_resp.data or []
    if not props:
        raise SystemExit("No rows found in Supabase table 'user_properties'.")

    matches: list[dict] = []

    # For each property, check if any Redfin rows exist for that city/state.
    # (We only need a quick existence check.)
    for prop in props:
        prop_id = prop.get("id") or prop.get("property_id")
        prop_id = str(prop_id) if prop_id is not None else ""

        address = _build_address_from_row(prop) or ""
        city = _safe(prop.get("city"))
        state = _safe(prop.get("state"))

        if address and (not city or not state):
            try:
                loc = CensusService.get_location_data(address)
                if isinstance(loc, dict):
                    city = _safe(loc.get("city")) or city
                    state = _safe(loc.get("state")) or state
            except Exception:
                pass

        state_norm = _normalize_state(state)
        if not prop_id or not city or not state_norm:
            continue

        try:
            r = (
                sb.table("redfin_city_monthly_trends")
                .select("period", count="exact")
                .ilike("city", f"%{city}%")
                .ilike("state", f"%{state_norm}%")
                .limit(1)
                .execute()
            )
            count = getattr(r, "count", None)
        except Exception:
            continue

        if isinstance(count, int) and count > 0:
            matches.append(
                {
                    "id": prop_id,
                    "city": city,
                    "state": state_norm,
                    "address": address,
                    "count": count,
                }
            )

        if len(matches) >= 10:
            break

    if not matches:
        print("No property matches found with current uploaded Redfin data.")
        print("This means redfin_city_monthly_trends has no rows for the sampled properties' cities.")
        return

    print("Found properties with existing Redfin rows (use these property_ids):")
    for i, m in enumerate(matches, start=1):
        url = f"{frontend_base}/dashboard?property_id={m['id']}"
        print(
            f"{i}. {m['city']}, {m['state']}  redfin_rows={m['count']}\n"
            f"   property_id={m['id']}\n"
            f"   address={m['address']}\n"
            f"   dashboard_url={url}\n"
        )


if __name__ == "__main__":
    main()
