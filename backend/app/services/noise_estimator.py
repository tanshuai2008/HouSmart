from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import requests
from geopy.distance import geodesic

# Support running this file directly (e.g., `python backend/app/services/noise_estimator.py`).
_BACKEND_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT_FOR_IMPORTS))

from app.utils.cache_utils import get_cached, set_cache

NOMINATIM_URL = os.getenv(
    "HOUSMART_NOMINATIM_URL", "https://nominatim.openstreetmap.org/search"
)
OVERPASS_URL = os.getenv(
    "HOUSMART_OVERPASS_URL", "https://overpass-api.de/api/interpreter"
)
_USER_AGENT = os.getenv(
    "HOUSMART_NOISE_USER_AGENT", "HouSmartProject/1.0 (noise_estimator)"
)
_NOMINATIM_TIMEOUT = int(os.getenv("HOUSMART_NOMINATIM_TIMEOUT", "20"))
_OVERPASS_TIMEOUT = int(os.getenv("HOUSMART_OVERPASS_TIMEOUT", "60"))


@dataclass(frozen=True)
class _WayFeature:
    kind: str
    tags: dict[str, Any]
    geometry: list[tuple[float, float]]


def _safe_float(v: Any) -> float | None:
    try:
        return float(v)
    except Exception:
        return None


def geocode_address_details(address: str) -> dict[str, Any] | None:
    """Geocode a precise property address using Nominatim.

    Note: spatial/environment queries are done via Overpass; this step only
    converts the user-provided address into coordinates + a human label.
    """

    addr = str(address or "").strip()
    if not addr:
        return None

    params = {
        "q": addr,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }
    headers = {"User-Agent": _USER_AGENT}

    try:
        res = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=_NOMINATIM_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()
    except Exception:
        return None

    if not data:
        return None
    if not isinstance(data, list) or not isinstance(data[0], dict):
        return None
    return data[0]


def geocode_address(address: str) -> tuple[float, float] | None:
    details = geocode_address_details(address)
    if not details:
        return None
    lat = _safe_float(details.get("lat"))
    lon = _safe_float(details.get("lon"))
    if lat is None or lon is None:
        return None
    return lat, lon


def _place_name_from_geocode(address_input: str, details: dict[str, Any] | None) -> str:
    raw = str(address_input or "").strip()
    if not details:
        return raw
    addr = details.get("address") if isinstance(details.get("address"), dict) else {}
    city = (
        addr.get("city")
        or addr.get("town")
        or addr.get("village")
        or addr.get("hamlet")
    )
    state = addr.get("state")
    if city and state:
        return f"{city}, {state}"
    disp = details.get("display_name")
    if disp:
        # Keep it short-ish: first two segments tend to be a useful label.
        parts = [p.strip() for p in str(disp).split(",") if p.strip()]
        if len(parts) >= 2:
            return f"{parts[0]}, {parts[1]}"
        if parts:
            return parts[0]
    return raw


def _overpass_post(query: str, *, timeout: int = _OVERPASS_TIMEOUT) -> dict[str, Any] | None:
    headers = {"User-Agent": _USER_AGENT}
    # Overpass can be flaky; keep retries modest.
    for attempt in range(3):
        try:
            res = requests.post(OVERPASS_URL, data=query, headers=headers, timeout=timeout)
            res.raise_for_status()
            if not res.text.strip():
                return None
            return res.json()
        except Exception:
            # small backoff
            if attempt < 2:
                time.sleep(0.6 * (attempt + 1))
            else:
                return None
    return None


def _parse_way_features(elements: Iterable[dict[str, Any]], *, kind: str) -> list[_WayFeature]:
    out: list[_WayFeature] = []
    for el in elements:
        if el.get("type") != "way":
            continue
        geom = el.get("geometry")
        if not isinstance(geom, list) or not geom:
            continue
        pts: list[tuple[float, float]] = []
        for p in geom:
            lat = _safe_float(p.get("lat"))
            lon = _safe_float(p.get("lon"))
            if lat is None or lon is None:
                continue
            pts.append((lat, lon))
        if not pts:
            continue
        tags = el.get("tags") if isinstance(el.get("tags"), dict) else {}
        out.append(_WayFeature(kind=kind, tags=dict(tags), geometry=pts))
    return out


def _min_distance_m(lat: float, lon: float, pts: Iterable[tuple[float, float]]) -> float | None:
    min_d: float | None = None
    for p_lat, p_lon in pts:
        d = geodesic((lat, lon), (p_lat, p_lon)).meters
        if min_d is None or d < min_d:
            min_d = d
    return min_d


def _polyline_length_m(pts: list[tuple[float, float]]) -> float:
    total = 0.0
    for a, b in zip(pts, pts[1:]):
        total += geodesic(a, b).meters
    return total


