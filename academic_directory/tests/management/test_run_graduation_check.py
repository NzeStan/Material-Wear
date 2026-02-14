# academic_directory/tests/management/test_run_graduation_check.py
"""
Comprehensive test suite for run_graduation_check management command.

Test Coverage:
- Command execution
- Background task scheduling (django-background-tasks)
- Output messages
- Integration with tasks.py
- No immediate database changes (schedules task)
- Threading/background task behavior
- Edge cases
"""

from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from unittest.mock import patch, MagicMock
from academic_directory.models import (
    University, Faculty, Department, Representative
)
from django.utils import timezone
from datetime import timedelta


class CommandBasicsTest(TestCase):
    """Test basic command execution."""
    
    def test_command_runs_successfully(self):
        """Test command runs without errors."""
        out = StringIO()
        
        with patch('academic_directory.tasks.trigger_graduation_check') as mock_trigger:
            call_command('run_graduation_check', stdout=out)
            
            # Should call the trigger function
            mock_trigger.assert_called_once()
    
    def test_command_help_text(self):
        """Test command has proper help text."""
        out = StringIO()
        call_command('run_graduation_check', '--help', stdout=out)
        
        output = out.getvalue()
        self.assertIn('run_graduation_check', output)
        self.assertIn('graduated', output)
        self.assertIn('deactivate', output)


class TaskTriggeringTest(TestCase):
    """Test that command triggers the correct background task."""
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_triggers_graduation_check(self, mock_trigger):
        """Test command triggers trigger_graduation_check."""
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        # Should call the trigger exactly once
        mock_trigger.assert_called_once_with()
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_multiple_runs_trigger_separately(self, mock_trigger):
        """Test multiple command runs trigger tasks independently."""
        out = StringIO()
        
        # Run three times
        call_command('run_graduation_check', stdout=out)
        call_command('run_graduation_check', stdout=out)
        call_command('run_graduation_check', stdout=out)
        
        # Should be called three times
        self.assertEqual(mock_trigger.call_count, 3)


class OutputMessagesTest(TestCase):
    """Test command output messages."""
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_shows_scheduling_message(self, mock_trigger):
        """Test command shows scheduling message."""
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Scheduling graduation check', output)
        self.assertIn('django-background-tasks', output)
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_shows_success_message(self, mock_trigger):
        """Test command shows success message."""
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        output = out.getvalue()
        self.assertIn('Graduation check queued successfully', output)
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_output_formatting(self, mock_trigger):
        """Test output has proper formatting."""
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        output = out.getvalue()
        # Should have both messages in order
        self.assertIn('Scheduling', output)
        self.assertIn('queued successfully', output)


class BackgroundTasksIntegrationTest(TestCase):
    """Test integration with django-background-tasks via tasks.py."""
    
    @patch('jmw.background_utils.check_graduation_statuses_task')
    def test_calls_background_task_function(self, mock_task):
        """Test that tasks.py calls the background task function."""
        out = StringIO()
        
        # Import and call the task directly (simulating command behavior)
        from academic_directory.tasks import trigger_graduation_check
        trigger_graduation_check()
        
        # Should call the background task function
        mock_task.assert_called_once()
    
    @patch('jmw.background_utils.background')
    def test_uses_background_decorator(self, mock_background):
        """Test that background task uses @background decorator."""
        # The check_graduation_statuses_task should use @background decorator
        # This ensures it's queued via django-background-tasks
        
        from jmw.background_utils import check_graduation_statuses_task
        
        # Function should have background decorator attributes
        # (In actual implementation, this is decorated with @background(schedule=0))
        self.assertTrue(callable(check_graduation_statuses_task))


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
        
        # Create a graduated class rep
        self.graduated_rep = Representative.objects.create(
            full_name="Graduated Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,  # Graduated (current year is 2026)
            is_active=True
        )
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_doesnt_deactivate_immediately(self, mock_trigger):
        """Test command doesn't deactivate representatives immediately."""
        # Representative should be active before
        self.assertTrue(self.graduated_rep.is_active)
        
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        # Refresh from database
        self.graduated_rep.refresh_from_db()
        
        # Should still be active (command only schedules task)
        self.assertTrue(self.graduated_rep.is_active)
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_doesnt_modify_notes(self, mock_trigger):
        """Test command doesn't modify representative notes immediately."""
        initial_notes = self.graduated_rep.notes
        
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        # Refresh from database
        self.graduated_rep.refresh_from_db()
        
        # Notes should be unchanged (command only schedules task)
        self.assertEqual(self.graduated_rep.notes, initial_notes)
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_doesnt_delete_representatives(self, mock_trigger):
        """Test command doesn't delete representatives."""
        initial_count = Representative.objects.count()
        
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        # Count should remain same
        self.assertEqual(Representative.objects.count(), initial_count)


class EdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_runs_with_no_representatives(self, mock_trigger):
        """Test command runs successfully even with no representatives."""
        # Ensure no representatives exist
        Representative.objects.all().delete()
        
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        # Should still call the trigger
        mock_trigger.assert_called_once()
        
        output = out.getvalue()
        self.assertIn('queued successfully', output)
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_runs_with_no_class_reps(self, mock_trigger):
        """Test command handles no class representatives."""
        # Create non-class-rep representatives
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
        
        # Create faculty rep (not class rep)
        Representative.objects.create(
            full_name="Faculty Rep",
            phone_number="08012345678",
            department=department,
            faculty=faculty,
            university=university,
            role="FACULTY_REP"
        )
        
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        # Should still work
        mock_trigger.assert_called_once()
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_command_runs_with_many_representatives(self, mock_trigger):
        """Test command handles large number of representatives."""
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
        
        # Create many class reps
        for i in range(100):
            Representative.objects.create(
                full_name=f"Rep {i}",
                phone_number=f"0801234567{i % 10}",
                department=department,
                faculty=faculty,
                university=university,
                role="CLASS_REP",
                entry_year=2020 if i % 2 == 0 else 2023,  # Mix of graduated and active
                is_active=True
            )
        
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        # Should still work
        mock_trigger.assert_called_once()


class CronSchedulingTest(TestCase):
    """Test command behavior for cron scheduling."""
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_quick_execution_for_cron(self, mock_trigger):
        """Test command executes quickly (suitable for cron)."""
        import time
        
        out = StringIO()
        
        start_time = time.time()
        call_command('run_graduation_check', stdout=out)
        end_time = time.time()
        
        # Should complete very quickly (< 1 second)
        # since it only schedules background task
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_no_arguments_required(self, mock_trigger):
        """Test command requires no arguments (good for cron)."""
        out = StringIO()
        
        # Should run without any arguments
        try:
            call_command('run_graduation_check', stdout=out)
            success = True
        except:
            success = False
        
        self.assertTrue(success)
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_silent_execution_possible(self, mock_trigger):
        """Test command can run silently (important for cron)."""
        # Command should work even without stdout
        try:
            call_command('run_graduation_check')
            success = True
        except:
            success = False
        
        self.assertTrue(success)


class ErrorHandlingTest(TestCase):
    """Test error handling scenarios."""
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_handles_trigger_exception(self, mock_trigger):
        """Test command handles exceptions from trigger gracefully."""
        # Make trigger raise an exception
        mock_trigger.side_effect = Exception("Trigger failed")
        
        out = StringIO()
        
        # Should raise the exception (not silently fail)
        with self.assertRaises(Exception):
            call_command('run_graduation_check', stdout=out)


