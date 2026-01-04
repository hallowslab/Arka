from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .dashboard.core import check_database, check_redis, check_rabbitmq

@login_required
def dashboard(request):
    context = {
        "checks": {
            "database": check_database(),
            "redis": check_redis(),
            "rabbitmq": check_rabbitmq(),
        }
    }
    return render(request, "dashboard.html", context)


@login_required
def profile(request):
    return render(request, "profile.html")
