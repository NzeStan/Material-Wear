"""
Celery Tasks for Background Processing

These tasks should be run periodically using Celery Beat.
"""

from celery import shared_task
from .models import Representative
from .utils.notifications import (
    send_daily_summary_email,
    process_pending_email_notifications
)


@shared_task
def check_graduation_statuses():
    """
    Check all class representatives for graduation status.
    
    Run daily to auto-deactivate graduated students.
    """
    class_reps = Representative.objects.filter(
        role='CLASS_REP',
        is_active=True
    )
    
    deactivated_count = 0
    for rep in class_reps:
        if rep.check_and_update_status():
            deactivated_count += 1
    
    return f"Deactivated {deactivated_count} graduated representatives"


@shared_task
def send_daily_summary():
    """
    Send daily summary email to admins.
    
    Run once per day (e.g., 9 AM).
    """
    count = send_daily_summary_email()
    return f"Sent daily summary to {count} recipients"


@shared_task
def process_email_notifications():
    """
    Process pending email notifications.
    
    Run every 5-10 minutes to batch notifications.
    """
    count = process_pending_email_notifications()
    return f"Processed {count} pending notifications"


@shared_task
def send_single_submission_email(representative_id):
    """
    Send email for a single new submission.
    
    Called asynchronously after submission.
    """
    from .utils.notifications import send_new_submission_email
    from .models import Representative
    
    try:
        rep = Representative.objects.get(id=representative_id)
        send_new_submission_email(rep)
        return f"Sent notification for {rep.display_name}"
    except Representative.DoesNotExist:
        return f"Representative {representative_id} not found"