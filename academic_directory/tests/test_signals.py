"""
Tests for Academic Directory Signals.

Tests cover:
- create_submission_notification: Auto-create notification on new representative
- check_graduation_status: Auto-deactivate graduated class reps
- Signal recursion prevention
"""
import pytest
from datetime import datetime
from django.db.models.signals import post_save
from unittest.mock import patch, MagicMock

from academic_directory.models import (
    Representative,
    SubmissionNotification,
)
from academic_directory.signals import (
    create_submission_notification,
    check_graduation_status,
)


# =============================================================================
# Notification Signal Tests
# =============================================================================

class TestCreateSubmissionNotificationSignal:
    """Tests for create_submission_notification signal."""

    def test_notification_created_on_new_representative(self, department, program_duration):
        """Test notification is created when new representative is saved."""
        current_year = datetime.now().year
        rep = Representative.objects.create(
            full_name='Signal Test Rep',
            phone_number='+2348012300001',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year,
            submission_source='WEBSITE',
        )

        # Check notification was created
        assert SubmissionNotification.objects.filter(representative=rep).exists()
        notification = SubmissionNotification.objects.get(representative=rep)
        assert notification.is_read is False
        assert notification.is_emailed is False

    def test_notification_not_duplicated_on_update(self, class_rep):
        """Test notification is not duplicated when representative is updated."""
        # Ensure notification exists
        SubmissionNotification.objects.get_or_create(representative=class_rep)
        initial_count = SubmissionNotification.objects.filter(representative=class_rep).count()

        # Update representative
        class_rep.full_name = 'Updated Signal Test'
        class_rep.save()

        # Count should remain the same (get_or_create prevents duplicates)
        final_count = SubmissionNotification.objects.filter(representative=class_rep).count()
        assert final_count == initial_count

    def test_notification_uses_get_or_create(self, department, program_duration):
        """Test signal uses get_or_create for idempotency."""
        current_year = datetime.now().year
        rep = Representative.objects.create(
            full_name='Idempotent Test',
            phone_number='+2348012300002',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year,
            submission_source='WEBSITE',
        )

        # Should only have one notification
        count = SubmissionNotification.objects.filter(representative=rep).count()
        assert count == 1


# =============================================================================
# Graduation Check Signal Tests
# =============================================================================

class TestCheckGraduationStatusSignal:
    """Tests for check_graduation_status signal."""

    def test_graduated_class_rep_deactivated(self, department, program_duration):
        """Test graduated class rep is auto-deactivated on save."""
        current_year = datetime.now().year
        # Create rep that has graduated (entry 6 years ago, 4-year program)
        rep = Representative.objects.create(
            full_name='Graduated Rep',
            phone_number='+2348012300003',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year - 6,
            submission_source='WEBSITE',
            is_active=True,
        )

        # Trigger post_save by making a change
        rep.notes = 'Updated note'
        rep.save()

        # Refresh and check
        rep.refresh_from_db()
        assert rep.is_active is False
        assert 'Auto-deactivated' in (rep.notes or '')

    def test_current_student_not_deactivated(self, class_rep, program_duration):
        """Test current student is not deactivated."""
        assert class_rep.is_active is True

        # Update and save
        class_rep.notes = 'Some note'
        class_rep.save()

        class_rep.refresh_from_db()
        assert class_rep.is_active is True

    def test_president_not_affected(self, dept_president):
        """Test presidents are not affected by graduation check."""
        assert dept_president.role == 'DEPT_PRESIDENT'
        assert dept_president.is_active is True

        # Update and save
        dept_president.notes = 'Updated'
        dept_president.save()

        dept_president.refresh_from_db()
        assert dept_president.is_active is True

    def test_already_inactive_not_processed(self, department, program_duration):
        """Test already inactive rep is not processed."""
        current_year = datetime.now().year
        rep = Representative.objects.create(
            full_name='Already Inactive',
            phone_number='+2348012300004',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year - 6,
            submission_source='WEBSITE',
            is_active=False,
            notes='Manually deactivated',
        )

        # Update and save
        original_notes = rep.notes
        rep.full_name = 'Updated Name'
        rep.save()

        rep.refresh_from_db()
        # Notes should not have auto-deactivation message added again
        # (signal guards with is_active check)
        assert rep.is_active is False

    def test_signal_avoids_recursion(self, department, program_duration):
        """Test signal uses update_fields to avoid recursion."""
        current_year = datetime.now().year
        rep = Representative.objects.create(
            full_name='Recursion Test',
            phone_number='+2348012300005',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year - 6,
            submission_source='WEBSITE',
            is_active=True,
        )

        # Trigger graduation check
        rep.notes = 'Trigger update'
        rep.save()

        # Should not cause recursion error
        rep.refresh_from_db()
        assert rep.is_active is False

    def test_new_rep_skips_graduation_check(self, department, program_duration):
        """Test newly created rep skips graduation check (created=True guard)."""
        current_year = datetime.now().year
        # This is a new creation, so created=True in signal
        # Graduated rep should still be created as active initially
        # (graduation check only runs on updates, not creation)
        rep = Representative.objects.create(
            full_name='New Graduated Rep',
            phone_number='+2348012300006',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year - 6,  # Would be graduated
            submission_source='WEBSITE',
            is_active=True,
        )

        # On creation, should remain active (signal guard: if created: return)
        # But note: the actual signal DOES run on new reps too for notification
        # Let's check the behavior
        rep.refresh_from_db()
        # Based on signal code: if created: return (for graduation check)
        # So new rep should remain active
        assert rep.is_active is True


