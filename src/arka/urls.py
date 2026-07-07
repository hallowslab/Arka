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
from django.conf import settings

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
]

# Modular apps URLs
if "pymap" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("PYMAP/", include(("pymap.urls", "pymap"), namespace="pymap")),
    ]
if "aera" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("AERA/", include(("aera.urls", "aera"), namespace="aera")),
    ]
if "dbtool" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("DBTOOL/", include(("dbtool.urls", "dbtool"), namespace="dbtool")),
    ]
if "nettools" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("NETTOOLS/", include(("nettools.urls", "nettools"), namespace="nettools")),
    ]
if "mimir" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("MIMIR/", include(("mimir.urls", "mimir"), namespace="mimir")),
    ]
if "mxr" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("MXRemastered/", include(("mxr.urls", "mxr"), namespace="mxr")),
    ]
if "bifrost" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("BIFROST/", include(("bifrost.urls", "bifrost"), namespace="bifrost")),
    ]
