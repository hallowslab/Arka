from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.cache import caches

@login_required
def dashboard(request):
    cache = caches["default"]
    # Provide default structure if cache is empty
    default_results = {
        "timestamp": None,
        "checks": {
            "database": {"status": "unknown", "message": "Pending check..."},
            "redis": {"status": "unknown", "message": "Pending check..."},
            "rabbitmq": {"status": "unknown", "message": "Pending check..."},
        }
    }
    
    results = cache.get("arka_system_status", default_results)
    
    context = {
        "checks": results.get("checks", default_results["checks"]),
        "timestamp": results.get("timestamp"),
    }
    return render(request, "dashboard.html", context)


@login_required
def monitor_database(request):
    cache = caches["default"]
    results = cache.get("arka_system_status", {})
    db_stats = results.get("checks", {}).get("database", {})
    context = {
        "database": db_stats,
        "timestamp": results.get("timestamp"),
    }
    return render(request, "monitoring/database.html", context)


@login_required
def monitor_redis(request):
    cache = caches["default"]
    results = cache.get("arka_system_status", {})
    redis_stats = results.get("checks", {}).get("redis", {})
    context = {
        "redis": redis_stats,
        "timestamp": results.get("timestamp"),
    }
    return render(request, "monitoring/redis.html", context)


@login_required
def monitor_rabbitmq(request):
    cache = caches["default"]
    results = cache.get("arka_system_status", {})
    rabbit_stats = results.get("checks", {}).get("rabbitmq", {})
    context = {
        "rabbitmq": rabbit_stats,
        "timestamp": results.get("timestamp"),
    }
    return render(request, "monitoring/rabbitmq.html", context)


@login_required
def profile(request):
    return render(request, "profile.html")
