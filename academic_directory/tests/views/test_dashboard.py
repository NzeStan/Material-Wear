# academic_directory/tests/views/test_dashboard.py
"""
Comprehensive test suite for Dashboard and Notification views.

Test Coverage:
- DashboardView stats endpoint (admin only)
- NotificationViewSet CRUD (admin only)
- Mark notification as read
- Mark all notifications as read  
- Permissions
- Stats calculation accuracy
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from academic_directory.models import (
    University, Faculty, Department, Representative,
    ProgramDuration, SubmissionNotification
)

User = get_user_model()


class DashboardViewTest(TestCase):
    """Test dashboard stats endpoint."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="testpass123"
        )
        
        # Create test data
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
        self.rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        self.url = '/api/v1/academic-directory/dashboard/'
    
    def test_dashboard_stats_as_admin(self):
        """Test dashboard endpoint returns stats."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_representatives', response.data)
        self.assertIn('total_universities', response.data)
        self.assertIn('total_faculties', response.data)
        self.assertIn('total_departments', response.data)
    
    def test_dashboard_stats_unauthenticated(self):
        """Test unauthenticated users cannot access dashboard."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_dashboard_stats_regular_user(self):
        """Test regular users cannot access dashboard."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_dashboard_counts_representatives_correctly(self):
        """Test that dashboard counts representatives correctly."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.data['total_representatives'], 2)
    
    def test_dashboard_counts_universities_correctly(self):
        """Test that dashboard counts universities correctly."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.data['total_universities'], 1)
    
    def test_dashboard_counts_verification_status(self):
        """Test that dashboard counts verification statuses correctly."""
        self.rep1.verify(self.admin_user)
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertIn('unverified_count', response.data)
        self.assertIn('verified_count', response.data)
        self.assertIn('disputed_count', response.data)
        self.assertEqual(response.data['verified_count'], 1)
        self.assertEqual(response.data['unverified_count'], 1)
    
    def test_dashboard_counts_roles(self):
        """Test that dashboard counts roles correctly."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertIn('class_reps_count', response.data)
        self.assertIn('dept_presidents_count', response.data)
        self.assertIn('faculty_presidents_count', response.data)
        self.assertEqual(response.data['class_reps_count'], 1)
        self.assertEqual(response.data['dept_presidents_count'], 1)


class NotificationViewSetListTest(TestCase):
    """Test listing notifications."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        self.url = '/api/v1/academic-directory/notifications/'
    
    def test_list_notifications_as_admin(self):
        """Test that admin can list notifications."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_list_notifications_unauthenticated(self):
        """Test that unauthenticated users cannot list notifications."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationViewSetMarkAsReadTest(TestCase):
    """Test marking notifications as read."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
    
    def test_mark_notification_as_read(self):
        """Test marking a notification as read."""
        self.client.force_authenticate(user=self.admin_user)
        url = f'/api/v1/academic-directory/notifications/{self.notification.id}/mark-read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertEqual(self.notification.read_by, self.admin_user)
    
    def test_mark_notification_as_read_unauthenticated(self):
        """Test that unauthenticated users cannot mark as read."""
        url = f'/api/v1/academic-directory/notifications/{self.notification.id}/mark-read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_mark_all_notifications_as_read(self):
        """Test marking all notifications as read."""
        # Create another notification
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2021
        )
        notification2 = SubmissionNotification.objects.create(
            representative=rep2
        )
        
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/academic-directory/notifications/mark-all-read/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Both notifications should be marked as read
        self.notification.refresh_from_db()
        notification2.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertTrue(notification2.is_read)


class NotificationViewSetRetrieveTest(TestCase):
    """Test retrieving a single notification."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        self.url = f'/api/v1/academic-directory/notifications/{self.notification.id}/'
    
    def test_retrieve_notification_as_admin(self):
        """Test that admin can retrieve a notification."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['representative_name'], self.rep.display_name)