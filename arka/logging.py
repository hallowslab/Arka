# Mostly to help keep settings.py cleaner
import os
from pathlib import Path

# Logging
# https://docs.djangoproject.com/en/5.2/topics/logging/
def load_logging_defaults(logdir: str):
    defaults = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "custom_formatter": {
                "format": "%(asctime)s - %(levelname)s >>> %(name)s: %(message)s",
                "datefmt": "%d/%m/%Y %I:%M:%S %p",
            },
            "verbose": {
                "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
                "datefmt": "%d/%m/%Y %I:%M:%S %p",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "custom_formatter",
            },
            "arka_file": {
                "level": os.getenv("ARKA_LOG_LEVEL", "WARNING"),
                "class": "logging.FileHandler",
                "filename": str(Path(logdir, "arka.log").resolve()),
                "formatter": "verbose",
            },
            "forj_file": {
                "level": os.getenv("FORJ_LOG_LEVEL", "WARNING"),
                "class": "logging.FileHandler",
                "filename": str(Path(logdir, "forj.log").resolve()),
                "formatter": "verbose",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "WARNING",
        },
        "loggers": {
            "django": {
                "handlers": ["console", "arka_file"],
                "level": os.getenv("ARKA_LOG_LEVEL", "WARNING"),
                "propagate": True,
            },
            "django.request": {
                "handlers": ["console", "arka_file"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }
    return defaults
