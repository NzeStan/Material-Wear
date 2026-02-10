"""Dashboard View"""

from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count

from ..models import (
    Representative, University, Faculty, Department, SubmissionNotification
)
from ..serializers import DashboardStatsSerializer, SubmissionNotificationSerializer
from ..utils.notifications import mark_notification_as_read, mark_all_notifications_as_read


class DashboardView(APIView):
    """
    Dashboard statistics endpoint.
    
    Returns counts and metrics for admin dashboard.
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        """Get dashboard statistics."""
        
        # Calculate date ranges
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=7)
        
        # Gather statistics
        stats = {
            'total_representatives': Representative.objects.filter(is_active=True).count(),
            'total_universities': University.objects.filter(is_active=True).count(),
            'total_faculties': Faculty.objects.filter(is_active=True).count(),
            'total_departments': Department.objects.filter(is_active=True).count(),
            
            # By verification status
            'unverified_count': Representative.objects.filter(
                verification_status='UNVERIFIED', is_active=True
            ).count(),
            'verified_count': Representative.objects.filter(
                verification_status='VERIFIED', is_active=True
            ).count(),
            'disputed_count': Representative.objects.filter(
                verification_status='DISPUTED', is_active=True
            ).count(),
            
            # By role
            'class_reps_count': Representative.objects.filter(
                role='CLASS_REP', is_active=True
            ).count(),
            'dept_presidents_count': Representative.objects.filter(
                role='DEPT_PRESIDENT', is_active=True
            ).count(),
            'faculty_presidents_count': Representative.objects.filter(
                role='FACULTY_PRESIDENT', is_active=True
            ).count(),
            
            # Notifications
            'unread_notifications': SubmissionNotification.get_unread_count(),
            
            # Recent activity
            'recent_submissions_24h': Representative.objects.filter(
                created_at__gte=yesterday
            ).count(),
            'recent_submissions_7d': Representative.objects.filter(
                created_at__gte=last_week
            ).count(),
        }
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for submission notifications.
    
    Admin can view and mark notifications as read.
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = SubmissionNotification.objects.select_related(
        'representative__department__faculty__university', 'read_by'
    ).order_by('-created_at')
    serializer_class = SubmissionNotificationSerializer
    
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.mark_as_read(request.user)
        
        return Response({
            'success': True,
            'message': 'Notification marked as read'
        })
    
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read."""
        count = mark_all_notifications_as_read(request.user)
        
        return Response({
            'success': True,
            'message': f'Marked {count} notifications as read',
            'count': count
        })
