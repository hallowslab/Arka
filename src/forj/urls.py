from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="forj_home"),
]
