from django.apps import AppConfig


class PluginsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "arka.plugins"
    label = "arka_plugins"

    def ready(self) -> None:
        from .discovery import registry

        registry.discover()
