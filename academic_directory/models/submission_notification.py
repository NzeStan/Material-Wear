"""
Submission Notification Model

Tracks new submissions for admin dashboard notifications.
"""

from django.db import models
from django.utils import timezone
from django.conf import settings

class SubmissionNotification(models.Model):
    """
    Submission Notification model for tracking new representative submissions.
    
    This model creates a notification record for each new submission,
    allowing admins to:
    - See count of unread/new submissions in dashboard
    - Track which submissions have been reviewed
    - Get email alerts for new submissions
    
    Attributes:
        representative: Foreign key to Representative
        is_read: Whether admin has viewed this notification
        is_emailed: Whether email notification was sent
        emailed_at: When email was sent
        read_by: Admin user who read this notification
        read_at: When notification was read
        created_at: When notification was created
    """
    
    representative = models.OneToOneField(
        'Representative',
        on_delete=models.CASCADE,
        related_name='notification',
        help_text="Representative this notification is for"
    )
    
    is_read = models.BooleanField(
        default=False,
        help_text="Whether this notification has been read by an admin"
    )
    
    is_emailed = models.BooleanField(
        default=False,
        help_text="Whether email notification was sent"
    )
    
    emailed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When email notification was sent"
    )
    
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='read_notifications',
        help_text="Admin user who read this notification"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was marked as read"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this notification was created"
    )
    
    class Meta:
        verbose_name = "Submission Notification"
        verbose_name_plural = "Submission Notifications"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read', '-created_at']),
            models.Index(fields=['is_emailed']),
        ]
    
    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"{self.representative.display_name} - {status}"
    
    def mark_as_read(self, user=None):
        """
        Mark this notification as read.
        
        Args:
            user: Optional User instance who read the notification
        """
        self.is_read = True
        self.read_at = timezone.now()
        if user:
            self.read_by = user
        self.save()
    
    def mark_as_emailed(self):
        """Mark that email notification has been sent."""
        self.is_emailed = True
        self.emailed_at = timezone.now()
        self.save()
    
    @classmethod
    def get_unread_count(cls):
        """Get count of unread notifications."""
        return cls.objects.filter(is_read=False).count()
    
    @classmethod
    def get_pending_email_notifications(cls):
        """Get notifications that need email sending."""
        return cls.objects.filter(
            is_emailed=False,
            is_read=False
        ).select_related('representative__department__faculty__university')
