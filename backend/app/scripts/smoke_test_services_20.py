from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable

import requests

from app.config.db import require_supabase


DEFAULT_BACKEND_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
DEFAULT_FRONTEND_URL = os.getenv("FRONTEND_BASE_URL", "http://127.0.0.1:3000")


@dataclass(frozen=True)
class PropertyInput:
    id: str
    address: str | None
    city: str | None
    state: str | None
    lat: float | None
    lon: float | None


def _to_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def fetch_20_properties() -> list[PropertyInput]:
    supabase = require_supabase()
    resp = (
        supabase.table("properties")
        .select("id,formatted_address,city,state,latitude,longitude")
        .order("id", desc=True)
        .limit(20)
        .execute()
    )

    rows = resp.data or []
    props: list[PropertyInput] = []
    for row in rows:
        props.append(
            PropertyInput(
                id=str(row["id"]),
                address=row.get("formatted_address"),
                city=row.get("city"),
                state=row.get("state"),
                lat=_to_float(row.get("latitude")),
                lon=_to_float(row.get("longitude")),
            )
        )
    return props


def _req(method: str, url: str, *, json_body: Any | None = None, timeout: float = 30.0):
    headers = {"accept": "application/json"}
    if method.upper() in {"POST", "PUT", "PATCH"}:
        headers["content-type"] = "application/json"

    return requests.request(
        method=method,
        url=url,
        headers=headers,
        json=json_body,
        timeout=timeout,
    )


def run_backend_checks(properties: list[PropertyInput], backend_url: str) -> dict:
    results: dict[str, Any] = {
        "backend_url": backend_url,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "properties_tested": len(properties),
        "checks": [],
    }

    # Global health check
    try:
        r = _req("GET", f"{backend_url}/health", timeout=10)
        results["health"] = {"status_code": r.status_code, "ok": r.ok}
    except Exception as e:
        results["health"] = {"ok": False, "error": str(e)}

    def add_check(name: str, prop: PropertyInput, fn: Callable[[], requests.Response | None]):
        entry: dict[str, Any] = {"name": name, "property_id": prop.id}
        try:
            resp = fn()
            if resp is None:
                entry["status"] = "skipped"
                results["checks"].append(entry)
                return
            entry["status_code"] = resp.status_code
            entry["ok"] = bool(resp.ok)
            try:
                entry["json"] = resp.json()
            except Exception:
                entry["text"] = resp.text[:500]
            entry["status"] = "pass" if resp.ok else "fail"
        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)
        results["checks"].append(entry)

    for prop in properties:
        address = (prop.address or "").strip()
        city = (prop.city or "").strip()
        state = (prop.state or "").strip()

        # Market trends (new real-data endpoint)
        add_check(
            "market_trends",
            prop,
            lambda p=prop: _req(
                "GET",
                f"{backend_url}/api/market-trends?property_id={p.id}&months=36",
                timeout=20,
            ),
        )

        # Noise by address
        add_check(
            "noise_estimate_address",
            prop,
            (lambda a=address: None)
            if not address
            else (lambda a=address: _req("GET", f"{backend_url}/api/noise-estimate/address?address={requests.utils.quote(a)}", timeout=25)),
        )

        # Noise by coordinates
        add_check(
            "noise_estimate_coordinates",
            prop,
            (lambda: None)
            if prop.lat is None or prop.lon is None
            else (lambda lat=prop.lat, lon=prop.lon: _req("GET", f"{backend_url}/api/noise-estimate/coordinates?lat={lat}&lon={lon}", timeout=25)),
        )

        # Median house price (city/state)
        add_check(
            "median_house_price",
            prop,
            (lambda: None)
            if not city or not state
            else (lambda c=city, s=state: _req("GET", f"{backend_url}/api/median-house-price?city={requests.utils.quote(c)}&state={requests.utils.quote(s)}", timeout=25)),
        )

        # Education level
        add_check(
            "education_level",
            prop,
            (lambda: None)
            if not address
            else (lambda a=address: _req("POST", f"{backend_url}/api/education-level", json_body={"address": a}, timeout=30)),
        )

        # Median income
        add_check(
            "median_income",
            prop,
            (lambda: None)
            if not address
            else (lambda a=address: _req("POST", f"{backend_url}/api/median-income", json_body={"address": a}, timeout=30)),
        )

        # Rent estimate (can be slow / may depend on external service)
        add_check(
            "rent_estimate",
            prop,
            (lambda: None)
            if not address
            else (
                lambda a=address, c=city or None, s=state or None: _req(
                    "POST",
                    f"{backend_url}/api/rent-estimate",
                    json_body={"address": a, "city": c, "state": s, "compCount": 3},
                    timeout=40,
                )
            ),
        )

        # Transit score by coordinates (async endpoint)
        add_check(
            "transit_score",
            prop,
            (lambda: None)
            if prop.lat is None or prop.lon is None
            else (lambda lat=prop.lat, lon=prop.lon: _req("GET", f"{backend_url}/transit/score?lat={lat}&lng={lon}&radius_meters=800", timeout=40)),
        )

        # Flood check by coordinates
        add_check(
            "flood_check",
            prop,
            (lambda: None)
            if prop.lat is None or prop.lon is None
            else (lambda lat=prop.lat, lon=prop.lon: _req("GET", f"{backend_url}/flood/check?lat={lat}&lng={lon}", timeout=40)),
        )

        # Road map import (place string); heavy OSM call so only run for first 3 props
        if prop.id in {p.id for p in properties[:3]} and city and state:
            add_check(
                "road_map",
                prop,
                (lambda place=f"{city}, {state}": _req("GET", f"{backend_url}/api/road-map?place={requests.utils.quote(place)}", timeout=60)),
            )

        # Crime score (can be rate-limited / requires external data) only for first 3 props
        if prop.id in {p.id for p in properties[:3]} and address:
            add_check(
                "crime_score",
                prop,
                (lambda a=address: _req("POST", f"{backend_url}/api/crime-score/", json_body={"address": a}, timeout=60)),
            )

        # POI evaluation (known to be flaky depending on Supabase RPC) only for first 3 props
        if prop.id in {p.id for p in properties[:3]} and prop.lat is not None and prop.lon is not None:
            add_check(
                "evaluation_amenity_score",
                prop,
                (lambda lat=prop.lat, lon=prop.lon: _req("POST", f"{backend_url}/evaluation/amenity-score", json_body={"latitude": lat, "longitude": lon}, timeout=60)),
            )

    return results


