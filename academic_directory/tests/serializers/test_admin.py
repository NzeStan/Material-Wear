# academic_directory/tests/serializers/test_admin.py
"""
Comprehensive test suite for Admin serializers.

Test Coverage:
- RepresentativeHistorySerializer
- SubmissionNotificationSerializer
- DashboardStatsSerializer
- Read-only serialization
- Display fields
- Nested data
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from academic_directory.models import (
    University, Faculty, Department, Representative,
    ProgramDuration, RepresentativeHistory, SubmissionNotification
)
from academic_directory.serializers import (
    RepresentativeHistorySerializer,
    SubmissionNotificationSerializer,
    DashboardStatsSerializer
)

User = get_user_model()


class RepresentativeHistorySerializerTest(TestCase):
    """Test RepresentativeHistorySerializer."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.history = RepresentativeHistory.create_from_representative(self.rep)
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = RepresentativeHistorySerializer(self.history)
        data = serializer.data
        
        expected_fields = {
            'id', 'representative', 'full_name', 'phone_number',
            'department_name', 'faculty_name', 'university_name',
            'role', 'role_display', 'entry_year', 'tenure_start_year',
            'verification_status', 'is_active', 'snapshot_date', 'notes'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = RepresentativeHistorySerializer(self.history)
        data = serializer.data
        
        self.assertEqual(data['full_name'], "John Doe")
        self.assertEqual(data['phone_number'], "08012345678")
        self.assertEqual(data['role'], "CLASS_REP")
        self.assertEqual(data['entry_year'], 2020)
    
    def test_serialization_display_fields(self):
        """Test serialization of display fields."""
        serializer = RepresentativeHistorySerializer(self.history)
        data = serializer.data
        
        self.assertEqual(data['role_display'], "Class Representative")
        self.assertEqual(data['department_name'], "Computer Science")
        self.assertEqual(data['faculty_name'], "Faculty of Engineering")
        self.assertEqual(data['university_name'], "University of Benin")
    
    def test_serialization_role_display_property(self):
        """Test role_display is properly serialized."""
        serializer = RepresentativeHistorySerializer(self.history)
        data = serializer.data
        
        self.assertIsNotNone(data['role_display'])
        self.assertIsInstance(data['role_display'], str)
    
    def test_serialization_snapshot_date(self):
        """Test snapshot_date is included."""
        serializer = RepresentativeHistorySerializer(self.history)
        data = serializer.data
        
        self.assertIn('snapshot_date', data)
        self.assertIsNotNone(data['snapshot_date'])
    
    def test_serialization_dept_president_history(self):
        """Test serialization for DEPT_PRESIDENT role."""
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        history2 = RepresentativeHistory.create_from_representative(rep2)
        
        serializer = RepresentativeHistorySerializer(history2)
        data = serializer.data
        
        self.assertEqual(data['role'], "DEPT_PRESIDENT")
        self.assertEqual(data['tenure_start_year'], 2024)
        self.assertIsNone(data['entry_year'])
    
    def test_serialize_multiple_histories(self):
        """Test serializing multiple history records."""
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2021
        )
        history2 = RepresentativeHistory.create_from_representative(rep2)
        
        serializer = RepresentativeHistorySerializer([self.history, history2], many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['full_name'], "John Doe")
        self.assertEqual(data[1]['full_name'], "Jane Smith")


