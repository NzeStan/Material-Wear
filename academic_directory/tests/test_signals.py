# academic_directory/tests/test_signals.py
"""
Comprehensive test suite for academic_directory signals.

Test Coverage:
- create_submission_notification signal (post_save on Representative creation)
- check_graduation_status signal (post_save on Representative update)
- Signal registration and connection
- Deduplication and idempotency
- Graduation logic edge cases
- Recursive signal prevention
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import signals
from unittest.mock import patch, Mock
from academic_directory.models import (
    University, Faculty, Department, Representative, SubmissionNotification
)
from academic_directory.signals import (
    create_submission_notification,
    check_graduation_status
)

User = get_user_model()


class CreateSubmissionNotificationSignalTest(TestCase):
    """Test create_submission_notification signal."""
    
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
    
    def test_creates_notification_on_representative_creation(self):
        """Test notification is created when representative is created."""
        # Should have no notifications initially
        self.assertEqual(SubmissionNotification.objects.count(), 0)
        
        # Create representative
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Should create notification
        self.assertEqual(SubmissionNotification.objects.count(), 1)
        
        notification = SubmissionNotification.objects.first()
        self.assertEqual(notification.representative, rep)
    
    def test_does_not_create_notification_on_update(self):
        """Test notification is NOT created when representative is updated."""
        # Create representative (creates notification)
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        initial_count = SubmissionNotification.objects.count()
        
        # Update representative
        rep.full_name = "Jane Doe"
        rep.save()
        
        # Should not create another notification
        self.assertEqual(SubmissionNotification.objects.count(), initial_count)
    
    def test_notification_created_only_once(self):
        """Test get_or_create prevents duplicate notifications."""
        # Create representative
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Should have exactly one notification
        self.assertEqual(SubmissionNotification.objects.filter(representative=rep).count(), 1)
        
        # Manually trigger signal again (shouldn't happen in practice)
        create_submission_notification(
            sender=Representative,
            instance=rep,
            created=True
        )
        
        # Should still have exactly one notification
        self.assertEqual(SubmissionNotification.objects.filter(representative=rep).count(), 1)
    
    def test_notification_has_correct_defaults(self):
        """Test created notification has correct default values."""
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        notification = SubmissionNotification.objects.get(representative=rep)
        
        self.assertFalse(notification.is_read)
        self.assertFalse(notification.is_emailed)
        self.assertIsNone(notification.emailed_at)
        self.assertIsNone(notification.read_at)
        self.assertIsNone(notification.read_by)


class CheckGraduationStatusSignalTest(TestCase):
    """Test check_graduation_status signal."""
    
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
    
    def test_does_not_check_graduation_on_creation(self):
        """Test graduation check is skipped on creation."""
        # Create a graduated class rep (entry_year 2020 = graduated)
        rep = Representative.objects.create(
            full_name="Graduated Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,  # Graduated
            is_active=True
        )
        
        # Should still be active (signal skips on creation)
        self.assertTrue(rep.is_active)
    
    def test_deactivates_graduated_class_rep_on_update(self):
        """Test graduated class rep is deactivated on update."""
        # Create active class rep
        rep = Representative.objects.create(
            full_name="Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2023,  # Active
            is_active=True
        )
        
        # Verify active
        self.assertTrue(rep.is_active)
        
        # Change to graduated year
        rep.entry_year = 2020  # Graduated
        rep.save()
        
        # Refresh from database
        rep.refresh_from_db()
        
        # Should be deactivated
        self.assertFalse(rep.is_active)
    
    def test_does_not_affect_non_class_reps(self):
        """Test graduation check only affects CLASS_REP role."""
        # Create graduated faculty president
        rep = Representative.objects.create(
            full_name="Faculty President",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="FACULTY_PRESIDENT",
            is_active=True
        )
        
        # Update something
        rep.full_name = "Updated President"
        rep.save()
        
        # Refresh from database
        rep.refresh_from_db()
        
        # Should still be active (not a class rep)
        self.assertTrue(rep.is_active)
    
    def test_adds_deactivation_note(self):
        """Test deactivation adds note with graduation year."""
        # Create class rep
        rep = Representative.objects.create(
            full_name="Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2023,
            is_active=True,
            notes=""
        )
        
        # Change to graduated year
        rep.entry_year = 2020
        rep.save()
        
        # Refresh from database
        rep.refresh_from_db()
        
        # Should have deactivation note
        self.assertIn('Auto-deactivated', rep.notes)
        self.assertIn('Graduated', rep.notes)
        self.assertIn('2025', rep.notes)  # Expected graduation year for 2020 entry
    
    def test_preserves_existing_notes(self):
        """Test deactivation preserves existing notes."""
        # Create class rep with existing notes
        rep = Representative.objects.create(
            full_name="Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2023,
            is_active=True,
            notes="Previous important note"
        )
        
        # Change to graduated year
        rep.entry_year = 2020
        rep.save()
        
        # Refresh from database
        rep.refresh_from_db()
        
        # Should have both old and new notes
        self.assertIn('Previous important note', rep.notes)
        self.assertIn('Auto-deactivated', rep.notes)
    
    def test_does_not_affect_already_inactive_reps(self):
        """Test signal skips already inactive representatives."""
        # Create inactive graduated class rep
        rep = Representative.objects.create(
            full_name="Inactive Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,  # Graduated
            is_active=False,
            notes="Already deactivated"
        )
        
        initial_notes = rep.notes
        
        # Update something
        rep.full_name = "Updated Student"
        rep.save()
        
        # Refresh from database
        rep.refresh_from_db()
        
        # Notes should be unchanged (signal skipped)
        self.assertEqual(rep.notes, initial_notes)
    
    def test_does_not_affect_active_students(self):
        """Test active students remain active."""
        # Create active class rep
        rep = Representative.objects.create(
            full_name="Active Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2023,  # Still active in 2026
            is_active=True
        )
        
        # Update something
        rep.full_name = "Updated Student"
        rep.save()
        
        # Refresh from database
        rep.refresh_from_db()
        
        # Should still be active
        self.assertTrue(rep.is_active)
    
    @patch('academic_directory.signals.logger')
    def test_logs_deactivation(self, mock_logger):
        """Test deactivation is logged."""
        # Create class rep
        rep = Representative.objects.create(
            full_name="Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2023,
            is_active=True
        )
        
        # Change to graduated year
        rep.entry_year = 2020
        rep.save()
        
        # Wait for signal processing
        rep.refresh_from_db()
        
        # Should log deactivation
        mock_logger.info.assert_called()
        log_call = str(mock_logger.info.call_args)
        self.assertIn('auto-deactivated', log_call.lower())
    
    def test_prevents_infinite_recursion(self):
        """Test signal doesn't trigger itself recursively."""
        # Create graduated class rep
        rep = Representative.objects.create(
            full_name="Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,  # Graduated
            is_active=True
        )
        
        # Update to trigger signal
        rep.full_name = "Updated Student"
        
        # This should not cause infinite recursion
        # (uses update() with update_fields to bypass signal)
        try:
            rep.save()
            success = True
        except RecursionError:
            success = False
        
        self.assertTrue(success)


