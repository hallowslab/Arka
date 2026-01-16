from django.core.cache import caches
from datetime import datetime

def get_worker_presence():
    """
    Reads cached heartbeats to determine which workers are alive.
    Uses SCAN via the default Django Redis cache connection.
    Production-safe.
    """
    alive_workers = []

    # Get the default cache
    cache_backend = caches["default"]  # type: RedisCache

    # The raw redis client is exposed as `cache_backend.client.get_client()`
    redis_client = cache_backend.client.get_client(write=True)

    # SCAN safely in production
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match="forj_worker_*_heartbeat", count=100)
        for key in keys:
            ts = redis_client.get(key)
            if ts:
                # key is already bytes, decode if necessary
                if isinstance(key, bytes):
                    key = key.decode("utf-8")
                worker_name = key.replace("forj_worker_", "").replace("_heartbeat", "")
                alive_workers.append(worker_name)
        if cursor == 0:
            break

    if not alive_workers:
        return {
            "type": "status",
            "side_effect": False,
            "description": "FORJ worker presence (observed via heartbeat). No workers have reported in yet.",
            "status": "unknown",
            "count": 0,
            "hosts": [],
        }

    return {
        "type": "status",
        "side_effect": False,
        "description": "FORJ worker presence (observed via heartbeat).",
        "status": "ok",
        "count": len(alive_workers),
        "hosts": sorted(alive_workers),
    }