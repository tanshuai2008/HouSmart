import sys
import os

# Add backend/ to path so we can import from app.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "housmart",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "workers.tasks.transit_tasks",
        "workers.tasks.flood_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)