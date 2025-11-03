from celery import Celery
from app.config import settings
from app.tasks.celery_config import CELERY_BEAT_SCHEDULE

celery_app = Celery(
    "tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
celery_app.autodiscover_tasks(["app.tasks"])