_MAJOR_HIGHWAYS = {"motorway", "trunk", "primary", "secondary"}


def _highway_weight(highway: str | None) -> float:
    h = str(highway or "").strip().lower()
    if h in {"motorway"}:
        return 1.0
    if h in {"trunk"}:
        return 0.9
    if h in {"primary"}:
        return 0.75
    if h in {"secondary"}:
        return 0.6
    if h in {"tertiary"}:
        return 0.45
    if h in {"residential", "living_street"}:
        return 0.25
    if h in {"service", "unclassified"}:
        return 0.2
    return 0.3


def _distance_score(distance_m: float | None, *, near: float, far: float, max_points: float) -> float:
    """Linear decay: near->max_points, far->0."""
    if distance_m is None:
        return 0.0
    if distance_m <= near:
        return float(max_points)
    if distance_m >= far:
        return 0.0
    frac = 1.0 - ((distance_m - near) / max(1e-9, (far - near)))
    return float(max_points) * max(0.0, min(1.0, frac))


def _score_to_noise_level(score: float) -> str:
    if score >= 80:
        return "Very High"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Moderate"
    if score >= 20:
        return "Low"
    return "Very Low"


# ------------------------------------------------------------------
# Backwards-compatible helper used by existing tests/older code.
# ------------------------------------------------------------------
def _distance_to_noise(distance: float | None) -> str:
    if distance is None:
        return "Unknown"
    if distance < 20:
        return "Very High"
    if distance < 50:
        return "High"
    if distance < 150:
        return "Moderate"
    return "Low"


def _nearest_road_distance(lat: float, lon: float) -> float | None:
    """Nearest road distance within 200m (legacy metric)."""
    roads = _query_roads(lat, lon, radius_m=200)
    if not roads:
        return None
    best: float | None = None
    for way in roads:
        d = _min_distance_m(lat, lon, way.geometry)
        if d is None:
            continue
        if best is None or d < best:
            best = d
    return best


def _query_roads(lat: float, lon: float, *, radius_m: int) -> list[_WayFeature]:
    query = f"""
    [out:json];
    (
      way(around:{int(radius_m)},{lat},{lon})[\"highway\"];
    );
    out tags geom;
    """
    data = _overpass_post(query, timeout=60)
    if not data:
        return []
    return _parse_way_features(data.get("elements", []), kind="road")


def _query_railways(lat: float, lon: float, *, radius_m: int) -> list[_WayFeature]:
    query = f"""
    [out:json];
    (
      way(around:{int(radius_m)},{lat},{lon})[\"railway\"~\"rail|light_rail|subway|tram\"];
    );
    out tags geom;
    """
    data = _overpass_post(query, timeout=60)
    if not data:
        return []
    return _parse_way_features(data.get("elements", []), kind="rail")


def _query_airport_features(lat: float, lon: float, *, radius_m: int) -> list[dict[str, Any]]:
    # Airports are often large; we include aerodromes and runways/taxiways.
    query = f"""
    [out:json];
    (
      nwr(around:{int(radius_m)},{lat},{lon})[\"aeroway\"~\"aerodrome|runway|taxiway\"];
    );
    out tags geom;
    """
    data = _overpass_post(query, timeout=90)
    if not data:
        return []
    els = data.get("elements", [])
    if not isinstance(els, list):
        return []
    return [e for e in els if isinstance(e, dict)]


def _query_landuse(lat: float, lon: float, *, radius_m: int) -> list[str]:
    query = f"""
    [out:json];
    (
      way(around:{int(radius_m)},{lat},{lon})[\"landuse\"];
      relation(around:{int(radius_m)},{lat},{lon})[\"landuse\"];
    );
    out tags;
    """
    data = _overpass_post(query, timeout=60)
    if not data:
        return []
    types: list[str] = []
    for el in data.get("elements", []):
        tags = el.get("tags") if isinstance(el.get("tags"), dict) else {}
        lu = tags.get("landuse")
        if lu:
            types.append(str(lu).strip().lower())
    # de-dup, preserve order
    seen: set[str] = set()
    out: list[str] = []
    for t in types:
        if t and t not in seen:
            out.append(t)
            seen.add(t)
    return out


def _airport_min_distance_m(lat: float, lon: float, els: list[dict[str, Any]]) -> float | None:
    best: float | None = None
    for el in els:
        geom = el.get("geometry")
        if isinstance(geom, list) and geom:
            pts: list[tuple[float, float]] = []
            for p in geom:
                p_lat = _safe_float(p.get("lat"))
                p_lon = _safe_float(p.get("lon"))
                if p_lat is None or p_lon is None:
                    continue
                pts.append((p_lat, p_lon))
            d = _min_distance_m(lat, lon, pts)
        else:
            p_lat = _safe_float(el.get("lat"))
            p_lon = _safe_float(el.get("lon"))
            d = None if p_lat is None or p_lon is None else geodesic((lat, lon), (p_lat, p_lon)).meters
        if d is None:
            continue
        if best is None or d < best:
            best = d
    return best


