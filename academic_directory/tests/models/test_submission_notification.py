# academic_directory/tests/models/test_submission_notification.py
"""
Comprehensive test suite for SubmissionNotification model.

Test Coverage:
- Model creation and basic functionality
- One-to-one relationship with Representative
- Notification status tracking (is_read, is_emailed)
- Methods (mark_as_read, mark_as_emailed)
- Class methods (get_unread_count, get_pending_email_notifications)
- Foreign key relationships
- Cascade delete behavior
- String representation
- Edge cases and boundary conditions
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from academic_directory.models import (
    University, Faculty, Department, Representative,
    SubmissionNotification
)
import uuid

User = get_user_model()


class SubmissionNotificationCreationTest(TestCase):
    """Test basic submission notification creation."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_create_notification_with_valid_data(self):
        """Test creating a notification with all valid data."""
        notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        
        self.assertIsNotNone(notification.id)
        self.assertIsInstance(notification.id, uuid.UUID)
        self.assertEqual(notification.representative, self.rep)
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_emailed)
        self.assertIsNone(notification.emailed_at)
        self.assertIsNone(notification.read_by)
        self.assertIsNone(notification.read_at)
        self.assertIsNotNone(notification.created_at)
    
    def test_default_is_read_false(self):
        """Test that is_read defaults to False."""
        notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        
        self.assertFalse(notification.is_read)
    
    def test_default_is_emailed_false(self):
        """Test that is_emailed defaults to False."""
        notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        
        self.assertFalse(notification.is_emailed)


class OneToOneRelationshipTest(TestCase):
    """Test one-to-one relationship with Representative."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_one_to_one_constraint(self):
        """Test that representative can have only one notification."""
        notification1 = SubmissionNotification.objects.create(
            representative=self.rep
        )
        
        # Attempting to create another notification for same representative
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SubmissionNotification.objects.create(
                representative=self.rep
            )
    
    def test_representative_notification_reverse_relation(self):
        """Test reverse relation from representative to notification."""
        notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        
        # Access via reverse relation
        self.assertEqual(self.rep.notification, notification)
    
    def test_representative_without_notification(self):
        """Test accessing notification on representative without one raises error."""
        # Create another rep without notification
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        with self.assertRaises(SubmissionNotification.DoesNotExist):
            _ = rep2.notification


class MarkAsReadMethodTest(TestCase):
    """Test mark_as_read() method."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.user = User.objects.create_user(
            username="admin",
            password="testpass123"
        )
        self.notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
    
    def test_mark_as_read_without_user(self):
        """Test mark_as_read() without user."""
        self.assertFalse(self.notification.is_read)
        self.assertIsNone(self.notification.read_at)
        self.assertIsNone(self.notification.read_by)
        
        self.notification.mark_as_read()
        
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)
        self.assertIsNone(self.notification.read_by)
    
    def test_mark_as_read_with_user(self):
        """Test mark_as_read() with user."""
        self.notification.mark_as_read(user=self.user)
        
        self.assertTrue(self.notification.is_read)
        self.assertIsNotNone(self.notification.read_at)
        self.assertEqual(self.notification.read_by, self.user)
    
    def test_mark_as_read_sets_timestamp(self):
        """Test that mark_as_read() sets read_at timestamp."""
        before_time = timezone.now()
        
        self.notification.mark_as_read()
        
        after_time = timezone.now()
        
        self.assertGreaterEqual(self.notification.read_at, before_time)
        self.assertLessEqual(self.notification.read_at, after_time)


class MarkAsEmailedMethodTest(TestCase):
    """Test mark_as_emailed() method."""
    
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
    
    def test_mark_as_emailed(self):
        """Test mark_as_emailed() method."""
        self.assertFalse(self.notification.is_emailed)
        self.assertIsNone(self.notification.emailed_at)
        
        self.notification.mark_as_emailed()
        
        self.assertTrue(self.notification.is_emailed)
        self.assertIsNotNone(self.notification.emailed_at)
    
    def test_mark_as_emailed_sets_timestamp(self):
        """Test that mark_as_emailed() sets emailed_at timestamp."""
        before_time = timezone.now()
        
        self.notification.mark_as_emailed()
        
        after_time = timezone.now()
        
        self.assertGreaterEqual(self.notification.emailed_at, before_time)
        self.assertLessEqual(self.notification.emailed_at, after_time)


class GetUnreadCountClassMethodTest(TestCase):
    """Test get_unread_count() class method."""
    
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
    
    def test_get_unread_count_zero_initially(self):
        """Test that unread count is 0 initially."""
        count = SubmissionNotification.get_unread_count()
        self.assertEqual(count, 0)
    
    def test_get_unread_count_with_unread_notifications(self):
        """Test unread count with unread notifications."""
        rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        SubmissionNotification.objects.create(representative=rep1)
        SubmissionNotification.objects.create(representative=rep2)
        
        count = SubmissionNotification.get_unread_count()
        self.assertEqual(count, 2)
    
    def test_get_unread_count_excludes_read_notifications(self):
        """Test that unread count excludes read notifications."""
        rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        notification1 = SubmissionNotification.objects.create(representative=rep1)
        notification2 = SubmissionNotification.objects.create(representative=rep2)
        
        # Mark one as read
        notification1.mark_as_read()
        
        count = SubmissionNotification.get_unread_count()
        self.assertEqual(count, 1)


