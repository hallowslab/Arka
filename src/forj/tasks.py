from celery import shared_task
from django.core.cache import cache
from datetime import datetime


@shared_task(bind=True)
def worker_heartbeat(self):
    """
    Each worker periodically writes its heartbeat to cache.
    """
    worker_name = self.request.hostname or "unknown_worker"
    timestamp = datetime.utcnow().isoformat()
    cache.set(
        f"forj_worker_{worker_name}_heartbeat", timestamp, timeout=60
    )  # expire after 60s
    return {"worker": worker_name, "timestamp": timestamp}
