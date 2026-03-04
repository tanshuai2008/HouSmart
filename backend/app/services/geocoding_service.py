import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


async def geocode_address(address: str) -> tuple[float, float]:
    """
    Convert a street address to (lat, lng) using OSM Nominatim.
    Free, no API key required.

    Returns: (lat, lng) tuple
    Raises: ValueError if address cannot be geocoded
    """
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 0,
    }
    headers = {
        "User-Agent": settings.HTTP_USER_AGENT,
        "Accept-Language": "en",
    }

    try:
        async with httpx.AsyncClient(
            timeout=settings.NOMINATIM_HTTP_TIMEOUT_SECONDS
        ) as client:
            response = await client.get(
                settings.NOMINATIM_URL,
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            results = response.json()

        if not results:
            raise ValueError(f"Address not found: '{address}'")

        lat = float(results[0]["lat"])
        lng = float(results[0]["lon"])
        logger.info(f"Geocoded '{address}' → ({lat}, {lng})")
        return lat, lng

    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Geocoding failed for '{address}': {e}")