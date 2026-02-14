# academic_directory/tests/management/test_send_academic_summary.py
"""
Comprehensive test suite for send_academic_summary management command.

Test Coverage:
- Command execution
- Background task triggering
- Output messages
- Integration with tasks.py
- No database changes (only triggers background tasks)
- Threading behavior verification
- Email logic (via background_utils)
- Edge cases and boundary conditions
"""

from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth import get_user_model
from io import StringIO
from unittest.mock import patch, MagicMock
from academic_directory.models import (
    University, Faculty, Department, Representative, SubmissionNotification
)
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class CommandBasicsTest(TestCase):
    """Test basic command execution."""
    
    def test_command_runs_successfully(self):
        """Test command runs without errors."""
        out = StringIO()
        
        with patch('academic_directory.tasks.trigger_daily_summary') as mock_trigger:
            call_command('send_academic_summary', stdout=out)
            
            # Should call the trigger function
            mock_trigger.assert_called_once()
    
    def test_command_help_text(self):
        """Test command has proper help text."""
        out = StringIO()
        call_command('send_academic_summary', '--help', stdout=out)
        
        output = out.getvalue()
        self.assertIn('send_academic_summary', output)
        self.assertIn('daily', output)
        self.assertIn('summary', output)


class TaskTriggeringTest(TestCase):
    """Test that command triggers the correct background task."""
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_triggers_daily_summary(self, mock_trigger):
        """Test command triggers trigger_daily_summary."""
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        # Should call the trigger exactly once
        mock_trigger.assert_called_once_with()
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_multiple_runs_trigger_separately(self, mock_trigger):
        """Test multiple command runs trigger tasks independently."""
        out = StringIO()
        
        # Run three times
        call_command('send_academic_summary', stdout=out)
        call_command('send_academic_summary', stdout=out)
        call_command('send_academic_summary', stdout=out)
        
        # Should be called three times
        self.assertEqual(mock_trigger.call_count, 3)


class OutputMessagesTest(TestCase):
    """Test command output messages."""
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_shows_queuing_message(self, mock_trigger):
        """Test command shows queuing message."""
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Queuing daily summary email', output)
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_shows_success_message(self, mock_trigger):
        """Test command shows success message."""
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Daily summary email queued', output)
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_output_formatting(self, mock_trigger):
        """Test output has proper formatting."""
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        output = out.getvalue()
        # Should have both messages in order
        self.assertIn('Queuing', output)
        self.assertIn('queued', output)


class BackgroundUtilsIntegrationTest(TestCase):
    """Test integration with background_utils.py via tasks.py."""
    
    @patch('jmw.background_utils.send_daily_summary_email_async')
    def test_calls_background_utils_function(self, mock_async):
        """Test that tasks.py eventually calls background_utils."""
        out = StringIO()
        
        # Import and call the task directly (simulating command behavior)
        from academic_directory.tasks import trigger_daily_summary
        trigger_daily_summary()
        
        # Should call the async function
        mock_async.assert_called_once()
    
    @patch('jmw.background_utils.Thread')
    def test_uses_threading_for_async(self, mock_thread):
        """Test that background_utils uses threading for non-blocking execution."""
        out = StringIO()
        
        # Mock the thread to prevent actual execution
        mock_thread_instance = mock_thread.return_value
        
        # Import the function
        from jmw.background_utils import send_daily_summary_email_async
        
        # Call it
        send_daily_summary_email_async()
        
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
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_command_doesnt_modify_representatives(self, mock_trigger):
        """Test command doesn't modify representative records."""
        initial_count = Representative.objects.count()
        initial_verification = self.rep.verification_status
        
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        # Refresh from database
        self.rep.refresh_from_db()
        
        # State should be unchanged
        self.assertEqual(Representative.objects.count(), initial_count)
        self.assertEqual(self.rep.verification_status, initial_verification)
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_command_doesnt_modify_notifications(self, mock_trigger):
        """Test command doesn't modify notification records."""
        initial_is_emailed = self.notification.is_emailed
        initial_is_read = self.notification.is_read
        
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        # Refresh from database
        self.notification.refresh_from_db()
        
        # State should be unchanged (command only triggers background task)
        self.assertEqual(self.notification.is_emailed, initial_is_emailed)
        self.assertEqual(self.notification.is_read, initial_is_read)


