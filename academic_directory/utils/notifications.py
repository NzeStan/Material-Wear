"""
Notifications Utility

Handles email notifications and dashboard counters for new submissions.
"""

from typing import List, Optional
from django.core.mail import send_mail, send_mass_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model

User = get_user_model()


def send_new_submission_email(representative, admin_emails: Optional[List[str]] = None):
    """
    Send email notification to admins about a new representative submission.
    
    Args:
        representative: Representative instance
        admin_emails: Optional list of admin emails (defaults to all staff users)
    
    Returns:
        int: Number of successfully delivered messages
    """
    if not admin_emails:
        # Get all staff user emails
        admin_emails = list(
            User.objects.filter(is_staff=True, is_active=True)
            .values_list('email', flat=True)
        )
    
    if not admin_emails:
        return 0
    
    # Prepare email context
    context = {
        'representative': representative,
        'university': representative.university.name,
        'faculty': representative.faculty.name,
        'department': representative.department.name,
        'role': representative.get_role_display(),
        'display_name': representative.display_name,
        'phone_number': representative.phone_number,
        'current_level': representative.current_level_display if representative.role == 'CLASS_REP' else None,
        'admin_url': f"{settings.SITE_URL}/admin/academic_directory/representative/{representative.id}/change/",
    }
    
    # Render email template
    subject = f"New Representative Submission: {representative.display_name}"
    html_message = render_to_string('academic_directory/emails/new_submission.html', context)
    plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        sent = send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
        
        # Mark notification as emailed
        if hasattr(representative, 'notification'):
            representative.notification.mark_as_emailed()
        
        return sent
    except Exception as e:
        # Log error but don't crash
        print(f"Error sending new submission email: {e}")
        return 0


def send_bulk_verification_email(representatives: List, verifier):
    """
    Send email notification about bulk verification action.
    
    Args:
        representatives: List of Representative instances that were verified
        verifier: User instance who performed the verification
    
    Returns:
        int: Number of successfully delivered messages
    """
    if not representatives:
        return 0
    
    # Get admin emails
    admin_emails = list(
        User.objects.filter(is_staff=True, is_active=True)
        .values_list('email', flat=True)
    )
    
    if not admin_emails:
        return 0
    
    # Prepare email context
    context = {
        'representatives': representatives,
        'count': len(representatives),
        'verifier': verifier.get_full_name() or verifier.username,
        'site_url': settings.SITE_URL,
    }
    
    # Render email template
    subject = f"Bulk Verification: {len(representatives)} representatives verified"
    html_message = render_to_string('academic_directory/emails/bulk_verification.html', context)
    plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        return send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending bulk verification email: {e}")
        return 0


def send_daily_summary_email():
    """
    Send daily summary email to admins about new unverified submissions.
    
    This should be called via a scheduled task (e.g., Celery beat).
    
    Returns:
        int: Number of successfully delivered messages
    """
    from ..models import Representative, SubmissionNotification
    from datetime import timedelta
    from django.utils import timezone
    
    # Get unverified submissions from last 24 hours
    yesterday = timezone.now() - timedelta(days=1)
    new_submissions = Representative.objects.filter(
        verification_status='UNVERIFIED',
        created_at__gte=yesterday
    ).select_related('department__faculty__university')
    
    if not new_submissions.exists():
        return 0
    
    # Get admin emails
    admin_emails = list(
        User.objects.filter(is_staff=True, is_active=True)
        .values_list('email', flat=True)
    )
    
    if not admin_emails:
        return 0
    
    # Prepare email context
    context = {
        'submissions': new_submissions,
        'count': new_submissions.count(),
        'unread_count': SubmissionNotification.get_unread_count(),
        'site_url': settings.SITE_URL,
    }
    
    # Render email template
    subject = f"Daily Summary: {new_submissions.count()} new representative submissions"
    html_message = render_to_string('academic_directory/emails/daily_summary.html', context)
    plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        return send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending daily summary email: {e}")
        return 0