def _compute_noise_factors(lat: float, lon: float) -> dict[str, Any] | None:
    """Query OSM (Overpass) and derive metrics needed for scoring."""

    roads_radius = 600
    rails_radius = 1200
    airports_radius = 7000
    landuse_radius = 500

    roads = _query_roads(lat, lon, radius_m=roads_radius)
    if not roads:
        return None

    road_infos: list[dict[str, Any]] = []
    total_length_m = 0.0
    nearest_any: float | None = None
    nearest_major: float | None = None
    major_count = 0

    for w in roads:
        highway = str(w.tags.get("highway") or "").strip().lower()
        d = _min_distance_m(lat, lon, w.geometry)
        if d is None:
            continue
        length_m = _polyline_length_m(w.geometry)
        total_length_m += length_m

        if nearest_any is None or d < nearest_any:
            nearest_any = d
        if highway in _MAJOR_HIGHWAYS:
            major_count += 1
            if nearest_major is None or d < nearest_major:
                nearest_major = d

        road_infos.append(
            {
                "highway": highway or None,
                "name": w.tags.get("name"),
                "distance_m": float(d),
                "length_m": float(length_m),
            }
        )

    road_infos.sort(key=lambda r: r.get("distance_m", math.inf))
    nearest_roads = road_infos[:5]

    rails = _query_railways(lat, lon, radius_m=rails_radius)
    nearest_rail: float | None = None
    for r in rails:
        d = _min_distance_m(lat, lon, r.geometry)
        if d is None:
            continue
        if nearest_rail is None or d < nearest_rail:
            nearest_rail = d

    airport_els = _query_airport_features(lat, lon, radius_m=airports_radius)
    nearest_airport = _airport_min_distance_m(lat, lon, airport_els) if airport_els else None

    landuse_types = _query_landuse(lat, lon, radius_m=landuse_radius)

    return {
        "roads": {
            "radius_m": roads_radius,
            "road_count": len(road_infos),
            "major_road_count": major_count,
            "total_road_length_m": round(total_length_m, 1),
            "nearest_road_distance_m": None if nearest_any is None else round(nearest_any, 2),
            "nearest_major_road_distance_m": None if nearest_major is None else round(nearest_major, 2),
            "nearest_roads": nearest_roads,
        },
        "railways": {
            "radius_m": rails_radius,
            "rail_count": len(rails),
            "nearest_rail_distance_m": None if nearest_rail is None else round(nearest_rail, 2),
        },
        "airports": {
            "radius_m": airports_radius,
            "airport_feature_count": len(airport_els),
            "nearest_airport_feature_distance_m": None
            if nearest_airport is None
            else round(nearest_airport, 2),
        },
        "landuse": {
            "radius_m": landuse_radius,
            "types": landuse_types,
        },
    }


