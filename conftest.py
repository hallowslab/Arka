"""Root conftest — configures Django before any app tests are collected."""

import importlib
import os
import sys
from pathlib import Path

import django

# Ensure src/ is importable for modular_apps.*
_root = Path(__file__).resolve().parent
_src = str(_root / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "arka.settings")

# Ensure the log directory exists so Django's logging config doesn't fail
_logdir = str(_root / "ARKA_LOGS")
os.environ["ARKA_LOGDIR"] = _logdir
os.makedirs(_logdir, exist_ok=True)

# Filter ENABLED_APPS to only apps that are actually installed.
# This prevents Django from failing on missing modules when running
# tests for a subset of apps.
_raw = os.environ.get("ENABLED_APPS", "")
if _raw:
    _all_apps = [a.strip() for a in _raw.split(",") if a.strip()]
    _importable = []
    for _app in _all_apps:
        try:
            importlib.import_module(_app.lower())
            _importable.append(_app)
        except ImportError:
            pass
    os.environ["ENABLED_APPS"] = ",".join(_importable)

django.setup()
