import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import asyncio
import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.import_transit_stops",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def import_transit_stops_task(self, lat: float, lng: float, radius_meters: int = 800):
    """
    Background Task: Import transit stops for a given location.
    Called during evaluation pipeline (Phase 7 - Location Intelligence stage).
    Retries up to 3 times with 60s delay if Overpass API fails.
    """
    try:
        from app.services.transit_service import save_transit_stops_to_db
        result = asyncio.get_event_loop().run_until_complete(
            save_transit_stops_to_db(lat, lng, radius_meters)
        )
        logger.info(f"Transit import complete: {result['inserted']} stops at ({lat},{lng})")
        return result
    except Exception as exc:
        logger.error(f"Transit import failed for ({lat},{lng}): {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="tasks.compute_transit_score",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def compute_transit_score_task(self, property_id: str, radius_meters: int = 800):
    """
    Background Task: Compute transit score for a property by ID.
    Called during evaluation pipeline after property coordinates are confirmed.
    """
    try:
        from app.services.transit_service import save_transit_score_for_property
        result = asyncio.get_event_loop().run_until_complete(
            save_transit_score_for_property(property_id, radius_meters)
        )
        logger.info(
            f"Transit score computed for property {property_id}: "
            f"score={result['transit_score']}, nearest={result['nearest_stop_meters']}m"
        )
        return result
    except ValueError as exc:
        logger.error(f"Property {property_id} not found: {exc}")
        return {"error": str(exc), "property_id": property_id}
    except Exception as exc:
        logger.error(f"Transit score failed for property {property_id}: {exc}")
        raise self.retry(exc=exc)