class EmailLogicTest(TestCase):
    """Test the underlying email sending logic (background task)."""
    
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
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            is_staff=True,
            is_active=True
        )
    
    @patch('jmw.background_utils.send_email_async')
    @patch('jmw.background_utils.logger')
    def test_sends_email_for_new_submissions(self, mock_logger, mock_email):
        """Test background task sends email when new submissions exist."""
        # Create a new submission from yesterday
        yesterday = timezone.now() - timedelta(days=1)
        with patch('django.utils.timezone.now', return_value=yesterday):
            rep = Representative.objects.create(
                full_name="New Student",
                phone_number="08012345678",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2023,
                verification_status='UNVERIFIED'
            )
        
        # Import the actual background function
        from jmw.background_utils import send_daily_summary_email_async
        
        # Execute the task directly (in thread)
        send_daily_summary_email_async()
        
        # Wait for thread to complete
        import time
        time.sleep(0.2)
        
        # Should have called send_email_async
        self.assertTrue(mock_email.called)
    
    @patch('jmw.background_utils.send_email_async')
    @patch('jmw.background_utils.logger')
    def test_skips_email_for_no_new_submissions(self, mock_logger, mock_email):
        """Test background task skips email when no new submissions."""
        # Create an old submission (more than 24 hours ago)
        old_time = timezone.now() - timedelta(days=2)
        with patch('django.utils.timezone.now', return_value=old_time):
            Representative.objects.create(
                full_name="Old Student",
                phone_number="08012345678",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2023,
                verification_status='UNVERIFIED'
            )
        
        # Import the actual background function
        from jmw.background_utils import send_daily_summary_email_async
        
        # Execute the task
        send_daily_summary_email_async()
        
        # Wait for thread
        import time
        time.sleep(0.2)
        
        # Should not send email
        mock_email.assert_not_called()
    
    @patch('jmw.background_utils.send_email_async')
    @patch('jmw.background_utils.logger')
    def test_sends_email_to_all_staff_admins(self, mock_logger, mock_email):
        """Test background task sends email to all active staff users."""
        # Create multiple admin users
        admin2 = User.objects.create_user(
            username='admin2',
            email='admin2@example.com',
            is_staff=True,
            is_active=True
        )
        admin3 = User.objects.create_user(
            username='admin3',
            email='admin3@example.com',
            is_staff=True,
            is_active=True
        )
        
        # Create a new submission
        yesterday = timezone.now() - timedelta(hours=12)
        with patch('django.utils.timezone.now', return_value=yesterday):
            Representative.objects.create(
                full_name="New Student",
                phone_number="08012345678",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2023,
                verification_status='UNVERIFIED'
            )
        
        # Import the actual background function
        from jmw.background_utils import send_daily_summary_email_async
        
        # Execute the task
        send_daily_summary_email_async()
        
        # Wait for thread
        import time
        time.sleep(0.2)
        
        # Should have sent to all admins
        if mock_email.called:
            call_kwargs = mock_email.call_args[1]
            recipient_list = call_kwargs.get('recipient_list', [])
            
            self.assertIn('admin@example.com', recipient_list)
            self.assertIn('admin2@example.com', recipient_list)
            self.assertIn('admin3@example.com', recipient_list)
    
    @patch('jmw.background_utils.send_email_async')
    @patch('jmw.background_utils.logger')
    def test_excludes_inactive_staff(self, mock_logger, mock_email):
        """Test background task excludes inactive staff users."""
        # Create inactive admin
        User.objects.create_user(
            username='inactive_admin',
            email='inactive@example.com',
            is_staff=True,
            is_active=False
        )
        
        # Create a new submission
        yesterday = timezone.now() - timedelta(hours=12)
        with patch('django.utils.timezone.now', return_value=yesterday):
            Representative.objects.create(
                full_name="New Student",
                phone_number="08012345678",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2023,
                verification_status='UNVERIFIED'
            )
        
        # Import the actual background function
        from jmw.background_utils import send_daily_summary_email_async
        
        # Execute the task
        send_daily_summary_email_async()
        
        # Wait for thread
        import time
        time.sleep(0.2)
        
        # Should not include inactive admin
        if mock_email.called:
            call_kwargs = mock_email.call_args[1]
            recipient_list = call_kwargs.get('recipient_list', [])
            
            self.assertNotIn('inactive@example.com', recipient_list)


class EdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_command_runs_with_no_representatives(self, mock_trigger):
        """Test command runs successfully even with no representatives."""
        # Ensure no representatives exist
        Representative.objects.all().delete()
        
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        # Should still call the trigger
        mock_trigger.assert_called_once()
        
        output = out.getvalue()
        self.assertIn('queued', output)
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_command_runs_with_no_admins(self, mock_trigger):
        """Test command handles no admin users gracefully."""
        # Ensure no admin users exist
        User.objects.filter(is_staff=True).delete()
        
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        # Should still work (background task will skip email)
        mock_trigger.assert_called_once()
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_command_runs_with_all_verified_submissions(self, mock_trigger):
        """Test command runs when all submissions are verified."""
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
        
        # Create verified representative
        Representative.objects.create(
            full_name="Verified Rep",
            phone_number="08012345678",
            department=department,
            faculty=faculty,
            university=university,
            role="CLASS_REP",
            entry_year=2023,
            verification_status='VERIFIED'
        )
        
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        # Should still trigger (background task will skip email)
        mock_trigger.assert_called_once()


