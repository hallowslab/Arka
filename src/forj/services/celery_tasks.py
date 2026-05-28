import logging
from importlib import import_module
from django.apps import apps
from django_celery_results.models import TaskResult
from django.db.models import Q
from forj.celery import app

logger = logging.getLogger(__name__)


def _get_known_task_id_map(user_tasks):
    """
    Recover task names for older result rows created before extended Celery
    result metadata was enabled.
    """
    task_id_map = {}

    if "pymap.tasks.run_imap_sync" in user_tasks:
        try:
            from pymap.models import MigrationTask

            for task_id in MigrationTask.objects.values_list("id", flat=True):
                task_id_map[str(task_id)] = "pymap.tasks.run_imap_sync"
        except Exception as e:
            logger.debug("Unable to build Pymap task result map: %s", e)

    return task_id_map


def _load_modular_task_modules():
    modular_labels = set()

    for app_config in apps.get_app_configs():
        if getattr(app_config, "is_modular", False):
            module_label = app_config.name.split(".")[-1]
            modular_labels.add(module_label)
            try:
                import_module(f"{app_config.name}.tasks")
            except ModuleNotFoundError as e:
                if e.name != f"{app_config.name}.tasks":
                    logger.debug("Unable to import %s.tasks: %s", app_config.name, e)
            except Exception as e:
                logger.debug("Unable to import %s.tasks: %s", app_config.name, e)

    return modular_labels


def get_celery_task_stats():
    """
    Return registered Celery tasks grouped by module with result-backend stats.
    """
    modular_labels = _load_modular_task_modules()
    all_tasks = sorted(app.tasks.keys())
    user_tasks = [
        task_name
        for task_name in all_tasks
        if task_name.split(".")[0] in modular_labels
    ]

    fallback_task_names = _get_known_task_id_map(user_tasks)
    task_stats = {
        task_name: {
            "total": 0,
            "success": 0,
            "failure": 0,
            "latest_status": None,
            "latest_done_at": None,
        }
        for task_name in user_tasks
    }
    recent_failures = []

    result_filter = Q(task_name__in=user_tasks)
    if fallback_task_names:
        result_filter |= Q(task_id__in=fallback_task_names.keys())

    result_rows = (
        TaskResult.objects.filter(result_filter)
        .order_by("-date_done")
        .values("task_id", "task_name", "status", "date_done", "result", "traceback")
    )

    for row in result_rows:
        task_name = row["task_name"] or fallback_task_names.get(row["task_id"])
        if task_name not in task_stats:
            continue

        task_stats[task_name]["total"] += 1
        if row["status"] == "SUCCESS":
            task_stats[task_name]["success"] += 1
        elif row["status"] == "FAILURE":
            task_stats[task_name]["failure"] += 1

        if task_stats[task_name]["latest_status"] is None:
            task_stats[task_name]["latest_status"] = row["status"]
            task_stats[task_name]["latest_done_at"] = row["date_done"]

        if row["status"] == "FAILURE" and len(recent_failures) < 5:
            recent_failures.append(
                {
                    "task_name": task_name,
                    "date_done": row["date_done"],
                    "result": row["result"],
                    "traceback": row["traceback"],
                }
            )

    modules_map = {}

    for task_name in user_tasks:
        parts = task_name.split(".")
        if len(parts) > 1:
            module_name = parts[0].upper()
        else:
            module_name = "OTHER"

        if module_name not in modules_map:
            modules_map[module_name] = {
                "name": module_name,
                "task_count": 0,
                "tasks": [],
                "totals": {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                },
            }

        stats = task_stats[task_name]

        modules_map[module_name]["tasks"].append({
            "name": task_name,
            "total": stats["total"],
            "success": stats["success"],
            "failure": stats["failure"],
            "latest_status": stats["latest_status"],
            "latest_done_at": stats["latest_done_at"],
        })
        modules_map[module_name]["task_count"] += 1
        modules_map[module_name]["totals"]["total"] += stats["total"]
        modules_map[module_name]["totals"]["success"] += stats["success"]
        modules_map[module_name]["totals"]["failure"] += stats["failure"]

    result = []
    for module in modules_map.values():
        module["tasks"].sort(key=lambda x: x["name"])
        result.append(module)

    result.sort(key=lambda x: x["name"])

    summary = {
        "modules": len(result),
        "registered_tasks": len(user_tasks),
        "total_results": sum(module["totals"]["total"] for module in result),
        "success": sum(module["totals"]["success"] for module in result),
        "failure": sum(module["totals"]["failure"] for module in result),
    }

    return {
        "summary": summary,
        "modules": result,
        "recent_failures": recent_failures,
    }
