from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from app.models.crime import GeocodedLocation
from app.utils.errors import ExternalAPIError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class GeocodeClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        http_session: Optional[requests.Session] = None,
        timeout: float = 600.0,
        census_year: Optional[int] = None,
    ) -> None:
        self._api_key = api_key or os.getenv("GEOCODIO_API_KEY")
        self._base_url = base_url or os.getenv("GEOCODIO_BASE_URL", "https://api.geocod.io/v1.7/geocode")
        self._http = http_session or requests.Session()
        self._timeout = timeout
        self._census_year = census_year or (datetime.utcnow().year - 1)

    def geocode(self, address: str) -> GeocodedLocation:
        if not self._api_key:
            raise ExternalAPIError("GEOCODIO_API_KEY is required")

        params = {
            "q": address,
            "api_key": self._api_key,
            "fields": "census",
            "census_year": self._census_year,
        }
        log_params = {key: value for key, value in params.items() if key != "api_key"}
        logger.debug(
            "Geocodio request address='%s' url=%s params=%s timeout=%.1fs",
            address,
            self._base_url,
            log_params,
            self._timeout,
        )
        start = time.perf_counter()
        try:
            response = self._http.get(self._base_url, params=params, timeout=self._timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ExternalAPIError(f"Geocodio request failed: {exc}") from exc
        elapsed = time.perf_counter() - start
        logger.debug(
            "Geocodio response address='%s' status=%s elapsed=%.2fs",
            address,
            response.status_code,
            elapsed,
        )

        try:
            payload = response.json()
        except ValueError as exc:
            raise ExternalAPIError("Geocodio returned a non-JSON response") from exc
        logger.debug("Geocodio payload address='%s': %s", address, payload)

        results = payload.get("results")
        if not results:
            raise ExternalAPIError("Geocodio did not return any matches for the supplied address")

        best = results[0]
        fields = best.get("fields", {})
        census_fields = fields.get("census", {}) or {}
        place_fips = _extract_place_fips(census_fields)
        county_fips = _extract_county_fips(census_fields)
        census_population = _extract_population(census_fields)
        formatted_address = best.get("formatted_address") or address

        logger.debug(
            "Geocodio candidates=%s best='%s' place_fips=%s county_fips=%s",
            len(results),
            formatted_address,
            place_fips,
            county_fips,
        )

        if not place_fips and not county_fips:
            raise ExternalAPIError(
                f"Geocodio census data is missing place and county FIPS codes for '{address}' (census_year={self._census_year})"
            )

        return GeocodedLocation(
            normalized_address=str(formatted_address),
            place_fips=place_fips,
            county_fips=county_fips,
            census_population=census_population,
        )


def _as_digits(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _extract_place_fips(census_fields: Dict[str, Any]) -> Optional[str]:
    direct_value = _lookup_scalar(census_fields, ["place_fips", "placeFips", "PlaceFips"])
    if direct_value:
        return _as_digits(direct_value)
    place_block = _lookup_dict(census_fields, ["place", "Place"])
    if place_block:
        return _as_digits(place_block.get("fips") or place_block.get("FIPS"))
    return None


def _extract_county_fips(census_fields: Dict[str, Any]) -> Optional[str]:
    direct_value = _lookup_scalar(census_fields, ["county_fips", "countyFips", "CountyFips"])
    if direct_value:
        return _as_digits(direct_value)
    county_block = _lookup_dict(census_fields, ["county", "County"])
    if county_block:
        return _as_digits(county_block.get("fips") or county_block.get("FIPS"))
    return None


def _extract_population(census_fields: Dict[str, Any]) -> Optional[int]:
    population = _lookup_scalar(census_fields, ["population", "Population"])
    if isinstance(population, (int, float)):
        return int(population)
    if isinstance(population, str):
        digits = population.replace(",", "").strip()
        if digits.isdigit():
            return int(digits)
    return None


def _lookup_scalar(data: Any, keys: List[str]) -> Optional[Any]:
    stack = [data]
    visited = set()
    while stack:
        current = stack.pop()
        if not isinstance(current, dict):
            continue
        current_id = id(current)
        if current_id in visited:
            continue
        visited.add(current_id)
        for key in keys:
            if key in current:
                value = current[key]
                if isinstance(value, dict):
                    continue
                if value not in (None, ""):
                    return value
        for value in current.values():
            if isinstance(value, dict):
                stack.append(value)
    return None


def _lookup_dict(data: Any, keys: List[str]) -> Optional[Dict[str, Any]]:
    stack = [data]
    visited = set()
    while stack:
        current = stack.pop()
        if not isinstance(current, dict):
            continue
        current_id = id(current)
        if current_id in visited:
            continue
        visited.add(current_id)
        for key in keys:
            if key in current and isinstance(current[key], dict):
                return current[key]
        for value in current.values():
            if isinstance(value, dict):
                stack.append(value)
    return None
