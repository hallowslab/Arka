from django.urls import path
from . import views

app_name="forj"

urlpatterns = [
    path("", views.index, name="forj_home"),
]
