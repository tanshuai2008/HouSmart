import logging

import anyio

from app.services.geocode import geocode_address as geocode_address_sync

logger = logging.getLogger(__name__)


async def geocode_address(address: str) -> tuple[float, float]:
    """
    Async geocoding wrapper that reuses the shared sync geocoder implementation.

    Returns: (lat, lng)
    Raises: ValueError if address cannot be geocoded
    """
    try:
        result = await anyio.to_thread.run_sync(geocode_address_sync, address)
        if not result:
            raise ValueError(f"Address not found: '{address}'")

        lat, lng, _city, _state = result
        logger.info("Geocoded '%s' -> (%s, %s)", address, lat, lng)
        return lat, lng
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(f"Geocoding failed for '{address}': {exc}")