class GetPendingEmailNotificationsClassMethodTest(TestCase):
    """Test get_pending_email_notifications() class method."""
    
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
    
    def test_get_pending_email_notifications_empty_initially(self):
        """Test that pending email notifications is empty initially."""
        pending = SubmissionNotification.get_pending_email_notifications()
        self.assertEqual(pending.count(), 0)
    
    def test_get_pending_email_notifications_with_pending(self):
        """Test pending email notifications with pending notifications."""
        rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        notification1 = SubmissionNotification.objects.create(representative=rep1)
        notification2 = SubmissionNotification.objects.create(representative=rep2)
        
        pending = SubmissionNotification.get_pending_email_notifications()
        self.assertEqual(pending.count(), 2)
        self.assertIn(notification1, pending)
        self.assertIn(notification2, pending)
    
    def test_get_pending_email_excludes_emailed(self):
        """Test that pending email excludes already emailed notifications."""
        rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        notification1 = SubmissionNotification.objects.create(representative=rep1)
        notification2 = SubmissionNotification.objects.create(representative=rep2)
        
        # Mark one as emailed
        notification1.mark_as_emailed()
        
        pending = SubmissionNotification.get_pending_email_notifications()
        self.assertEqual(pending.count(), 1)
        self.assertNotIn(notification1, pending)
        self.assertIn(notification2, pending)
    
    def test_get_pending_email_excludes_read(self):
        """Test that pending email excludes read notifications."""
        rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        notification1 = SubmissionNotification.objects.create(representative=rep1)
        notification2 = SubmissionNotification.objects.create(representative=rep2)
        
        # Mark one as read
        notification1.mark_as_read()
        
        pending = SubmissionNotification.get_pending_email_notifications()
        self.assertEqual(pending.count(), 1)
        self.assertNotIn(notification1, pending)
        self.assertIn(notification2, pending)


class CascadeDeleteBehaviorTest(TestCase):
    """Test cascade delete behavior."""
    
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
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_delete_representative_deletes_notification(self):
        """Test that deleting representative deletes notification."""
        notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        
        self.assertEqual(SubmissionNotification.objects.count(), 1)
        
        self.rep.delete()
        
        # Notification should be deleted
        self.assertEqual(SubmissionNotification.objects.count(), 0)
    
    def test_delete_user_sets_read_by_null(self):
        """Test that deleting user sets read_by to NULL."""
        user = User.objects.create_user(
            username="admin",
            password="testpass123"
        )
        
        notification = SubmissionNotification.objects.create(
            representative=self.rep
        )
        notification.mark_as_read(user=user)
        
        self.assertEqual(notification.read_by, user)
        
        # Delete user
        user.delete()
        
        # Notification should still exist but read_by should be NULL
        notification.refresh_from_db()
        self.assertIsNone(notification.read_by)
        self.assertTrue(notification.is_read)  # is_read should remain True


class StringRepresentationTest(TestCase):
    """Test string representation."""
    
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
    
    def test_str_format_unread(self):
        """Test __str__ for unread notification."""
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notification = SubmissionNotification.objects.create(
            representative=rep
        )
        
        expected = "John Doe - Unread"
        self.assertEqual(str(notification), expected)
    
    def test_str_format_read(self):
        """Test __str__ for read notification."""
        rep = Representative.objects.create(
            full_name="John Doe",
            nickname="Jon",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notification = SubmissionNotification.objects.create(
            representative=rep
        )
        notification.mark_as_read()
        
        # Uses display_name (nickname if available)
        expected = "Jon - Read"
        self.assertEqual(str(notification), expected)


class MetaOptionsTest(TestCase):
    """Test model Meta options."""
    
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
    
    def test_ordering_by_created_at_desc(self):
        """Test that notifications are ordered by created_at descending."""
        import time
        
        rep1 = Representative.objects.create(
            full_name="First Rep",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notification1 = SubmissionNotification.objects.create(
            representative=rep1
        )
        
        time.sleep(0.01)
        
        rep2 = Representative.objects.create(
            full_name="Second Rep",
            phone_number="08098765432",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        
        notification2 = SubmissionNotification.objects.create(
            representative=rep2
        )
        
        notifications = list(SubmissionNotification.objects.all())
        self.assertEqual(notifications[0].id, notification2.id)  # Newest first
        self.assertEqual(notifications[1].id, notification1.id)
    
    def test_verbose_name(self):
        """Test verbose_name is set correctly."""
        self.assertEqual(
            SubmissionNotification._meta.verbose_name,
            "Submission Notification"
        )
    
    def test_verbose_name_plural(self):
        """Test verbose_name_plural is set correctly."""
        self.assertEqual(
            SubmissionNotification._meta.verbose_name_plural,
            "Submission Notifications"
        )


class IndexingTest(TestCase):
    """Test database indexes."""
    
    def test_is_read_created_at_composite_index(self):
        """Test composite index on is_read and created_at."""
        indexes = [index.fields for index in SubmissionNotification._meta.indexes]
        self.assertIn(['is_read', '-created_at'], indexes)
    
    def test_is_emailed_index_exists(self):
        """Test that is_emailed field has an index."""
        indexes = [index.fields for index in SubmissionNotification._meta.indexes]
        self.assertIn(['is_emailed'], indexes)