def get_unread_notification_count() -> int:
    """
    Get count of unread submission notifications.
    
    Used for dashboard counter.
    
    Returns:
        int: Number of unread notifications
    """
    from ..models import SubmissionNotification
    return SubmissionNotification.get_unread_count()


def mark_notification_as_read(notification_id: int, user=None):
    """
    Mark a specific notification as read.
    
    Args:
        notification_id: ID of SubmissionNotification
        user: Optional User instance who read it
    
    Returns:
        bool: True if successful, False otherwise
    """
    from ..models import SubmissionNotification
    
    try:
        notification = SubmissionNotification.objects.get(id=notification_id)
        notification.mark_as_read(user)
        return True
    except SubmissionNotification.DoesNotExist:
        return False


def mark_all_notifications_as_read(user=None):
    """
    Mark all unread notifications as read.
    
    Args:
        user: Optional User instance who read them
    
    Returns:
        int: Number of notifications marked as read
    """
    from ..models import SubmissionNotification
    from django.utils import timezone
    
    unread = SubmissionNotification.objects.filter(is_read=False)
    count = unread.count()
    
    unread.update(
        is_read=True,
        read_at=timezone.now(),
        read_by=user
    )
    
    return count


def create_submission_notification(representative):
    """
    Create a notification for a new representative submission.
    
    Args:
        representative: Representative instance
    
    Returns:
        SubmissionNotification instance
    """
    from ..models import SubmissionNotification
    
    notification, created = SubmissionNotification.objects.get_or_create(
        representative=representative
    )
    
    return notification


def process_pending_email_notifications():
    """
    Process all pending email notifications.
    
    This should be called periodically (e.g., every 5 minutes via Celery)
    to batch email notifications instead of sending one per submission.
    
    Returns:
        int: Number of notifications processed
    """
    from ..models import SubmissionNotification
    
    pending = SubmissionNotification.get_pending_email_notifications()
    
    if not pending.exists():
        return 0
    
    # Group by timeframe and send batch email
    representatives = [n.representative for n in pending]
    
    # Get admin emails
    admin_emails = list(
        User.objects.filter(is_staff=True, is_active=True)
        .values_list('email', flat=True)
    )
    
    if not admin_emails:
        return 0
    
    # Prepare email context
    context = {
        'submissions': representatives,
        'count': len(representatives),
        'site_url': settings.SITE_URL,
    }
    
    # Render email template
    subject = f"New Submissions: {len(representatives)} representative(s) added"
    html_message = render_to_string('academic_directory/emails/batch_notification.html', context)
    plain_message = strip_tags(html_message)
    
    from_email = settings.DEFAULT_FROM_EMAIL
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
        
        # Mark all as emailed
        for notification in pending:
            notification.mark_as_emailed()
        
        return len(representatives)
    except Exception as e:
        print(f"Error sending batch notification email: {e}")
        return 0


# Email template context helpers

def get_representative_email_context(representative):
    """
    Get standardized context dictionary for representative email templates.
    
    Args:
        representative: Representative instance
    
    Returns:
        dict: Context dictionary for email templates
    """
    context = {
        'representative': representative,
        'display_name': representative.display_name,
        'full_name': representative.full_name,
        'phone_number': representative.phone_number,
        'email': representative.email,
        'university': representative.university.name,
        'faculty': representative.faculty.name,
        'department': representative.department.name,
        'role': representative.get_role_display(),
        'verification_status': representative.get_verification_status_display(),
        'created_at': representative.created_at,
        'admin_url': f"{settings.SITE_URL}/admin/academic_directory/representative/{representative.id}/change/",
    }
    
    # Add level info for class reps
    if representative.role == 'CLASS_REP':
        context.update({
            'current_level': representative.current_level_display,
            'entry_year': representative.entry_year,
            'expected_graduation_year': representative.expected_graduation_year,
            'is_final_year': representative.is_final_year,
        })
    else:
        context.update({
            'tenure_start_year': representative.tenure_start_year,
        })
    
    return context
