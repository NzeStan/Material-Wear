"""
Tests for Academic Directory Management Commands.

Tests cover:
- run_graduation_check: Auto-deactivate graduated reps
- send_academic_summary: Send daily summary email
- process_academic_notifications: Batch process pending notifications
- populate_academic_data: (if testable without side effects)
"""
import pytest
from io import StringIO
from django.core.management import call_command
from django.core.management.base import CommandError
from unittest.mock import patch, MagicMock


# =============================================================================
# Run Graduation Check Command Tests
# =============================================================================

class TestRunGraduationCheckCommand:
    """Tests for run_graduation_check management command."""

    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_calls_trigger(self, mock_trigger, db):
        """Test command calls trigger_graduation_check."""
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        mock_trigger.assert_called_once()

    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_outputs_success(self, mock_trigger, db):
        """Test command outputs success message."""
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        output = out.getvalue()
        assert 'queued' in output.lower() or 'success' in output.lower()

    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_outputs_scheduling_message(self, mock_trigger, db):
        """Test command outputs scheduling message."""
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        output = out.getvalue()
        assert 'graduation' in output.lower()


# =============================================================================
# Send Academic Summary Command Tests
# =============================================================================

class TestSendAcademicSummaryCommand:
    """Tests for send_academic_summary management command."""

    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_command_calls_trigger(self, mock_trigger, db):
        """Test command calls trigger_daily_summary."""
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        mock_trigger.assert_called_once()

    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_command_outputs_success(self, mock_trigger, db):
        """Test command outputs success message."""
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        output = out.getvalue()
        assert 'queued' in output.lower() or 'summary' in output.lower()


# =============================================================================
# Process Academic Notifications Command Tests
# =============================================================================

class TestProcessAcademicNotificationsCommand:
    """Tests for process_academic_notifications management command."""

    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_command_calls_trigger(self, mock_trigger, db):
        """Test command calls trigger_process_notifications."""
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        mock_trigger.assert_called_once()

    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_command_outputs_success(self, mock_trigger, db):
        """Test command outputs success message."""
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        output = out.getvalue()
        assert 'queued' in output.lower() or 'notification' in output.lower()


# =============================================================================
# Command Help Tests
# =============================================================================

class TestCommandHelp:
    """Tests for command help text."""

    def test_graduation_check_help(self, db, capsys):
        """Test run_graduation_check has help text."""
        with pytest.raises(SystemExit):
            call_command('run_graduation_check', '--help')
        captured = capsys.readouterr()
        output = captured.out
        assert 'graduation' in output.lower() or 'deactivate' in output.lower()

    def test_send_summary_help(self, db, capsys):
        """Test send_academic_summary has help text."""
        with pytest.raises(SystemExit):
            call_command('send_academic_summary', '--help')
        captured = capsys.readouterr()
        output = captured.out
        assert 'summary' in output.lower() or 'email' in output.lower()

    def test_process_notifications_help(self, db, capsys):
        """Test process_academic_notifications has help text."""
        with pytest.raises(SystemExit):
            call_command('process_academic_notifications', '--help')
        captured = capsys.readouterr()
        output = captured.out
        assert 'notification' in output.lower() or 'batch' in output.lower()


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestCommandErrorHandling:
    """Tests for command error handling."""

    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_graduation_check_handles_error(self, mock_trigger, db):
        """Test graduation check handles errors gracefully."""
        mock_trigger.side_effect = Exception("Task error")

        out = StringIO()
        err = StringIO()

        # Should raise the exception (not silently fail)
        with pytest.raises(Exception, match="Task error"):
            call_command('run_graduation_check', stdout=out, stderr=err)

    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_send_summary_handles_error(self, mock_trigger, db):
        """Test send summary handles errors gracefully."""
        mock_trigger.side_effect = Exception("Email error")

        out = StringIO()
        err = StringIO()

        with pytest.raises(Exception, match="Email error"):
            call_command('send_academic_summary', stdout=out, stderr=err)


# =============================================================================
# Integration Tests
# =============================================================================

class TestCommandIntegration:
    """Integration-like tests for commands."""

    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_graduation_check_full_flow(self, mock_task, db):
        """Test full flow of graduation check command."""
        out = StringIO()
        call_command('run_graduation_check', stdout=out)

        # Task should be called
        mock_task.assert_called_once()

        # Output should indicate success
        output = out.getvalue()
        assert len(output) > 0

    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_send_summary_full_flow(self, mock_async, db):
        """Test full flow of send summary command."""
        out = StringIO()
        call_command('send_academic_summary', stdout=out)

        # Async function should be called
        mock_async.assert_called_once()

    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_process_notifications_full_flow(self, mock_async, db):
        """Test full flow of process notifications command."""
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)

        # Async function should be called
        mock_async.assert_called_once()
