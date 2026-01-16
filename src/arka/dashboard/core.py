from django.db import connections
from django.conf import settings
from django.core.cache import cache
from kombu import Connection
from kombu.exceptions import OperationalError as KombuOperationalError
import os
import redis


def get_worker_presence():
    """
    Reads cached heartbeats to determine which workers are alive.
    Uses SCAN via a direct Redis connection from settings to find keys,
    but uses Django's cache API to retrieve values for safe unpickling.
    """
    workers = []

    try:
        cache_config = settings.CACHES.get("default", {})
        location = cache_config.get("LOCATION")
        if not location:
            return {
                "status": "error",
                "message": "Cache LOCATION not configured",
                "workers": [],
            }

        redis_client = redis.from_url(location)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Redis connection failed: {str(e)}",
            "workers": [],
        }

    cursor = 0
    while True:
        # Use wildcard at start to catch Django cache prefixes like ":1:"
        cursor, keys = redis_client.scan(
            cursor=cursor, match="*forj_worker_*_heartbeat", count=100
        )
        for key in keys:
            if isinstance(key, bytes):
                key = key.decode("utf-8")

            # Remove prefix (e.g., ":1:") to get the key as Django expects it
            clean_key = key.split(":")[-1] if ":" in key else key

            # Use Django's cache.get() to handle unpickling/deserialization
            ts = cache.get(clean_key)

            if ts:
                # If it's already a string or datetime, we're good
                if not isinstance(ts, str):
                    ts = str(ts)

                worker_name = clean_key.replace("forj_worker_", "").replace(
                    "_heartbeat", ""
                )

                workers.append(
                    {"name": worker_name, "last_heartbeat": ts, "status": "online"}
                )
        if cursor == 0:
            break

    return {
        "status": "ok" if workers else "unknown",
        "count": len(workers),
        "workers": sorted(workers, key=lambda x: x["name"]),
    }


def check_database():
    try:
        db_conn = connections["default"]
        # Basic connectivity
        db_conn.cursor()

        stats = {"vendor": db_conn.vendor}
        if db_conn.vendor == "sqlite":
            # Table count
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
                stats["table_count"] = cursor.fetchone()[0]

            # File size
            db_path = settings.DATABASES["default"]["NAME"]
            if os.path.exists(db_path):
                stats["size_bytes"] = os.path.getsize(db_path)

        elif db_conn.vendor == "postgresql":
            with db_conn.cursor() as cursor:
                # Table count
                cursor.execute(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
                )
                stats["table_count"] = cursor.fetchone()[0]

                # Database size
                db_name = settings.DATABASES["default"]["NAME"]
                cursor.execute(f"SELECT pg_database_size('{db_name}')")
                stats["size_bytes"] = cursor.fetchone()[0]

                # Active connections
                cursor.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = %s",
                    [db_name],
                )
                stats["active_connections"] = cursor.fetchone()[0]

        return {
            "status": "ok",
            "message": "Database connection successful",
            "stats": stats,
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def check_redis():
    try:
        # Fetch default cache backend
        cache_config = settings.CACHES.get("default", {})

        # Only support Redis backend
        if "redis" not in cache_config.get("BACKEND", "").lower():
            return {
                "status": "warning",
                "message": "Default cache backend is not Redis",
            }

        # Extract host, port, db from location string
        location = cache_config.get("LOCATION", None)
        if location is None:
            raise ValueError("location is None")
        r = redis.from_url(location, socket_connect_timeout=2)
        r.ping()

        # Gather stats
        info = r.info()
        stats = {
            "version": info.get("redis_version"),
            "memory_used_human": info.get("used_memory_human"),
            "memory_rss_human": info.get("used_memory_rss_human"),
            "memory_fragmentation_ratio": info.get("mem_fragmentation_ratio"),
            "clients": info.get("connected_clients"),
            "uptime_days": info.get("uptime_in_days"),
            "uptime_in_seconds": info.get("uptime_in_seconds"),
            "ops_per_sec": info.get("instantaneous_ops_per_sec"),
            "commands_processed": info.get("total_commands_processed"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "keys_count": (
                info.get("db0", {}).get("keys", 0)
                if "db0" in info
                else sum(
                    d.get("keys", 0) for k, d in info.items() if k.startswith("db")
                )
            ),
        }

        return {
            "status": "ok",
            "message": "Redis connection successful",
            "stats": stats,
        }
    except (redis.ConnectionError, ValueError) as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


def check_rabbitmq():
    broker_url = getattr(settings, "CELERY_BROKER_URL", None)

    if not broker_url:
        return {
            "status": "warning",
            "message": "RabbitMQ broker URL not configured",
        }

    try:
        with Connection(broker_url, connect_timeout=2) as conn:
            conn.ensure_connection(max_retries=1)

        # Check workers
        worker_info = get_worker_presence()
        worker_count = worker_info.get("count", 0)

        stats = {
            "workers_active": worker_count,
            "worker_details": worker_info.get("workers", []),
        }

        if worker_count > 0:
            return {
                "status": "ok",
                "message": f"RabbitMQ successful. {worker_count} workers active.",
                "stats": stats,
            }
        else:
            return {
                "status": "warning",
                "message": "Broker connected, but no active workers found.",
                "stats": stats,
            }

    except KombuOperationalError as exc:
        return {
            "status": "error",
            "message": str(exc),
        }
