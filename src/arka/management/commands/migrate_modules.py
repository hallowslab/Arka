from django.apps import apps
from django.core.management.base import BaseCommand
from django.core.management import call_command



class Command(BaseCommand):
    """
    Run migrations for each installed modular app.
    """

    help = "Run migrations for all installed modular apps."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Checking for modular apps..."))

        modular_apps = [
            app for app in apps.get_app_configs() if getattr(app, "is_modular", False)
        ]

        if not modular_apps:
            self.stdout.write("No modular apps found.")
            return

        for app_config in modular_apps:
            try:
                self.stdout.write(
                    f"Running migrations for modular app: {app_config.name} ({app_config.label})"
                )
                call_command("migrate", app_config.label, interactive=False)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to migrate {app_config.name}: {e}"))