class SignalRegistrationTest(TestCase):
    """Test that signals are properly registered."""
    
    def test_create_submission_notification_registered(self):
        """Test create_submission_notification is registered."""
        # Get all post_save receivers for Representative
        receivers = signals.post_save.receivers
        
        # Extract receiver functions
        receiver_funcs = []
        for receiver in receivers:
            if len(receiver) > 1:
                func = receiver[1]()
                if func is not None:
                    receiver_funcs.append(func)
        
        # Check our signal is registered
        func_names = [getattr(r, '__name__', '') for r in receiver_funcs]
        self.assertIn('create_submission_notification', func_names)
    
    def test_check_graduation_status_registered(self):
        """Test check_graduation_status is registered."""
        # Get all post_save receivers for Representative
        receivers = signals.post_save.receivers
        
        # Extract receiver functions
        receiver_funcs = []
        for receiver in receivers:
            if len(receiver) > 1:
                func = receiver[1]()
                if func is not None:
                    receiver_funcs.append(func)
        
        # Check our signal is registered
        func_names = [getattr(r, '__name__', '') for r in receiver_funcs]
        self.assertIn('check_graduation_status', func_names)


class SignalEdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
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
    
    def test_multiple_representatives_same_signal(self):
        """Test signal works for multiple representatives."""
        reps = []
        for i in range(5):
            rep = Representative.objects.create(
                full_name=f"Student {i}",
                phone_number=f"0801234567{i}",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2020
            )
            reps.append(rep)
        
        # Each should have a notification
        for rep in reps:
            self.assertTrue(
                SubmissionNotification.objects.filter(representative=rep).exists()
            )
    
    def test_signal_with_minimal_data(self):
        """Test signals work with minimal representative data."""
        # Create with only required fields
        rep = Representative.objects.create(
            full_name="Minimal Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Should still create notification
        self.assertTrue(
            SubmissionNotification.objects.filter(representative=rep).exists()
        )
    
    def test_graduation_check_boundary_year(self):
        """Test graduation check at boundary year."""
        # Create class rep at exact graduation year
        # 2021 entry = graduating in 2026 (5-year program)
        rep = Representative.objects.create(
            full_name="Boundary Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2021,  # Should graduate in 2026
            is_active=True
        )
        
        # Update to trigger check
        rep.full_name = "Updated Student"
        rep.save()
        
        # Refresh
        rep.refresh_from_db()
        
        # Should be deactivated (graduated)
        self.assertFalse(rep.is_active)
    
    def test_notification_signal_with_existing_notification(self):
        """Test signal handles case where notification already exists."""
        # Create representative (creates notification)
        rep = Representative.objects.create(
            full_name="Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Get notification
        notification = SubmissionNotification.objects.get(representative=rep)
        
        # Delete representative (should delete notification via CASCADE)
        rep.delete()
        
        # Notification should be deleted
        self.assertFalse(
            SubmissionNotification.objects.filter(id=notification.id).exists()
        )


class SignalIntegrationTest(TestCase):
    """Test signals in realistic integration scenarios."""
    
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
    
    def test_bulk_create_triggers_signals(self):
        """Test signals fire for bulk_create."""
        # Note: Django's bulk_create doesn't trigger post_save signals
        # This test verifies this expected behavior
        
        reps_data = [
            Representative(
                full_name=f"Student {i}",
                phone_number=f"0801234567{i}",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2020
            )
            for i in range(3)
        ]
        
        Representative.objects.bulk_create(reps_data)
        
        # Bulk create does NOT trigger signals in Django
        # So no notifications should be created
        self.assertEqual(SubmissionNotification.objects.count(), 0)
    
    def test_update_queryset_bypasses_signal(self):
        """Test queryset.update() bypasses post_save signal."""
        rep = Representative.objects.create(
            full_name="Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            is_active=True
        )
        
        # Use queryset.update() (bypasses signal)
        Representative.objects.filter(id=rep.id).update(full_name="Updated via queryset")
        
        # Refresh
        rep.refresh_from_db()
        
        # Should still be active (signal didn't fire)
        # This is expected Django behavior
        self.assertTrue(rep.is_active)
    
    def test_create_then_immediate_update(self):
        """Test creating then immediately updating representative."""
        # Create
        rep = Representative.objects.create(
            full_name="Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2023,
            is_active=True
        )
        
        # Should have notification
        self.assertEqual(SubmissionNotification.objects.count(), 1)
        
        # Update immediately
        rep.full_name = "Updated Student"
        rep.save()
        
        # Should still have only one notification
        self.assertEqual(SubmissionNotification.objects.count(), 1)
        
        # Should still be active
        self.assertTrue(rep.is_active)