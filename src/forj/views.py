from django.http import HttpResponse
from django.core.cache import cache
from django.shortcuts import render
from celery import current_app

# Create your views here.

from .tasks import forj_healthcheck
from .utils import get_worker_presence

def checks(request):
    checks_result = {}

    # ---- Manual test task (has side effects) ----
    task = None
    if request.method == "POST":
        task = forj_healthcheck.delay()
    checks_result["manual_task_dispatch"] = {
        "type": "action",
        "side_effect": True,
        "description": "Dispatch a test task to verify task execution.",
        "task_id": task.id if task else None,
    }

    # ---- Worker presence (no side effects, read from cache) ----
    checks_result["worker_presence"] = get_worker_presence()

    return render(request, "forj_checks.html", {"checks": checks_result})


def index(request):
    return render(request, "forj_index.html")