def run_frontend_checks(properties: list[PropertyInput], frontend_url: str) -> dict:
    results: dict[str, Any] = {
        "frontend_url": frontend_url,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "pages": [],
    }

    for prop in properties:
        url = f"{frontend_url}/dashboard?property_id={prop.id}"
        entry: dict[str, Any] = {"property_id": prop.id, "url": url}
        try:
            r = _req("GET", url, timeout=20)
            entry["status_code"] = r.status_code
            entry["ok"] = bool(r.ok)
            entry["status"] = "pass" if r.ok else "fail"
        except Exception as e:
            entry["status"] = "error"
            entry["error"] = str(e)
        results["pages"].append(entry)

    return results


def main() -> None:
    backend_url = DEFAULT_BACKEND_URL
    frontend_url = DEFAULT_FRONTEND_URL

    props = fetch_20_properties()
    if not props:
        raise SystemExit("No properties found in Supabase 'properties' table")

    report: dict[str, Any] = {
        "backend": run_backend_checks(props, backend_url=backend_url),
        "frontend": run_frontend_checks(props, frontend_url=frontend_url),
    }

    out_path = os.path.join(os.path.dirname(__file__), "..", "..", "smoke_test_report.json")
    out_path = os.path.abspath(out_path)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Console summary
    def summarize(entries: list[dict[str, Any]]) -> dict[str, int]:
        counts: dict[str, int] = {"pass": 0, "fail": 0, "error": 0, "skipped": 0}
        for e in entries:
            status = e.get("status")
            if status in counts:
                counts[status] += 1
        return counts

    backend_counts = summarize(report["backend"]["checks"])
    frontend_counts = summarize(report["frontend"]["pages"])

    print("\n=== Smoke Test Summary ===")
    print(f"Backend:  pass={backend_counts['pass']} fail={backend_counts['fail']} error={backend_counts['error']} skipped={backend_counts['skipped']}")
    print(f"Frontend: pass={frontend_counts['pass']} fail={frontend_counts['fail']} error={frontend_counts['error']}")
    print(f"Report written to: {out_path}")


if __name__ == "__main__":
    main()
