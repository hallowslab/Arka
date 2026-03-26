from django.core.management.base import BaseCommand
from django.core.management import call_command
from arka.plugins.discovery import registry


class Command(BaseCommand):
    """
    Run migrations for each enabled modular plugin based on its AppConfig.
    """

    help = "Run migrations for all enabled modular plugins."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Checking for enabled modular plugins..."))

        # Ensure discovery has run (it usually runs in AppConfig.ready)
        registry.discover()

        enabled_plugins = registry.get_enabled_plugins()

        if not enabled_plugins:
            self.stdout.write("No enabled plugins found.")
            return

        for plugin in enabled_plugins:
            self.stdout.write(f"Running migrations for plugin: {plugin.name}")
            try:
                # Get the app label from django_app (e.g., 'pymap.apps.PymapConfig' -> 'pymap')
                # This assumes the app is already in INSTALLED_APPS, which is handled in settings.py
                app_label = plugin.django_app.split(".")[0]

                self.stdout.write(f"Calling migrate for app: {app_label}")
                call_command("migrate", app_label, interactive=False)
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully migrated {plugin.name}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to migrate {plugin.name}: {e}")
                )