def _compute_noise_score(factors: dict[str, Any]) -> tuple[float, dict[str, float]]:
    roads = factors.get("roads") if isinstance(factors.get("roads"), dict) else {}
    rails = factors.get("railways") if isinstance(factors.get("railways"), dict) else {}
    airports = factors.get("airports") if isinstance(factors.get("airports"), dict) else {}
    landuse = factors.get("landuse") if isinstance(factors.get("landuse"), dict) else {}

    nearest_road = roads.get("nearest_road_distance_m")
    nearest_major = roads.get("nearest_major_road_distance_m")
    total_road_length_m = float(roads.get("total_road_length_m") or 0.0)
    road_count = int(roads.get("road_count") or 0)
    nearest_rail = rails.get("nearest_rail_distance_m")
    nearest_airport = airports.get("nearest_airport_feature_distance_m")
    landuse_types = landuse.get("types") if isinstance(landuse.get("types"), list) else []

    # 1) Nearest road proximity (0..30)
    s_nearest = _distance_score(
        _safe_float(nearest_road), near=15, far=200, max_points=30
    )

    # 2) Major road proximity (0..25)
    s_major = _distance_score(
        _safe_float(nearest_major), near=30, far=600, max_points=25
    )

    # 3) Multi-road influence: sum of up to 5 nearest road contributions (0..15)
    s_multi = 0.0
    nearest_roads = roads.get("nearest_roads") if isinstance(roads.get("nearest_roads"), list) else []
    for info in nearest_roads[:5]:
        if not isinstance(info, dict):
            continue
        d = _safe_float(info.get("distance_m"))
        if d is None:
            continue
        hw = info.get("highway")
        w = _highway_weight(str(hw) if hw is not None else None)
        # decay to zero by 500m
        s_multi += (w * _distance_score(d, near=25, far=500, max_points=3.5))
    s_multi = min(15.0, s_multi)

    # 4) Road density within radius via total length + count (0..15)
    # Simple normalization: around ~600m radius, a few km of roads implies a dense area.
    s_density = 0.0
    s_density += min(10.0, (total_road_length_m / 4000.0) * 10.0)
    s_density += min(5.0, (road_count / 60.0) * 5.0)
    s_density = min(15.0, s_density)

    # 5) Rail proximity (0..10)
    s_rail = _distance_score(_safe_float(nearest_rail), near=40, far=600, max_points=10)

    # 6) Airport proximity (0..10) -- large radius and slower decay
    s_air = _distance_score(_safe_float(nearest_airport), near=800, far=7000, max_points=10)

    # 7) Landuse adjustment (-5..+10)
    s_land = 0.0
    land_set = {str(t).strip().lower() for t in landuse_types if str(t).strip()}
    if {"industrial", "commercial"} & land_set:
        s_land += 8.0
    if "retail" in land_set:
        s_land += 3.0
    if "residential" in land_set and not ({"industrial"} & land_set):
        s_land -= 4.0
    s_land = max(-5.0, min(10.0, s_land))

    parts = {
        "nearest_road": round(s_nearest, 2),
        "major_road": round(s_major, 2),
        "multi_roads": round(s_multi, 2),
        "road_density": round(s_density, 2),
        "rail": round(s_rail, 2),
        "airport": round(s_air, 2),
        "landuse": round(s_land, 2),
    }

    total = sum(parts.values())
    total = max(0.0, min(100.0, round(total, 2)))
    return total, parts


def _noise_cache_key(lat: float, lon: float) -> str:
    # Round to ~11m to maximize cache hits without over-collapsing.
    return f"noise:{round(lat, 4)}:{round(lon, 4)}"


def estimate_noise(lat: float, lon: float) -> dict[str, Any]:
    """Estimate environmental noise at coordinates.

    Returns a composite, multi-factor assessment.
    """

    key = _noise_cache_key(lat, lon)
    cached = get_cached(key)
    if isinstance(cached, dict) and not cached.get("error"):
        return cached

    factors = _compute_noise_factors(lat, lon)
    if not factors:
        return {"error": "No nearby road found"}

    score, score_parts = _compute_noise_score(factors)
    level = _score_to_noise_level(score)

    # Keep legacy field name used by older callers/tests.
    nearest_road_m = (
        factors.get("roads", {}).get("nearest_road_distance_m")
        if isinstance(factors.get("roads"), dict)
        else None
    )

    out: dict[str, Any] = {
        "noise_level": level,
        "noise_score": score,
        "distance_to_road_m": None if nearest_road_m is None else round(float(nearest_road_m), 2),
        "factors": factors,
        "score_breakdown": score_parts,
        "method": "Composite score from nearby roads, railways, airports, and landuse",
        "source": "OpenStreetMap",
        "data_sources": {
            "spatial": "Overpass API (OpenStreetMap)",
        },
    }

    set_cache(key, out)
    return out


def estimate_noise_from_address(address: str) -> dict[str, Any]:
    details = geocode_address_details(address)
    if not details:
        return {"error": "Address not found"}
    lat = _safe_float(details.get("lat"))
    lon = _safe_float(details.get("lon"))
    if lat is None or lon is None:
        return {"error": "Address not found"}
    out = estimate_noise(lat, lon)
    if isinstance(out, dict) and not out.get("error"):
        out = dict(out)
        out["address"] = str(address)
        out["coordinates"] = {"lat": lat, "lon": lon}
        out["place_name"] = _place_name_from_geocode(address, details)
        out.setdefault("data_sources", {})
        if isinstance(out["data_sources"], dict):
            out["data_sources"].update({"geocoding": "Nominatim (OpenStreetMap)"})
    return out


def estimate_noise_brief_from_address(address: str) -> str:
    """Return a compact summary for UI/CLI display."""

    result = estimate_noise_from_address(address)
    if not isinstance(result, dict) or result.get("error"):
        return f"Error: {result.get('error', 'Unable to estimate noise')}"

    place = str(result.get("place_name") or address).strip()
    level = str(result.get("noise_level") or "Unknown").strip()
    return f"Place:- {place}\nNoise Estimation:- {level}"


if __name__ == "__main__":
    address = input("Enter property address: ").strip()
    print(estimate_noise_brief_from_address(address))
