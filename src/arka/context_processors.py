from django.apps import apps
from importlib import import_module
from ._version import __version__ as PROJECT_VERSION


def project_version(request):
    return {"PROJECT_VERSION": PROJECT_VERSION}


def active_app_version(request):
    match = getattr(request, "resolver_match", None)
    namespace = getattr(match, "namespace", None)

    if not namespace:
        return {
            "APP_NAME": None,
            "APP_VERSION": PROJECT_VERSION,
        }

    try:
        app_config = apps.get_app_config(namespace)
        module = import_module(f"{app_config.name}._version")

        return {
            "APP_NAME": namespace,
            "APP_VERSION": module.__version__,
        }

    except Exception:
        return {
            "APP_NAME": namespace,
            "APP_VERSION": PROJECT_VERSION,
        }


def modular_apps(request):
    apps_list = [
        app for app in apps.get_app_configs() if getattr(app, "is_modular", False)
    ]
    print(f"APPS LIST: {apps_list}")
    return {"modular_apps": apps_list}
