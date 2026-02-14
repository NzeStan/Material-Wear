# academic_directory/tests/utils/test_notifications.py
"""
Comprehensive test suite for notifications utility.

Test Coverage:
- Send new submission email
- Send bulk verification email
- Get unread notification count
- Mark notification as read
- Mark all notifications as read
- Create submission notification
- Email context generation
"""

from django.test import TestCase
from unittest.mock import patch, Mock
from django.contrib.auth import get_user_model
from academic_directory.models import (
    University, Faculty, Department, Representative, 
    ProgramDuration, SubmissionNotification
)
from academic_directory.utils.notifications import (
    send_new_submission_email,
    send_bulk_verification_email,
    get_unread_notification_count,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    create_submission_notification,
    get_representative_email_context
)

User = get_user_model()


class SendNewSubmissionEmailTest(TestCase):
    """Test sending new submission emails."""
    
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
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    @patch('academic_directory.utils.notifications.send_new_submission_email_async')
    def test_sends_email_async(self, mock_send):
        """Test email is sent asynchronously."""
        send_new_submission_email(self.rep)
        
        # Should call background task
        mock_send.assert_called_once_with(self.rep.id)
    
    @patch('academic_directory.utils.notifications.send_new_submission_email_async')
    def test_handles_none_admin_emails(self, mock_send):
        """Test handles None admin_emails gracefully."""
        send_new_submission_email(self.rep, admin_emails=None)
        
        mock_send.assert_called_once()


class SendBulkVerificationEmailTest(TestCase):
    """Test sending bulk verification emails."""
    
    def setUp(self):
        """Create test data."""
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="test",
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
        self.reps = [
            Representative.objects.create(
                full_name=f"Rep {i}",
                phone_number=f"+234801234{i:04d}",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2020
            )
            for i in range(3)
        ]
    
    @patch('academic_directory.utils.notifications.send_bulk_verification_email_async')
    def test_sends_bulk_email(self, mock_send):
        """Test bulk verification email is sent."""
        send_bulk_verification_email(self.reps, self.admin)
        
        # Should call with list of IDs and verifier ID
        mock_send.assert_called_once()
        args = mock_send.call_args[0]
        self.assertEqual(len(args[0]), 3)  # 3 representative IDs
        self.assertEqual(args[1], self.admin.id)


class GetUnreadNotificationCountTest(TestCase):
    """Test getting unread notification count."""
    
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
    
    def test_returns_zero_when_no_notifications(self):
        """Test returns 0 when no notifications exist."""
        count = get_unread_notification_count()
        self.assertEqual(count, 0)
    
    def test_counts_unread_notifications(self):
        """Test counts only unread notifications."""
        rep1 = Representative.objects.create(
            full_name="Rep 1",
            phone_number="+2348012340001",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep2 = Representative.objects.create(
            full_name="Rep 2",
            phone_number="+2348012340002",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Create notifications
        notif1 = SubmissionNotification.objects.create(representative=rep1)
        notif2 = SubmissionNotification.objects.create(representative=rep2)
        
        # Mark one as read
        notif1.is_read = True
        notif1.save()
        
        count = get_unread_notification_count()
        self.assertEqual(count, 1)


class MarkNotificationAsReadTest(TestCase):
    """Test marking notifications as read."""
    
    def setUp(self):
        """Create test data."""
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="test",
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
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
    
    def test_marks_notification_as_read(self):
        """Test notification is marked as read."""
        result = mark_notification_as_read(self.notification.id, self.admin)
        
        self.assertTrue(result)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)
        self.assertEqual(self.notification.read_by, self.admin)
    
    def test_returns_false_for_nonexistent(self):
        """Test returns False for non-existent notification."""
        result = mark_notification_as_read(99999)
        self.assertFalse(result)


class MarkAllNotificationsAsReadTest(TestCase):
    """Test marking all notifications as read."""
    
    def setUp(self):
        """Create test data."""
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="test",
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
    
    def test_marks_all_as_read(self):
        """Test all unread notifications are marked as read."""
        # Create multiple representatives and notifications
        for i in range(3):
            rep = Representative.objects.create(
                full_name=f"Rep {i}",
                phone_number=f"+234801234{i:04d}",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2020
            )
            SubmissionNotification.objects.create(representative=rep)
        
        count = mark_all_notifications_as_read(self.admin)
        
        self.assertEqual(count, 3)
        self.assertEqual(SubmissionNotification.objects.filter(is_read=False).count(), 0)


class CreateSubmissionNotificationTest(TestCase):
    """Test creating submission notifications."""
    
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
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_creates_notification(self):
        """Test notification is created."""
        notification = create_submission_notification(self.rep)
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.representative, self.rep)
    
    def test_does_not_duplicate(self):
        """Test doesn't create duplicate notification."""
        notification1 = create_submission_notification(self.rep)
        notification2 = create_submission_notification(self.rep)
        
        self.assertEqual(notification1.id, notification2.id)
        self.assertEqual(SubmissionNotification.objects.filter(representative=self.rep).count(), 1)


class GetRepresentativeEmailContextTest(TestCase):
    """Test email context generation."""
    
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
            phone_number="+2348012345678",
            email="john@example.com",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_includes_basic_info(self):
        """Test context includes basic representative info."""
        context = get_representative_email_context(self.rep)
        
        self.assertEqual(context['full_name'], 'John Doe')
        self.assertEqual(context['display_name'], 'Johnny')
        self.assertEqual(context['phone_number'], '+2348012345678')
        self.assertEqual(context['email'], 'john@example.com')
    
    def test_includes_institutional_info(self):
        """Test context includes institutional information."""
        context = get_representative_email_context(self.rep)
        
        self.assertEqual(context['university'], 'University of Benin')
        self.assertEqual(context['faculty'], 'Faculty of Engineering')
        self.assertEqual(context['department'], 'Computer Science')
    
    def test_includes_class_rep_specific_fields(self):
        """Test context includes class rep specific fields."""
        context = get_representative_email_context(self.rep)
        
        self.assertIn('current_level', context)
        self.assertIn('entry_year', context)
        self.assertIn('expected_graduation_year', context)
        self.assertIn('is_final_year', context)
    
    def test_includes_president_specific_fields(self):
        """Test context includes president specific fields."""
        president = Representative.objects.create(
            full_name="Jane President",
            phone_number="+2348087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        context = get_representative_email_context(president)
        
        self.assertIn('tenure_start_year', context)
        self.assertEqual(context['tenure_start_year'], 2024)