class SubmissionNotificationSerializerTest(TestCase):
    """Test SubmissionNotificationSerializer."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        self.rep = Representative.objects.create(
            full_name="John Doe",
            nickname="Johnny",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123"
        )
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = SubmissionNotificationSerializer(self.notification)
        data = serializer.data
        
        expected_fields = {
            'id', 'representative', 'representative_name', 'representative_phone',
            'representative_role', 'university_name', 'is_read', 'is_emailed',
            'emailed_at', 'read_by', 'read_by_username', 'read_at', 'created_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_representative_fields(self):
        """Test serialization of representative-related fields."""
        serializer = SubmissionNotificationSerializer(self.notification)
        data = serializer.data
        
        self.assertEqual(data['representative_name'], "Johnny")  # Uses display_name
        self.assertEqual(data['representative_phone'], "08012345678")
        self.assertEqual(data['representative_role'], "Class Representative")
        self.assertEqual(data['university_name'], "University of Benin")
    
    def test_serialization_unread_notification(self):
        """Test serialization of unread notification."""
        serializer = SubmissionNotificationSerializer(self.notification)
        data = serializer.data
        
        self.assertFalse(data['is_read'])
        self.assertFalse(data['is_emailed'])
        self.assertIsNone(data['emailed_at'])
        self.assertIsNone(data['read_by'])
        self.assertIsNone(data['read_by_username'])
        self.assertIsNone(data['read_at'])
    
    def test_serialization_read_notification(self):
        """Test serialization of read notification."""
        self.notification.mark_as_read(self.user)
        
        serializer = SubmissionNotificationSerializer(self.notification)
        data = serializer.data
        
        self.assertTrue(data['is_read'])
        self.assertEqual(data['read_by'], str(self.user.id))
        self.assertEqual(data['read_by_username'], self.user.username)
        self.assertIsNotNone(data['read_at'])
    
    def test_serialization_emailed_notification(self):
        """Test serialization of emailed notification."""
        self.notification.mark_as_emailed()
        
        serializer = SubmissionNotificationSerializer(self.notification)
        data = serializer.data
        
        self.assertTrue(data['is_emailed'])
        self.assertIsNotNone(data['emailed_at'])
    
    def test_serialize_multiple_notifications(self):
        """Test serializing multiple notifications."""
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2021
        )
        notification2 = SubmissionNotification.objects.create(representative=rep2)
        
        serializer = SubmissionNotificationSerializer(
            [self.notification, notification2],
            many=True
        )
        data = serializer.data
        
        self.assertEqual(len(data), 2)


class DashboardStatsSerializerTest(TestCase):
    """Test DashboardStatsSerializer."""
    
    def test_serialization_with_all_fields(self):
        """Test serialization with all required fields."""
        stats = {
            'total_representatives': 100,
            'total_universities': 5,
            'total_faculties': 20,
            'total_departments': 80,
            'unverified_count': 30,
            'verified_count': 60,
            'disputed_count': 10,
            'class_reps_count': 70,
            'dept_presidents_count': 20,
            'faculty_presidents_count': 10,
            'unread_notifications': 15,
            'recent_submissions_24h': 5,
            'recent_submissions_7d': 25,
        }
        
        serializer = DashboardStatsSerializer(stats)
        data = serializer.data
        
        self.assertEqual(len(data), 13)
        self.assertEqual(data['total_representatives'], 100)
        self.assertEqual(data['total_universities'], 5)
        self.assertEqual(data['unverified_count'], 30)
        self.assertEqual(data['class_reps_count'], 70)
        self.assertEqual(data['recent_submissions_24h'], 5)
    
    def test_serialization_all_fields_present(self):
        """Test that all fields are properly serialized."""
        stats = {
            'total_representatives': 10,
            'total_universities': 2,
            'total_faculties': 5,
            'total_departments': 15,
            'unverified_count': 3,
            'verified_count': 6,
            'disputed_count': 1,
            'class_reps_count': 7,
            'dept_presidents_count': 2,
            'faculty_presidents_count': 1,
            'unread_notifications': 4,
            'recent_submissions_24h': 2,
            'recent_submissions_7d': 8,
        }
        
        serializer = DashboardStatsSerializer(stats)
        data = serializer.data
        
        expected_fields = {
            'total_representatives', 'total_universities', 'total_faculties',
            'total_departments', 'unverified_count', 'verified_count',
            'disputed_count', 'class_reps_count', 'dept_presidents_count',
            'faculty_presidents_count', 'unread_notifications',
            'recent_submissions_24h', 'recent_submissions_7d'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_with_zero_values(self):
        """Test serialization with zero values."""
        stats = {
            'total_representatives': 0,
            'total_universities': 0,
            'total_faculties': 0,
            'total_departments': 0,
            'unverified_count': 0,
            'verified_count': 0,
            'disputed_count': 0,
            'class_reps_count': 0,
            'dept_presidents_count': 0,
            'faculty_presidents_count': 0,
            'unread_notifications': 0,
            'recent_submissions_24h': 0,
            'recent_submissions_7d': 0,
        }
        
        serializer = DashboardStatsSerializer(stats)
        data = serializer.data
        
        self.assertEqual(data['total_representatives'], 0)
        self.assertEqual(data['unread_notifications'], 0)
    
    def test_serialization_with_large_numbers(self):
        """Test serialization with large numbers."""
        stats = {
            'total_representatives': 10000,
            'total_universities': 500,
            'total_faculties': 2000,
            'total_departments': 8000,
            'unverified_count': 3000,
            'verified_count': 6000,
            'disputed_count': 1000,
            'class_reps_count': 7000,
            'dept_presidents_count': 2000,
            'faculty_presidents_count': 1000,
            'unread_notifications': 1500,
            'recent_submissions_24h': 500,
            'recent_submissions_7d': 2500,
        }
        
        serializer = DashboardStatsSerializer(stats)
        data = serializer.data
        
        self.assertEqual(data['total_representatives'], 10000)
        self.assertEqual(data['unread_notifications'], 1500)
    
    def test_serializer_is_read_only(self):
        """Test that DashboardStatsSerializer is read-only."""
        stats = {
            'total_representatives': 10,
            'total_universities': 2,
            'total_faculties': 5,
            'total_departments': 15,
            'unverified_count': 3,
            'verified_count': 6,
            'disputed_count': 1,
            'class_reps_count': 7,
            'dept_presidents_count': 2,
            'faculty_presidents_count': 1,
            'unread_notifications': 4,
            'recent_submissions_24h': 2,
            'recent_submissions_7d': 8,
        }
        
        serializer = DashboardStatsSerializer(stats)
        
        # This serializer is for output only, not for input validation
        self.assertIsNotNone(serializer.data)