import os
import signal
import psutil
import socket
from django.core.management.base import BaseCommand
from django.utils import timezone
from pymap.models import MigrationTask


class Command(BaseCommand):
    help = "Clean up orphaned imapsync processes and update database status."

    def handle(self, *args, **options):
        current_host = socket.gethostname()
        self.stdout.write(f"Cleaning up orphaned tasks for host: {current_host}")

        # Find tasks marked as RUNNING on this host
        tasks = MigrationTask.objects.filter(
            status="RUNNING", worker_hostname=current_host
        )

        for task in tasks:
            if not task.pid:
                self.stdout.write(
                    self.style.WARNING(
                        f"Task {task.id} has no PID record. Marking as FAILED."
                    )
                )
                task.status = "FAILED"
                task.end_time = timezone.now()
                task.save()
                continue

            try:
                # Check if process exists
                process = psutil.Process(task.pid)

                # Verify it's actually an imapsync or perl process (optional but safer)
                # For now, we trust the PID + hostname combination
                if process.is_running():
                    self.stdout.write(
                        f"Task {task.id} (PID {task.pid}) is still running."
                    )
                else:
                    raise psutil.NoSuchProcess(task.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.stdout.write(
                    self.style.WARNING(
                        f"Task {task.id} (PID {task.pid}) not found. Marking as FAILED."
                    )
                )
                task.status = "FAILED"
                task.end_time = timezone.now()
                task.save()