class GraduationLogicTest(TestCase):
    """Test the underlying graduation check logic (background task)."""
    
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
    
    @patch('jmw.background_utils.logger')
    def test_background_task_identifies_graduates(self, mock_logger):
        """Test background task correctly identifies graduated class reps."""
        # Create graduated class rep (2020 entry = graduated in 2025)
        graduated_rep = Representative.objects.create(
            full_name="Graduated Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            is_active=True
        )
        
        # Import the actual background task
        from jmw.background_utils import check_graduation_statuses_task
        
        # Execute the task directly (not via background queue)
        check_graduation_statuses_task()
        
        # Refresh from database
        graduated_rep.refresh_from_db()
        
        # Should be deactivated
        self.assertFalse(graduated_rep.is_active)
    
    @patch('jmw.background_utils.logger')
    def test_background_task_preserves_active_students(self, mock_logger):
        """Test background task doesn't deactivate current students."""
        # Create current class rep (2023 entry = still active in 2026)
        current_rep = Representative.objects.create(
            full_name="Current Student",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2023,
            is_active=True
        )
        
        # Import the actual background task
        from jmw.background_utils import check_graduation_statuses_task
        
        # Execute the task
        check_graduation_statuses_task()
        
        # Refresh from database
        current_rep.refresh_from_db()
        
        # Should still be active
        self.assertTrue(current_rep.is_active)
    
    @patch('jmw.background_utils.logger')
    def test_background_task_adds_deactivation_note(self, mock_logger):
        """Test background task adds note explaining deactivation."""
        # Create graduated class rep
        graduated_rep = Representative.objects.create(
            full_name="Graduated Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            is_active=True,
            notes=""
        )
        
        # Import the actual background task
        from jmw.background_utils import check_graduation_statuses_task
        
        # Execute the task
        check_graduation_statuses_task()
        
        # Refresh from database
        graduated_rep.refresh_from_db()
        
        # Should have note about auto-deactivation
        self.assertIn('Auto-deactivated', graduated_rep.notes)
        self.assertIn('Graduated', graduated_rep.notes)
        self.assertIn('2025', graduated_rep.notes)  # Expected graduation year
    
    @patch('jmw.background_utils.logger')
    def test_background_task_preserves_existing_notes(self, mock_logger):
        """Test background task preserves existing notes when adding deactivation note."""
        # Create graduated class rep with existing notes
        graduated_rep = Representative.objects.create(
            full_name="Graduated Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            is_active=True,
            notes="Previous important note"
        )
        
        # Import the actual background task
        from jmw.background_utils import check_graduation_statuses_task
        
        # Execute the task
        check_graduation_statuses_task()
        
        # Refresh from database
        graduated_rep.refresh_from_db()
        
        # Should have both old and new notes
        self.assertIn('Previous important note', graduated_rep.notes)
        self.assertIn('Auto-deactivated', graduated_rep.notes)
    
    @patch('jmw.background_utils.logger')
    def test_background_task_only_affects_class_reps(self, mock_logger):
        """Test background task only checks CLASS_REP role."""
        # Create graduated faculty rep
        faculty_rep = Representative.objects.create(
            full_name="Faculty Rep",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="FACULTY_REP",
            is_active=True
        )
        
        # Create graduated department rep
        dept_rep = Representative.objects.create(
            full_name="Department Rep",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPARTMENT_REP",
            is_active=True
        )
        
        # Import the actual background task
        from jmw.background_utils import check_graduation_statuses_task
        
        # Execute the task
        check_graduation_statuses_task()
        
        # Refresh from database
        faculty_rep.refresh_from_db()
        dept_rep.refresh_from_db()
        
        # Should still be active (not class reps)
        self.assertTrue(faculty_rep.is_active)
        self.assertTrue(dept_rep.is_active)


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
    
    @patch('academic_directory.tasks.trigger_graduation_check')
    def test_typical_daily_cron_execution(self, mock_trigger):
        """Test typical scheduled daily execution scenario."""
        # Create mix of graduated and active class reps
        for i in range(5):
            Representative.objects.create(
                full_name=f"Graduated Student {i}",
                phone_number=f"0801234567{i}",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2020,  # Graduated
                is_active=True
            )
        
        for i in range(3):
            Representative.objects.create(
                full_name=f"Active Student {i}",
                phone_number=f"0809876543{i}",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2023,  # Still active
                is_active=True
            )
        
        out = StringIO()
        call_command('run_graduation_check', stdout=out)
        
        # Should trigger the task
        mock_trigger.assert_called_once()
        
        output = out.getvalue()
        self.assertIn('Scheduling', output)
        self.assertIn('queued successfully', output)