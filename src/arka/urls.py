"""
URL configuration for arka project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .utils import app_exists
from .plugins.discovery import registry
from . import views


urlpatterns = [
    # Administration
    path("admin/", admin.site.urls),
    # Forj/celery
    path("FORJ/", include("forj.urls")),
    # Authetication
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    # Base site
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.profile, name="user_profile"),
    # Monitoring Details
    path("monitoring/database/", views.monitor_database, name="monitor_database"),
    path("monitoring/redis/", views.monitor_redis, name="monitor_redis"),
    path("monitoring/rabbitmq/", views.monitor_rabbitmq, name="monitor_rabbitmq"),
]

# Modular apps (Backward compatibility)
if app_exists("pymap"):
    urlpatterns.append(
        path("PYMAP/", include(("pymap.urls", "pymap"), namespace="pymap"))
    )
if app_exists("aera"):
    urlpatterns.append(path("AERA/", include(("aera.urls", "aera"), namespace="aera")))

# Dynamic Plugin URLs
for plugin in registry.get_enabled_plugins():
    url_info = plugin.get_urls()
    if url_info:
        url_module, namespace = url_info
        # Avoid double-including apps that are already hardcoded
        if namespace not in ["pymap", "aera"]:
            urlpatterns.append(
                path(
                    f"{plugin.name.upper()}/",
                    include((url_module, namespace), namespace=namespace),
                )
            )