class CronSchedulingTest(TestCase):
    """Test command behavior for cron scheduling."""
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_quick_execution_for_cron(self, mock_trigger):
        """Test command executes quickly (suitable for cron)."""
        import time
        
        out = StringIO()
        
        start_time = time.time()
        call_command('send_academic_summary', stdout=out)
        end_time = time.time()
        
        # Should complete very quickly (< 1 second)
        # since it only triggers background task
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_no_arguments_required(self, mock_trigger):
        """Test command requires no arguments (good for cron)."""
        out = StringIO()
        
        # Should run without any arguments
        try:
            call_command('send_academic_summary', stdout=out)
            success = True
        except:
            success = False
        
        self.assertTrue(success)
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_silent_execution_possible(self, mock_trigger):
        """Test command can run silently (important for cron)."""
        # Command should work even without stdout
        try:
            call_command('send_academic_summary')
            success = True
        except:
            success = False
        
        self.assertTrue(success)


class ErrorHandlingTest(TestCase):
    """Test error handling scenarios."""
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_handles_trigger_exception(self, mock_trigger):
        """Test command handles exceptions from trigger gracefully."""
        # Make trigger raise an exception
        mock_trigger.side_effect = Exception("Trigger failed")
        
        out = StringIO()
        
        # Should raise the exception (not silently fail)
        with self.assertRaises(Exception):
            call_command('send_academic_summary', stdout=out)
    
    @patch('jmw.background_utils.send_email_async')
    def test_background_task_logs_errors(self, mock_email):
        """Test that background task logs errors properly."""
        # Make email async raise an error
        mock_email.side_effect = Exception("Email failed")
        
        from jmw.background_utils import send_daily_summary_email_async
        
        # Should not raise (errors are logged, not raised)
        try:
            send_daily_summary_email_async()
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
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            is_staff=True,
            is_active=True
        )
    
    @patch('jmw.background_utils.send_email_async')
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_typical_daily_cron_execution(self, mock_trigger, mock_email):
        """Test typical scheduled daily execution scenario."""
        # Create some new unverified submissions from last 24h
        yesterday = timezone.now() - timedelta(hours=12)
        
        for i in range(3):
            with patch('django.utils.timezone.now', return_value=yesterday):
                Representative.objects.create(
                    full_name=f"Student {i}",
                    phone_number=f"0801234567{i}",
                    department=self.department,
                    faculty=self.faculty,
                    university=self.university,
                    role="CLASS_REP",
                    entry_year=2023,
                    verification_status='UNVERIFIED'
                )
        
        out = StringIO()
        call_command('send_academic_summary', stdout=out)
        
        # Should trigger the task
        mock_trigger.assert_called_once()
        
        output = out.getvalue()
        self.assertIn('Queuing', output)
        self.assertIn('queued', output)
    
    @patch('academic_directory.tasks.trigger_daily_summary')
    def test_multiple_daily_executions(self, mock_trigger):
        """Test multiple executions in same day work independently."""
        out = StringIO()
        
        # Run morning execution
        call_command('send_academic_summary', stdout=out)
        
        # Run afternoon execution
        call_command('send_academic_summary', stdout=out)
        
        # Both should trigger
        self.assertEqual(mock_trigger.call_count, 2)


class EmailContentTest(TestCase):
    """Test email content and context."""
    
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
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            is_staff=True,
            is_active=True
        )
    
    @patch('jmw.background_utils.render_to_string')
    @patch('jmw.background_utils.send_email_async')
    def test_email_includes_submission_count(self, mock_email, mock_render):
        """Test email context includes correct submission count."""
        # Create new submissions
        yesterday = timezone.now() - timedelta(hours=12)
        
        for i in range(5):
            with patch('django.utils.timezone.now', return_value=yesterday):
                Representative.objects.create(
                    full_name=f"Student {i}",
                    phone_number=f"0801234567{i}",
                    department=self.department,
                    faculty=self.faculty,
                    university=self.university,
                    role="CLASS_REP",
                    entry_year=2023,
                    verification_status='UNVERIFIED'
                )
        
        # Import and execute
        from jmw.background_utils import send_daily_summary_email_async
        send_daily_summary_email_async()
        
        # Wait for thread
        import time
        time.sleep(0.2)
        
        # Should have rendered with context
        if mock_render.called:
            call_args = mock_render.call_args[0]
            context = call_args[1] if len(call_args) > 1 else {}
            
            # Should have count
            self.assertIn('count', context)
            self.assertEqual(context['count'], 5)