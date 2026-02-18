"""
Tests for Academic Directory Background Tasks.

Tests cover:
- Task trigger functions
- Integration with background_utils
- Error handling
"""
import pytest
from unittest.mock import patch, MagicMock

from academic_directory.tasks import (
    trigger_new_submission_email,
    trigger_bulk_verification_email,
    trigger_daily_summary,
    trigger_process_notifications,
    trigger_graduation_check,
)


# =============================================================================
# Task Trigger Tests
# =============================================================================

class TestTriggerNewSubmissionEmail:
    """Tests for trigger_new_submission_email."""

    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_calls_async_function(self, mock_async, class_rep):
        """Test trigger calls the async function."""
        trigger_new_submission_email(class_rep.id)
        mock_async.assert_called_once_with(class_rep.id)

    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_handles_uuid(self, mock_async, class_rep):
        """Test trigger handles UUID representative_id."""
        trigger_new_submission_email(class_rep.id)
        # Should pass the UUID through
        assert mock_async.called


class TestTriggerBulkVerificationEmail:
    """Tests for trigger_bulk_verification_email."""

    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_calls_async_function(self, mock_async, multiple_representatives, admin_user):
        """Test trigger calls the async function."""
        ids = [rep.id for rep in multiple_representatives[:3]]
        trigger_bulk_verification_email(ids, admin_user.id)
        mock_async.assert_called_once_with(ids, admin_user.id)

    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_empty_ids_still_calls(self, mock_async, admin_user):
        """Test trigger still calls async even with empty list."""
        trigger_bulk_verification_email([], admin_user.id)
        mock_async.assert_called_once_with([], admin_user.id)


class TestTriggerDailySummary:
    """Tests for trigger_daily_summary."""

    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_calls_async_function(self, mock_async):
        """Test trigger calls the async function."""
        trigger_daily_summary()
        mock_async.assert_called_once()

    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_no_arguments(self, mock_async):
        """Test trigger is called without arguments."""
        trigger_daily_summary()
        mock_async.assert_called_once_with()


class TestTriggerProcessNotifications:
    """Tests for trigger_process_notifications."""

    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_calls_async_function(self, mock_async):
        """Test trigger calls the async function."""
        trigger_process_notifications()
        mock_async.assert_called_once()

    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_no_arguments(self, mock_async):
        """Test trigger is called without arguments."""
        trigger_process_notifications()
        mock_async.assert_called_once_with()


class TestTriggerGraduationCheck:
    """Tests for trigger_graduation_check."""

    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_calls_task_function(self, mock_task):
        """Test trigger calls the task function."""
        trigger_graduation_check()
        mock_task.assert_called_once()

    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_no_arguments(self, mock_task):
        """Test trigger is called without arguments."""
        trigger_graduation_check()
        mock_task.assert_called_once_with()


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestTaskErrorHandling:
    """Tests for task error handling."""

    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_submission_email_exception_propagates(self, mock_async):
        """Test exceptions from async function propagate."""
        mock_async.side_effect = Exception("Email error")

        with pytest.raises(Exception, match="Email error"):
            trigger_new_submission_email('some-id')

    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_bulk_email_exception_propagates(self, mock_async, admin_user):
        """Test exceptions from bulk email propagate."""
        mock_async.side_effect = Exception("Bulk email error")

        with pytest.raises(Exception, match="Bulk email error"):
            trigger_bulk_verification_email([1, 2, 3], admin_user.id)


# =============================================================================
# Integration-like Tests (with mocked external)
# =============================================================================

class TestTaskIntegration:
    """Integration-like tests for tasks."""

    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_full_workflow_new_submission(self, mock_async, class_rep):
        """Test full workflow for new submission email."""
        # This simulates what happens when a new rep is created
        # and we trigger the email task
        representative_id = class_rep.id

        trigger_new_submission_email(representative_id)

        # Verify the async function was called with correct ID
        mock_async.assert_called_once()
        called_id = mock_async.call_args[0][0]
        assert called_id == representative_id

    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_full_workflow_bulk_verify(self, mock_async, multiple_representatives, admin_user):
        """Test full workflow for bulk verification."""
        rep_ids = [rep.id for rep in multiple_representatives[:2]]
        verifier_id = admin_user.id

        trigger_bulk_verification_email(rep_ids, verifier_id)

        mock_async.assert_called_once()
        called_rep_ids = mock_async.call_args[0][0]
        called_verifier_id = mock_async.call_args[0][1]
        assert called_rep_ids == rep_ids
        assert called_verifier_id == verifier_id
