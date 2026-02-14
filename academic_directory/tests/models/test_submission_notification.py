# academic_directory/tests/models/test_submission_notification.py
"""
Comprehensive test suite for SubmissionNotification model.

Test Coverage:
- Model creation and defaults
- OneToOneField relationship with Representative
- mark_as_read() method
- mark_as_emailed() method
- get_unread_count() class method
- get_unemailed_count() class method
- String representation
- Meta options (ordering)
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError
from academic_directory.models import (
    University, Faculty, Department, Representative, SubmissionNotification
)

User = get_user_model()


class SubmissionNotificationCreationTest(TestCase):
    """Test notification creation."""
    
    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        
        self.university = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Engineering",
            abbreviation="COE"
        )
    
    def test_create_notification_with_valid_data(self):
        """Test creating a notification with all valid data."""
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="+2348012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Signal creates notification automatically
        notification = rep.notification
        
        self.assertEqual(notification.representative, rep)
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_emailed)
        self.assertIsNone(notification.read_by)
        self.assertIsNone(notification.read_at)
        self.assertIsNone(notification.emailed_at)
        self.assertIsNotNone(notification.created_at)
    
    def test_default_is_read_false(self):
        """Test that is_read defaults to False."""
        rep = Representative.objects.create(
            full_name="Jane Doe",
            phone_number="+2348012345679",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notification = rep.notification
        self.assertFalse(notification.is_read)
    
    def test_default_is_emailed_false(self):
        """Test that is_emailed defaults to False."""
        rep = Representative.objects.create(
            full_name="Bob Smith",
            phone_number="+2348012345680",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notification = rep.notification
        self.assertFalse(notification.is_emailed)


class OneToOneRelationshipTest(TestCase):
    """Test OneToOneField relationship."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Engineering",
            abbreviation="COE"
        )
    
    def test_one_to_one_constraint(self):
        """Test that representative can have only one notification."""
        rep = Representative.objects.create(
            full_name="Alice Johnson",
            phone_number="+2348012345681",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Signal already created one notification
        self.assertEqual(SubmissionNotification.objects.filter(representative=rep).count(), 1)
        
        # Try to create duplicate - should raise IntegrityError
        with self.assertRaises(IntegrityError):
            SubmissionNotification.objects.create(representative=rep)
    
    def test_representative_notification_reverse_relation(self):
        """Test reverse relation from representative to notification."""
        rep = Representative.objects.create(
            full_name="Charlie Brown",
            phone_number="+2348012345682",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Access via reverse relation
        notification = rep.notification
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.representative, rep)
    
    def test_representative_without_notification(self):
        """Test accessing notification on representative without one raises error."""
        from django.db.models.signals import post_save
        from academic_directory.signals import create_submission_notification
        
        # Temporarily disconnect the signal
        post_save.disconnect(create_submission_notification, sender=Representative)
        
        try:
            rep = Representative.objects.create(
                full_name="David Miller",
                phone_number="+2348012345683",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2020
            )
            
            # Should raise DoesNotExist
            with self.assertRaises(SubmissionNotification.DoesNotExist):
                _ = rep.notification
        finally:
            # Reconnect the signal
            post_save.connect(create_submission_notification, sender=Representative)


class MarkAsReadMethodTest(TestCase):
    """Test mark_as_read() method."""
    
    def setUp(self):
        """Create test data."""
        self.user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        
        self.university = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Engineering",
            abbreviation="COE"
        )
        
        # Create representative - signal creates notification
        self.representative = Representative.objects.create(
            full_name="Test User",
            phone_number="+2348012345684",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        # Access the notification created by signal
        self.notification = self.representative.notification
    
    def test_mark_as_read_without_user(self):
        """Test mark_as_read() without user."""
        self.assertFalse(self.notification.is_read)
        
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
        before = timezone.now()
        self.notification.mark_as_read()
        after = timezone.now()
        
        self.assertIsNotNone(self.notification.read_at)
        self.assertGreaterEqual(self.notification.read_at, before)
        self.assertLessEqual(self.notification.read_at, after)


class MarkAsEmailedMethodTest(TestCase):
    """Test mark_as_emailed() method."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Engineering",
            abbreviation="COE"
        )
        
        # Create representative - signal creates notification
        self.representative = Representative.objects.create(
            full_name="Email Test User",
            phone_number="+2348012345685",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        # Access the notification created by signal
        self.notification = self.representative.notification
    
    def test_mark_as_emailed(self):
        """Test mark_as_emailed() method."""
        self.assertFalse(self.notification.is_emailed)
        
        self.notification.mark_as_emailed()
        
        self.assertTrue(self.notification.is_emailed)
        self.assertIsNotNone(self.notification.emailed_at)
    
    def test_mark_as_emailed_sets_timestamp(self):
        """Test that mark_as_emailed() sets emailed_at timestamp."""
        before = timezone.now()
        self.notification.mark_as_emailed()
        after = timezone.now()
        
        self.assertIsNotNone(self.notification.emailed_at)
        self.assertGreaterEqual(self.notification.emailed_at, before)
        self.assertLessEqual(self.notification.emailed_at, after)


class GetUnreadCountClassMethodTest(TestCase):
    """Test get_unread_count() class method."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Engineering",
            abbreviation="COE"
        )
    
    def test_get_unread_count_with_unread_notifications(self):
        """Test unread count with unread notifications."""
        # Create representatives - each gets notification via signal
        rep1 = Representative.objects.create(
            full_name="Unread 1",
            phone_number="+2348012345686",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep2 = Representative.objects.create(
            full_name="Unread 2",
            phone_number="+2348012345687",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep3 = Representative.objects.create(
            full_name="Unread 3",
            phone_number="+2348012345688",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Mark one as read
        rep2.notification.mark_as_read()
        
        # Should have 2 unread
        self.assertEqual(SubmissionNotification.get_unread_count(), 2)


class GetUnemailedCountClassMethodTest(TestCase):
    """Test get_unemailed_count() class method."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Engineering",
            abbreviation="COE"
        )
    
    def test_get_unemailed_count_with_unemailed_notifications(self):
        """Test unemailed count."""
        rep1 = Representative.objects.create(
            full_name="Unemailed 1",
            phone_number="+2348012345689",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep2 = Representative.objects.create(
            full_name="Unemailed 2",
            phone_number="+2348012345690",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        rep3 = Representative.objects.create(
            full_name="Unemailed 3",
            phone_number="+2348012345691",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Mark one as emailed
        rep2.notification.mark_as_emailed()
        
        # Should have 2 unemailed
        self.assertEqual(SubmissionNotification.get_unemailed_count(), 2)


class StringRepresentationTest(TestCase):
    """Test __str__ method."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Engineering",
            abbreviation="COE"
        )
    
    def test_str_format_unread(self):
        """Test __str__ for unread notification."""
        rep = Representative.objects.create(
            full_name="String Test User",
            phone_number="+2348012345692",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notification = rep.notification
        expected = f"{rep.display_name} - Unread"
        self.assertEqual(str(notification), expected)
    
    def test_str_format_read(self):
        """Test __str__ for read notification."""
        rep = Representative.objects.create(
            full_name="Read Test User",
            phone_number="+2348012345693",
            nickname="RTU",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notification = rep.notification
        notification.mark_as_read()
        
        expected = f"{rep.display_name} - Read"
        self.assertEqual(str(notification), expected)


class MetaOptionsTest(TestCase):
    """Test Meta options."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Nigeria, Nsukka",
            abbreviation="UNN",
            state="ENUGU",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Engineering",
            abbreviation="COE"
        )
    
    def test_ordering_by_created_at_desc(self):
        """Test that notifications are ordered by created_at descending."""
        rep1 = Representative.objects.create(
            full_name="First",
            phone_number="+2348012345694",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        rep2 = Representative.objects.create(
            full_name="Second",
            phone_number="+2348012345695",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notifications = SubmissionNotification.objects.all()
        
        # Most recent first (rep2 created after rep1)
        self.assertEqual(notifications[0].representative, rep2)
        self.assertEqual(notifications[1].representative, rep1)

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