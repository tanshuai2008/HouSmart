from __future__ import annotations

from typing import Any

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
TIMEOUT = 30

# Nominatim requires a descriptive User-Agent.
DEFAULT_HEADERS = {
    "User-Agent": "HouSmart/1.0 (contact: local-dev)",
    "Accept": "application/json",
}


def import_road_network(place: str) -> dict[str, Any]:
    """
    Fetch road network from OpenStreetMap using Overpass API.
    """

    place = (place or "").strip()
    if not place:
        return {"error": "Place is required"}

    def _run_overpass(query: str) -> dict[str, Any]:
        res = requests.post(
            OVERPASS_URL,
            data=query,
            headers=DEFAULT_HEADERS,
            timeout=TIMEOUT,
        )
        res.raise_for_status()
        return res.json()

    def _summarize(data: dict[str, Any], *, resolution: str) -> dict[str, Any]:
        elements = data.get("elements") or []
        ways = [e for e in elements if e.get("type") == "way"]
        nodes = [e for e in elements if e.get("type") == "node"]
        return {
            "place": place,
            "roads_count": len(ways),
            "nodes_count": len(nodes),
            "source": "OpenStreetMap (Overpass API)",
            "resolution": resolution,
        }

    # 1) Preferred: let Overpass resolve the place string to an area.
    # Works for inputs like "Seattle, Washington, USA".
    query_geocode_area = f"""
    [out:json][timeout:25];
    {{geocodeArea:{place}}}->.searchArea;
    (
      way["highway"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """

    try:
        data = _run_overpass(query_geocode_area)
        summary = _summarize(data, resolution="overpass-geocodeArea")
        if summary["roads_count"] > 0 or summary["nodes_count"] > 0:
            return summary
    except requests.RequestException:
        # Fall back to Nominatim resolution below.
        pass
    except ValueError:
        pass

    # 2) Fallback: use Nominatim to find an OSM object, then query Overpass.
    try:
        nom_res = requests.get(
            NOMINATIM_URL,
            params={"q": place, "format": "jsonv2", "limit": 1},
            headers=DEFAULT_HEADERS,
            timeout=TIMEOUT,
        )
        nom_res.raise_for_status()
        results = nom_res.json() or []
        if not results:
            return {"error": f"Place not found: {place}"}

        top = results[0]
        osm_type = (top.get("osm_type") or "").lower()  # node|way|relation
        osm_id_raw = top.get("osm_id")

        # Prefer area queries when possible; otherwise fall back to bbox.
        area_id: int | None = None
        if isinstance(osm_id_raw, int):
            if osm_type == "relation":
                area_id = 3_600_000_000 + osm_id_raw
            elif osm_type == "way":
                area_id = 2_400_000_000 + osm_id_raw

        if area_id is not None:
            query_area_id = f"""
            [out:json][timeout:25];
            area({area_id})->.searchArea;
            (
              way["highway"](area.searchArea);
            );
            out body;
            >;
            out skel qt;
            """
            data = _run_overpass(query_area_id)
            return _summarize(data, resolution="nominatim-area-id")

        # Bounding box fallback (Nominatim returns: [south, north, west, east]).
        bbox = top.get("boundingbox")
        if not (isinstance(bbox, list) and len(bbox) == 4):
            return {"error": f"Could not resolve a query area for: {place}"}

        south, north, west, east = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
        query_bbox = f"""
        [out:json][timeout:25];
        (
          way["highway"]({south},{west},{north},{east});
        );
        out body;
        >;
        out skel qt;
        """
        data = _run_overpass(query_bbox)
        return _summarize(data, resolution="nominatim-bbox")

    except requests.RequestException as e:
        return {"error": f"Network error: {e}"}
    except (ValueError, TypeError) as e:
        return {"error": f"Unexpected response parsing error: {e}"}


if __name__ == "__main__":
    place = input("Enter city or area: ").strip()
    result = import_road_network(place)
    print(result)