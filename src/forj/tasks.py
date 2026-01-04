from celery import shared_task
import time

@shared_task(bind=True)
def forj_healthcheck(self):
    time.sleep(1)
    return {
        "status": "ok",
        "worker": self.request.hostname,
    }
