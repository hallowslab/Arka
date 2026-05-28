from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .services.celery_status import get_celery_status

from .services.celery_tasks import get_celery_task_stats

# Create your views here.


@login_required
def index(request):
    celery_task_stats = get_celery_task_stats()
    celery_status = get_celery_status()

    context = {
        "task_summary": celery_task_stats["summary"],
        "task_modules": celery_task_stats["modules"],
        "recent_failures": celery_task_stats["recent_failures"],
        "broker": celery_status,
    }
    return render(request, "forj_index.html", context)
