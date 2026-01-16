from celery import shared_task
from django.core.cache import caches
from django.utils import timezone

from arka.dashboard.core import check_database, check_redis, check_rabbitmq


@shared_task
def perform_system_checks():
    """
    Periodic task to run system health checks and cache the results.
    Stores result in default cache under key 'arka_system_status'.
    """
    results = {
        "timestamp": timezone.now().isoformat(),
        "checks": {
            "database": check_database(),
            "redis": check_redis(),
            "rabbitmq": check_rabbitmq(),
        },
    }

    # Store in Redis (default cache) with a long timeout (e.g., 1 hour)
    # The task runs frequently enough to keep this fresh
    cache = caches["default"]
    cache.set("arka_system_status", results, timeout=3600)

    return results