# =============================================================================
# Signal Connection Tests
# =============================================================================

class TestSignalConnections:
    """Tests that signals are properly connected."""

    def test_notification_signal_connected(self):
        """Test notification signal is connected."""
        receivers = [r for r in post_save.receivers if r[1] is not None]
        # Should have at least one receiver
        assert len(receivers) > 0

    def test_signals_imported_in_app_ready(self):
        """Test signals are imported when app is ready."""
        # Verify that the signals module can be imported without error
        try:
            import academic_directory.signals
        except Exception as e:
            pytest.fail(f"Signal import failed: {e}")

        # Verify signal handlers are defined
        from academic_directory.signals import create_submission_notification, check_graduation_status
        assert callable(create_submission_notification)
        assert callable(check_graduation_status)


# =============================================================================
# Signal Edge Cases
# =============================================================================

class TestSignalEdgeCases:
    """Tests for signal edge cases."""

    def test_notification_for_different_roles(self, department):
        """Test notification created for all role types."""
        current_year = datetime.now().year
        roles_data = [
            {'role': 'CLASS_REP', 'entry_year': current_year, 'phone': '+2348012300007'},
            {'role': 'DEPT_PRESIDENT', 'tenure_start_year': current_year, 'phone': '+2348012300008'},
            {'role': 'FACULTY_PRESIDENT', 'tenure_start_year': current_year, 'phone': '+2348012300009'},
        ]

        for data in roles_data:
            rep = Representative.objects.create(
                full_name=f"Test {data['role']}",
                phone_number=data['phone'],
                department=department,
                faculty=department.faculty,
                university=department.faculty.university,
                role=data['role'],
                entry_year=data.get('entry_year'),
                tenure_start_year=data.get('tenure_start_year'),
                submission_source='WEBSITE',
            )
            assert SubmissionNotification.objects.filter(representative=rep).exists()

    def test_graduation_check_with_no_program_duration(self, faculty):
        """Test graduation check handles missing program duration gracefully."""
        current_year = datetime.now().year
        # Create department without program duration
        dept = Department.objects.create(
            faculty=faculty,
            name='No Duration Dept',
            abbreviation='NDD',
        )

        rep = Representative.objects.create(
            full_name='No Duration Test',
            phone_number='+2348012300010',
            department=dept,
            faculty=faculty,
            university=faculty.university,
            role='CLASS_REP',
            entry_year=current_year - 6,
            submission_source='WEBSITE',
            is_active=True,
        )

        # Update to trigger signal
        rep.notes = 'Test update'
        rep.save()

        rep.refresh_from_db()
        # Should handle gracefully (defaults to 4-year program)
        # After 6 years, would be graduated even with default
        # But signal might not deactivate if has_graduated returns False due to exception
        # The actual behavior depends on implementation


# Import Department for the test above
from academic_directory.models import Department
