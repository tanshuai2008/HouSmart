from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "housmart",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.transit_tasks",
        "app.workers.tasks.flood_tasks",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)