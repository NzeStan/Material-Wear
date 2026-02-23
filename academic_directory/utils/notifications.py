# academic_directory/utils/notifications.py
"""
Notifications Utility

Thin wrappers that delegate to material/background_utils.py for all
async email delivery and to the SubmissionNotification model for
dashboard counters.

No direct send_mail calls here — all email goes through background_utils
so the request thread is never blocked.
"""
from typing import List, Optional
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# SUBMISSION NOTIFICATIONS (used from signals + views)
# ============================================================================


def send_new_submission_email(representative, admin_emails: Optional[List[str]] = None):
    """
    Queue an email notification to admins about a new representative submission.

    Args:
        representative: Representative instance
        admin_emails: Unused — kept for backward-compat signature.
                      Recipients are always resolved from staff users in background_utils.

    Returns:
        None (async — fire and forget)
    """
    from material.background_utils import send_new_submission_email_async

    send_new_submission_email_async(representative.id)


def send_bulk_verification_email(representatives: List, verifier):
    """
    Queue a bulk-verification notification email to admins.

    Args:
        representatives: List of Representative instances
        verifier: User instance who performed the verification
    """
    from material.background_utils import send_bulk_verification_email_async

    ids = [r.id for r in representatives]
    send_bulk_verification_email_async(ids, verifier.id)


def send_daily_summary_email():
    """
    Queue daily summary email to admins (called from management command).
    Returns immediately — delivery happens in a daemon thread.
    """
    from material.background_utils import send_daily_summary_email_async

    send_daily_summary_email_async()


def process_pending_email_notifications():
    """
    Queue batch notification for all pending (un-emailed) SubmissionNotifications.
    Called from management command every 5-10 minutes.
    Returns immediately — delivery happens in a daemon thread.
    """
    from material.background_utils import process_pending_notifications_async

    process_pending_notifications_async()


# ============================================================================
# DASHBOARD COUNTER HELPERS
# ============================================================================


def get_unread_notification_count() -> int:
    """Return count of unread submission notifications for dashboard."""
    from academic_directory.models import SubmissionNotification

    return SubmissionNotification.get_unread_count()


def mark_notification_as_read(notification_id: int, user=None) -> bool:
    """
    Mark a specific notification as read.

    Args:
        notification_id: PK of SubmissionNotification
        user: Optional User who read it

    Returns:
        bool: True if found and updated, False otherwise
    """
    from academic_directory.models import SubmissionNotification

    try:
        notification = SubmissionNotification.objects.get(id=notification_id)
        notification.mark_as_read(user)
        return True
    except SubmissionNotification.DoesNotExist:
        return False


def mark_all_notifications_as_read(user=None) -> int:
    """
    Mark all unread notifications as read.

    Returns:
        int: Number of notifications updated
    """
    from academic_directory.models import SubmissionNotification
    from django.utils import timezone

    unread = SubmissionNotification.objects.filter(is_read=False)
    count = unread.count()
    unread.update(is_read=True, read_at=timezone.now(), read_by=user)
    return count


def create_submission_notification(representative):
    """
    Create (or get) a SubmissionNotification for a new representative.

    Args:
        representative: Representative instance

    Returns:
        SubmissionNotification instance
    """
    from academic_directory.models import SubmissionNotification

    notification, _ = SubmissionNotification.objects.get_or_create(
        representative=representative
    )
    return notification


# ============================================================================
# TEMPLATE CONTEXT HELPER
# ============================================================================


def get_representative_email_context(representative) -> dict:
    """
    Build a standardised context dict for representative email templates.

    Args:
        representative: Representative instance

    Returns:
        dict: Template context
    """
    context = {
        "representative": representative,
        "display_name": representative.display_name,
        "full_name": representative.full_name,
        "phone_number": representative.phone_number,
        "email": representative.email,
        "university": representative.university.name,
        "faculty": representative.faculty.name,
        "department": representative.department.name,
        "role": representative.get_role_display(),
        "verification_status": representative.get_verification_status_display(),
        "created_at": representative.created_at,
        "admin_url": (
            f"{settings.SITE_URL}/admin/academic_directory/representative/"
            f"{representative.id}/change/"
        ),
        "company_name": getattr(settings, "COMPANY_NAME", "Material_Wear"),
        "primary_color": "#064E3B",
        "accent_color": "#F59E0B",
    }

    if representative.role == "CLASS_REP":
        context.update(
            {
                "current_level": representative.current_level_display,
                "entry_year": representative.entry_year,
                "expected_graduation_year": representative.expected_graduation_year,
                "is_final_year": representative.is_final_year,
            }
        )
    else:
        context.update({"tenure_start_year": representative.tenure_start_year})

    return context
