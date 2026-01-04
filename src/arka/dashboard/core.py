from django.db import connections
from django.db.utils import OperationalError
from django.conf import settings
from kombu import Connection
from kombu.exceptions import OperationalError as KombuOperationalError
import redis

from arka.utils import build_broker_url

def check_database():
    try:
        db_conn = connections["default"]
        db_conn.cursor()
        return {
            "status": "ok",
            "message": "Database connection successful",
        }
    except OperationalError as exc:
        return {
            "status": "error",
            "message": str(exc),
        }

def check_redis():
    try:
        # Fetch default cache backend
        cache_config = settings.CACHES.get('default', {})

        # Only support Redis backend
        if 'redis' not in cache_config.get('BACKEND', '').lower():
            return {
                "status": "warning",
                "message": "Default cache backend is not Redis",
            }

        # Extract host, port, db from location string
        location = cache_config.get('LOCATION', None)
        if location is None:
            raise ValueError("location is None")
        r = redis.from_url(location, socket_connect_timeout=2)
        r.ping()
        return {
            "status": "ok",
            "message": "Redis connection successful",
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
        return {
            "status": "ok",
            "message": "RabbitMQ connection successful",
        }
    except KombuOperationalError as exc:
        return {
            "status": "error",
            "message": str(exc),
        }