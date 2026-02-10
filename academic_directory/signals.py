"""Signals for Academic Directory"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Representative, SubmissionNotification


@receiver(post_save, sender=Representative)
def create_submission_notification(sender, instance, created, **kwargs):
    """
    Create submission notification when a new representative is created.
    
    This allows admins to track new submissions in the dashboard.
    """
    if created:
        SubmissionNotification.objects.get_or_create(representative=instance)


@receiver(post_save, sender=Representative)
def check_graduation_status(sender, instance, created, **kwargs):
    """
    Check if representative should be auto-deactivated due to graduation.
    
    This runs on every save to catch status changes.
    """
    if not created and instance.role == 'CLASS_REP':
        instance.check_and_update_status()