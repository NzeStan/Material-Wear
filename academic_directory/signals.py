# academic_directory/signals.py
"""
Signals for Academic Directory

Changes from original:
  - Graduation check uses update_fields=['is_active', 'notes'] to prevent
    triggering a recursive post_save loop.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Representative, SubmissionNotification

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Representative)
def create_submission_notification(sender, instance, created, **kwargs):
    """
    Create a SubmissionNotification when a new representative is saved for
    the first time, so admins see it in the dashboard.
    """
    if created:
        SubmissionNotification.objects.get_or_create(representative=instance)


@receiver(post_save, sender=Representative)
def check_graduation_status(sender, instance, created, **kwargs):
    """
    Auto-deactivate class reps who have graduated.

    Uses update_fields so that the subsequent save() call does NOT
    re-fire this signal (Django skips post_save for update_fields calls
    that do not match the handler's watched fields — but more importantly
    we guard with `instance.is_active` to avoid infinite recursion).
    """
    if created:
        return  # Newly created reps are handled separately; skip check

    if instance.role != 'CLASS_REP':
        return

    if not instance.is_active:
        return  # Already deactivated — nothing to do

    if instance.has_graduated:
        note = f"Auto-deactivated: Graduated in {instance.expected_graduation_year}"
        new_notes = f"{instance.notes}\n\n{note}" if instance.notes else note

        # Use update_fields to avoid triggering the signal recursively
        Representative.objects.filter(pk=instance.pk).update(
            is_active=False,
            notes=new_notes,
        )
        logger.info(
            f"signals: auto-deactivated class rep #{instance.pk} "
            f"({instance.display_name}) — graduated {instance.expected_graduation_year}"
        )