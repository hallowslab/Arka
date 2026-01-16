from celery import shared_task, current_app
from django.core.cache import cache
from datetime import datetime
import time

@shared_task
def worker_heartbeat():
    """
    Each worker periodically writes its heartbeat to cache.
    """
    worker_name = current_app.main or "unknown_worker"
    timestamp = datetime.utcnow().isoformat()
    cache.set(f"forj_worker_{worker_name}_heartbeat", timestamp, timeout=60)  # expire after 60s
    return {"worker": worker_name, "timestamp": timestamp}


@shared_task(bind=True)
def forj_healthcheck(self):
    time.sleep(1)
    return {
        "status": "ok",
        "worker": self.request.hostname,
    }
