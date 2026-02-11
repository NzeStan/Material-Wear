# academic_directory/management/commands/process_academic_notifications.py
"""
Management command: process_academic_notifications

Batches all pending (un-emailed) SubmissionNotifications into a single
email to staff admins.

Schedule every 5-10 minutes via cron, e.g.:
  */10 * * * * /path/to/python manage.py process_academic_notifications
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Batch-process pending academic submission notifications (run every ~10 min via cron)"

    def handle(self, *args, **options):
        from academic_directory.tasks import trigger_process_notifications
        self.stdout.write("Processing pending submission notifications...")
        trigger_process_notifications()
        self.stdout.write(self.style.SUCCESS("Notification batch queued."))
