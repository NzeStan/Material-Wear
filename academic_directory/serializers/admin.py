"""Admin Serializers"""

from rest_framework import serializers
from ..models import RepresentativeHistory, SubmissionNotification


class RepresentativeHistorySerializer(serializers.ModelSerializer):
    """Serializer for representative history."""
    
    role_display = serializers.ReadOnlyField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    faculty_name = serializers.CharField(source='faculty.name', read_only=True)
    university_name = serializers.CharField(source='university.name', read_only=True)
    
    class Meta:
        model = RepresentativeHistory
        fields = [
            'id', 'representative', 'full_name', 'phone_number',
            'department_name', 'faculty_name', 'university_name',
            'role', 'role_display', 'entry_year', 'tenure_start_year',
            'verification_status', 'is_active', 'snapshot_date', 'notes'
        ]


class SubmissionNotificationSerializer(serializers.ModelSerializer):
    """Serializer for submission notifications."""
    
    representative_name = serializers.CharField(source='representative.display_name', read_only=True)
    representative_phone = serializers.CharField(source='representative.phone_number', read_only=True)
    representative_role = serializers.CharField(source='representative.get_role_display', read_only=True)
    university_name = serializers.CharField(source='representative.university.name', read_only=True)
    read_by_username = serializers.CharField(source='read_by.username', read_only=True)
    
    class Meta:
        model = SubmissionNotification
        fields = [
            'id', 'representative', 'representative_name', 'representative_phone',
            'representative_role', 'university_name', 'is_read', 'is_emailed',
            'emailed_at', 'read_by', 'read_by_username', 'read_at', 'created_at'
        ]


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics."""
    
    total_representatives = serializers.IntegerField()
    total_universities = serializers.IntegerField()
    total_faculties = serializers.IntegerField()
    total_departments = serializers.IntegerField()
    
    # By verification status
    unverified_count = serializers.IntegerField()
    verified_count = serializers.IntegerField()
    disputed_count = serializers.IntegerField()
    
    # By role
    class_reps_count = serializers.IntegerField()
    dept_presidents_count = serializers.IntegerField()
    faculty_presidents_count = serializers.IntegerField()
    
    # Notifications
    unread_notifications = serializers.IntegerField()
    
    # Recent activity
    recent_submissions_24h = serializers.IntegerField()
    recent_submissions_7d = serializers.IntegerField()
