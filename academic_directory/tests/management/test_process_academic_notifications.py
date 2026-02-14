# academic_directory/tests/management/test_process_academic_notifications.py
"""
Comprehensive test suite for process_academic_notifications management command.

Test Coverage:
- Command execution
- Background task triggering
- Output messages
- Integration with tasks.py
- No database changes (only triggers background tasks)
- Multiple execution scenarios
- Threading behavior verification
- Edge cases
"""

from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from unittest.mock import patch, call
from academic_directory.models import (
    University, Faculty, Department, Representative, SubmissionNotification
)


class CommandBasicsTest(TestCase):
    """Test basic command execution."""
    
    def test_command_runs_successfully(self):
        """Test command runs without errors."""
        out = StringIO()
        
        with patch('academic_directory.tasks.trigger_process_notifications') as mock_trigger:
            call_command('process_academic_notifications', stdout=out)
            
            # Should call the trigger function
            mock_trigger.assert_called_once()
    
    def test_command_help_text(self):
        """Test command has proper help text."""
        out = StringIO()
        call_command('process_academic_notifications', '--help', stdout=out)
        
        output = out.getvalue()
        self.assertIn('process_academic_notifications', output)
        self.assertIn('pending', output)
        self.assertIn('notification', output)


class TaskTriggeringTest(TestCase):
    """Test that command triggers the correct background task."""
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_triggers_process_notifications(self, mock_trigger):
        """Test command triggers trigger_process_notifications."""
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        # Should call the trigger exactly once
        mock_trigger.assert_called_once_with()
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_multiple_runs_trigger_separately(self, mock_trigger):
        """Test multiple command runs trigger tasks independently."""
        out = StringIO()
        
        # Run three times
        call_command('process_academic_notifications', stdout=out)
        call_command('process_academic_notifications', stdout=out)
        call_command('process_academic_notifications', stdout=out)
        
        # Should be called three times
        self.assertEqual(mock_trigger.call_count, 3)


class OutputMessagesTest(TestCase):
    """Test command output messages."""
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_shows_processing_message(self, mock_trigger):
        """Test command shows processing message."""
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Processing pending submission notifications', output)
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_shows_success_message(self, mock_trigger):
        """Test command shows success message."""
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Notification batch queued', output)
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_output_formatting(self, mock_trigger):
        """Test output has proper formatting."""
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        output = out.getvalue()
        # Should have both messages in order
        self.assertIn('Processing', output)
        self.assertIn('queued', output)


class BackgroundUtilsIntegrationTest(TestCase):
    """Test integration with background_utils.py via tasks.py."""
    
    @patch('jmw.background_utils.process_pending_notifications_async')
    def test_calls_background_utils_function(self, mock_async):
        """Test that tasks.py eventually calls background_utils."""
        out = StringIO()
        
        # Import and call the task directly (simulating command behavior)
        from academic_directory.tasks import trigger_process_notifications
        trigger_process_notifications()
        
        # Should call the async function
        mock_async.assert_called_once()
    
    @patch('jmw.background_utils.Thread')
    def test_uses_threading_for_async(self, mock_thread):
        """Test that background_utils uses threading for non-blocking execution."""
        out = StringIO()
        
        # Mock the thread to prevent actual execution
        mock_thread_instance = mock_thread.return_value
        
        # Import the function
        from jmw.background_utils import process_pending_notifications_async
        
        # Call it
        process_pending_notifications_async()
        
        # Should create a thread
        mock_thread.assert_called_once()
        
        # Thread should be started
        mock_thread_instance.start.assert_called_once()


class DatabaseStateTest(TestCase):
    """Test that command doesn't modify database state directly."""
    
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
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_command_doesnt_modify_notifications(self, mock_trigger):
        """Test command doesn't directly modify notification records."""
        # Record initial state
        initial_is_emailed = self.notification.is_emailed
        initial_is_read = self.notification.is_read
        
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        # Refresh from database
        self.notification.refresh_from_db()
        
        # State should be unchanged (command only triggers background task)
        self.assertEqual(self.notification.is_emailed, initial_is_emailed)
        self.assertEqual(self.notification.is_read, initial_is_read)
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_command_doesnt_delete_notifications(self, mock_trigger):
        """Test command doesn't delete notifications."""
        initial_count = SubmissionNotification.objects.count()
        
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        # Count should remain same
        self.assertEqual(SubmissionNotification.objects.count(), initial_count)
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_command_doesnt_create_notifications(self, mock_trigger):
        """Test command doesn't create new notifications."""
        initial_count = SubmissionNotification.objects.count()
        
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        # Count should remain same
        self.assertEqual(SubmissionNotification.objects.count(), initial_count)


class EdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_command_runs_with_no_notifications(self, mock_trigger):
        """Test command runs successfully even with no notifications."""
        # Ensure no notifications exist
        SubmissionNotification.objects.all().delete()
        
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        # Should still call the trigger
        mock_trigger.assert_called_once()
        
        output = out.getvalue()
        self.assertIn('queued', output)
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_command_runs_with_many_notifications(self, mock_trigger):
        """Test command handles large number of notifications."""
        # Create test data
        university = University.objects.create(
            name="Test University",
            abbreviation="TEST",
            state="ENUGU",
            type="FEDERAL"
        )
        faculty = Faculty.objects.create(
            university=university,
            name="Test Faculty",
            abbreviation="TF"
        )
        department = Department.objects.create(
            faculty=faculty,
            name="Test Department",
            abbreviation="TD"
        )
        
        # Create many notifications
        for i in range(50):
            rep = Representative.objects.create(
                full_name=f"Rep {i}",
                phone_number=f"0801234567{i % 10}",
                department=department,
                faculty=faculty,
                university=university,
                role="CLASS_REP",
                entry_year=2020
            )
            SubmissionNotification.objects.create(representative=rep)
        
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        # Should still work
        mock_trigger.assert_called_once()
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_command_runs_with_all_emailed_notifications(self, mock_trigger):
        """Test command runs when all notifications already emailed."""
        # Create test data
        university = University.objects.create(
            name="Test University",
            abbreviation="TEST",
            state="ENUGU",
            type="FEDERAL"
        )
        faculty = Faculty.objects.create(
            university=university,
            name="Test Faculty",
            abbreviation="TF"
        )
        department = Department.objects.create(
            faculty=faculty,
            name="Test Department",
            abbreviation="TD"
        )
        rep = Representative.objects.create(
            full_name="Test Rep",
            phone_number="08012345678",
            department=department,
            faculty=faculty,
            university=university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # Create notification and mark as emailed
        notification = SubmissionNotification.objects.create(representative=rep)
        notification.mark_as_emailed()
        
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        # Should still trigger (background task will handle filtering)
        mock_trigger.assert_called_once()


class CronSchedulingTest(TestCase):
    """Test command behavior for cron scheduling."""
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_quick_execution_for_cron(self, mock_trigger):
        """Test command executes quickly (suitable for cron)."""
        import time
        
        out = StringIO()
        
        start_time = time.time()
        call_command('process_academic_notifications', stdout=out)
        end_time = time.time()
        
        # Should complete very quickly (< 1 second)
        # since it only triggers background task
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_no_arguments_required(self, mock_trigger):
        """Test command requires no arguments (good for cron)."""
        out = StringIO()
        
        # Should run without any arguments
        try:
            call_command('process_academic_notifications', stdout=out)
            success = True
        except:
            success = False
        
        self.assertTrue(success)
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_silent_execution_possible(self, mock_trigger):
        """Test command can run silently (important for cron)."""
        # Command should work even without stdout
        try:
            call_command('process_academic_notifications')
            success = True
        except:
            success = False
        
        self.assertTrue(success)


class ErrorHandlingTest(TestCase):
    """Test error handling scenarios."""
    
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_handles_trigger_exception(self, mock_trigger):
        """Test command handles exceptions from trigger gracefully."""
        # Make trigger raise an exception
        mock_trigger.side_effect = Exception("Trigger failed")
        
        out = StringIO()
        
        # Should raise the exception (not silently fail)
        with self.assertRaises(Exception):
            call_command('process_academic_notifications', stdout=out)
    
    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_background_task_logs_errors(self, mock_async):
        """Test that background task logs errors properly."""
        # This tests the background_utils error handling
        # The actual logging happens in background_utils.py
        
        # Make the async function raise an error
        mock_async.side_effect = Exception("Background error")
        
        from academic_directory.tasks import trigger_process_notifications
        
        # Should not raise (errors are logged, not raised)
        try:
            trigger_process_notifications()
            # Wait a moment for thread to execute
            import time
            time.sleep(0.1)
            success = True
        except:
            success = False
        
        # Should handle gracefully
        self.assertTrue(success)


class IntegrationScenariosTest(TestCase):
    """Test realistic integration scenarios."""
    
    def setUp(self):
        """Create realistic test data."""
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
    
    @patch('jmw.background_utils.send_email_async')
    @patch('academic_directory.tasks.trigger_process_notifications')
    def test_typical_cron_execution(self, mock_trigger, mock_email):
        """Test typical scheduled execution scenario."""
        # Create some pending notifications
        for i in range(3):
            rep = Representative.objects.create(
                full_name=f"Student {i}",
                phone_number=f"0801234567{i}",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2020
            )
            SubmissionNotification.objects.create(representative=rep)
        
        out = StringIO()
        call_command('process_academic_notifications', stdout=out)
        
        # Should trigger the task
        mock_trigger.assert_called_once()
        
        output = out.getvalue()
        self.assertIn('Processing', output)
        self.assertIn('queued', output)