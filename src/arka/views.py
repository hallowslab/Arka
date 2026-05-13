from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request):
    modular_stats = []
    for app_config in apps.get_app_configs():
        if getattr(app_config, "is_modular", False) and hasattr(app_config, "get_dashboard_stats"):
            modular_stats.append({
                "name": app_config.verbose_name,
                "stats": app_config.get_dashboard_stats()
            })

    return render(request, "dashboard.html", {"modular_stats": modular_stats})


@login_required
def profile(request):
    return render(request, "profile.html")
