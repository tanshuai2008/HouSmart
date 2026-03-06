from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

from app.utils.errors import CrimeSafetyServiceError
from app.utils.logging import get_logger

load_dotenv()

logger = get_logger(__name__)


class FbiCrimeDataClient:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        http_session: Optional[requests.Session] = None,
        timeout: float = 120.0,
    ) -> None:
        self._api_key = api_key or os.getenv("FBI_API_KEY")
        self._base_url = base_url or os.getenv("FBI_API_BASE_URL", "https://api.usa.gov/crime/fbi/cde")
        self._http = http_session or requests.Session()
        self._timeout = timeout

    def fetch_summarized_data(
        self,
        *,
        ori: str,
        offense_code: str,
        from_month: str,
        to_month: str,
    ) -> Dict[str, Any]:
        if not self._api_key:
            raise CrimeSafetyServiceError("FBI_API_KEY is required")
        if not ori:
            raise CrimeSafetyServiceError("ORI is required for crime data fetch")
        if not offense_code:
            raise CrimeSafetyServiceError("Offense code is required for crime data fetch")
        endpoint = f"{self._base_url.rstrip('/')}/summarized/agency/{ori}/{offense_code}"
        params = {
            "from": from_month,
            "to": to_month,
            "API_KEY": self._api_key,
        }
        logger.info(
            "Fetching FBI summarized data ori=%s offense=%s from=%s to=%s",
            ori,
            offense_code,
            from_month,
            to_month,
        )
        try:
            response = self._http.get(endpoint, params=params, timeout=self._timeout)
            logger.info("FBI request URL: %s", response.url)
            logger.info("FBI response JSON: %s", response.json())  # Debug: print the full URL being requested
            response.raise_for_status()
        except requests.RequestException as exc:
            raise CrimeSafetyServiceError(f"FBI summarized request failed: {exc}") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise CrimeSafetyServiceError("FBI API returned non-JSON response") from exc
        required_keys = {"offenses", "populations", "tooltips", "cde_properties"}
        missing = [key for key in required_keys if key not in payload]
        if missing:
            raise CrimeSafetyServiceError(
                f"FBI summarized payload missing fields: {', '.join(missing)}"
            )
        return payload


def fetch_SummarizedCrimeData(ori: str, offense_code: str, from_date: str, to_date: str) -> Dict[str, Any]:
    client = FbiCrimeDataClient()
    return client.fetch_summarized_data(
        ori=ori,
        offense_code=offense_code,
        from_month=from_date,
        to_month=to_date,
    )


if __name__ == "__main__":
    fetch_SummarizedCrimeData(
        ori="VA0290500",
        offense_code="HOM",
        from_date="01-2025",
        to_date="12-2025",
    )


