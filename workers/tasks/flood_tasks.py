import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import asyncio
import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.import_flood_zone",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def import_flood_zone_task(self, lat: float, lng: float):
    """
    Background Task: Import FEMA flood zone for a given lat/lng.
    Called during evaluation pipeline (Phase 7 - Risk & Scoring stage).
    Falls back to geographic mock automatically if FEMA unreachable.
    """
    try:
        from app.services.flood_service import save_flood_zone_to_db
        result = asyncio.get_event_loop().run_until_complete(
            save_flood_zone_to_db(lat, lng)
        )
        logger.info(
            f"Flood zone imported for ({lat},{lng}): "
            f"zone={result['fld_zone']}, score={result['flood_score']}"
        )
        return result
    except Exception as exc:
        logger.error(f"Flood import failed for ({lat},{lng}): {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    name="tasks.check_property_flood",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def check_property_flood_task(self, property_id: str):
    """
    Background Task: Check flood zone for a property by ID.
    Returns in_flood_zone flag used by the scoring engine.
    """
    try:
        from app.services.flood_service import check_flood_for_property
        result = asyncio.get_event_loop().run_until_complete(
            check_flood_for_property(property_id)
        )
        logger.info(
            f"Flood check complete for property {property_id}: "
            f"zone={result['fld_zone']}, in_flood_zone={result['in_flood_zone']}"
        )
        return result
    except ValueError as exc:
        logger.error(f"Property {property_id} not found: {exc}")
        return {"error": str(exc), "property_id": property_id}
    except Exception as exc:
        logger.error(f"Flood check failed for property {property_id}: {exc}")
        raise self.retry(exc=exc)