from celery import Celery
from core.config import settings

_broker = settings.redis_url
_backend = settings.redis_url

celery_app = Celery(
    "mmm_platform",
    broker=_broker,
    backend=_backend,
    include=[
        "workers.robyn_worker",
        "workers.meridian_worker",
        "workers.pymcmarketing_worker",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
    # Run tasks inline (synchronously) when broker is memory://
    task_always_eager=_broker.startswith("memory"),
    task_eager_propagates=True,
)
