from django.http import HttpResponse
from django.core.cache import cache
from django.shortcuts import render
from celery import current_app

# Create your views here.

def index(request):
    return render(request, "forj_index.html")
