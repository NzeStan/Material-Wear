# academic_directory/management/commands/send_academic_summary.py
"""
Management command: send_academic_summary

Sends a daily summary email to all staff admins listing new unverified
representative submissions from the past 24 hours.

Schedule daily via cron, e.g.:
  0 8 * * * /path/to/python manage.py send_academic_summary
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send daily academic directory summary email to admins (run daily via cron)"

    def handle(self, *args, **options):
        from academic_directory.tasks import trigger_daily_summary
        self.stdout.write("Queuing daily summary email...")
        trigger_daily_summary()
        self.stdout.write(self.style.SUCCESS("Daily summary email queued."))
