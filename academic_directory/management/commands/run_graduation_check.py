# academic_directory/management/commands/run_graduation_check.py
"""
Management command: run_graduation_check

Auto-deactivates class representatives who have graduated.
Schedule daily via cron, e.g.:
  0 1 * * * /path/to/python manage.py run_graduation_check
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Auto-deactivate graduated class representatives (run daily via cron)"

    def handle(self, *args, **options):
        from academic_directory.tasks import trigger_graduation_check
        self.stdout.write("Scheduling graduation check via django-background-tasks...")
        trigger_graduation_check()
        self.stdout.write(self.style.SUCCESS("Graduation check queued successfully."))
