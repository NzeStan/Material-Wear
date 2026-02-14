# academic_directory/tests/test_tasks.py
"""
Comprehensive test suite for academic_directory tasks module.

Test Coverage:
- trigger_new_submission_email
- trigger_bulk_verification_email
- trigger_daily_summary
- trigger_process_notifications
- trigger_graduation_check
- Integration with jmw/background_utils.py
- Error handling
- Multiple invocation scenarios
"""

from django.test import TestCase
from unittest.mock import patch, call, Mock
from academic_directory.tasks import (
    trigger_new_submission_email,
    trigger_bulk_verification_email,
    trigger_daily_summary,
    trigger_process_notifications,
    trigger_graduation_check
)


class TriggerNewSubmissionEmailTest(TestCase):
    """Test trigger_new_submission_email function."""
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_calls_background_utils_function(self, mock_async):
        """Test function calls send_new_submission_email_async."""
        representative_id = 123
        
        trigger_new_submission_email(representative_id)
        
        # Should call the async function with representative_id
        mock_async.assert_called_once_with(representative_id)
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_passes_correct_representative_id(self, mock_async):
        """Test correct representative_id is passed."""
        representative_id = 456
        
        trigger_new_submission_email(representative_id)
        
        # Should pass exact ID
        call_args = mock_async.call_args[0]
        self.assertEqual(call_args[0], representative_id)
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_multiple_invocations(self, mock_async):
        """Test multiple calls work independently."""
        # Call multiple times
        trigger_new_submission_email(1)
        trigger_new_submission_email(2)
        trigger_new_submission_email(3)
        
        # Should be called three times
        self.assertEqual(mock_async.call_count, 3)
        
        # With different IDs
        calls = [call(1), call(2), call(3)]
        mock_async.assert_has_calls(calls)
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_handles_exception_from_background_utils(self, mock_async):
        """Test exception from background_utils is propagated."""
        mock_async.side_effect = Exception("Background task failed")
        
        with self.assertRaises(Exception):
            trigger_new_submission_email(123)


class TriggerBulkVerificationEmailTest(TestCase):
    """Test trigger_bulk_verification_email function."""
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_calls_background_utils_function(self, mock_async):
        """Test function calls send_bulk_verification_email_async."""
        representative_ids = [1, 2, 3]
        verifier_id = 99
        
        trigger_bulk_verification_email(representative_ids, verifier_id)
        
        # Should call the async function
        mock_async.assert_called_once_with(representative_ids, verifier_id)
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_passes_correct_parameters(self, mock_async):
        """Test correct parameters are passed."""
        representative_ids = [10, 20, 30]
        verifier_id = 5
        
        trigger_bulk_verification_email(representative_ids, verifier_id)
        
        # Check both arguments
        call_args = mock_async.call_args[0]
        self.assertEqual(call_args[0], representative_ids)
        self.assertEqual(call_args[1], verifier_id)
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_handles_empty_list(self, mock_async):
        """Test handles empty representative list."""
        representative_ids = []
        verifier_id = 1
        
        trigger_bulk_verification_email(representative_ids, verifier_id)
        
        # Should still call (let background_utils handle empty list)
        mock_async.assert_called_once_with([], verifier_id)
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_handles_single_representative(self, mock_async):
        """Test handles single representative."""
        representative_ids = [42]
        verifier_id = 1
        
        trigger_bulk_verification_email(representative_ids, verifier_id)
        
        mock_async.assert_called_once_with([42], verifier_id)
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_handles_many_representatives(self, mock_async):
        """Test handles large list of representatives."""
        representative_ids = list(range(1, 101))  # 100 IDs
        verifier_id = 1
        
        trigger_bulk_verification_email(representative_ids, verifier_id)
        
        # Should pass entire list
        call_args = mock_async.call_args[0]
        self.assertEqual(len(call_args[0]), 100)


class TriggerDailySummaryTest(TestCase):
    """Test trigger_daily_summary function."""
    
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_calls_background_utils_function(self, mock_async):
        """Test function calls send_daily_summary_email_async."""
        trigger_daily_summary()
        
        # Should call the async function
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_no_parameters_required(self, mock_async):
        """Test function requires no parameters."""
        # Should work without any arguments
        try:
            trigger_daily_summary()
            success = True
        except TypeError:
            success = False
        
        self.assertTrue(success)
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_multiple_invocations(self, mock_async):
        """Test multiple calls work independently."""
        # Call multiple times
        trigger_daily_summary()
        trigger_daily_summary()
        trigger_daily_summary()
        
        # Should be called three times
        self.assertEqual(mock_async.call_count, 3)
    
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_handles_exception_from_background_utils(self, mock_async):
        """Test exception from background_utils is propagated."""
        mock_async.side_effect = Exception("Email sending failed")
        
        with self.assertRaises(Exception):
            trigger_daily_summary()


class TriggerProcessNotificationsTest(TestCase):
    """Test trigger_process_notifications function."""
    
    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_calls_background_utils_function(self, mock_async):
        """Test function calls process_pending_notifications_async."""
        trigger_process_notifications()
        
        # Should call the async function
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_no_parameters_required(self, mock_async):
        """Test function requires no parameters."""
        # Should work without any arguments
        try:
            trigger_process_notifications()
            success = True
        except TypeError:
            success = False
        
        self.assertTrue(success)
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_multiple_invocations(self, mock_async):
        """Test multiple calls work independently."""
        # Call multiple times
        trigger_process_notifications()
        trigger_process_notifications()
        
        # Should be called twice
        self.assertEqual(mock_async.call_count, 2)
    
    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_handles_exception_from_background_utils(self, mock_async):
        """Test exception from background_utils is propagated."""
        mock_async.side_effect = Exception("Processing failed")
        
        with self.assertRaises(Exception):
            trigger_process_notifications()


class TriggerGraduationCheckTest(TestCase):
    """Test trigger_graduation_check function."""
    
    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_calls_background_task_function(self, mock_task):
        """Test function calls check_graduation_statuses_task."""
        trigger_graduation_check()
        
        # Should call the background task function
        mock_task.assert_called_once()
    
    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_no_parameters_required(self, mock_task):
        """Test function requires no parameters."""
        # Should work without any arguments
        try:
            trigger_graduation_check()
            success = True
        except TypeError:
            success = False
        
        self.assertTrue(success)
        mock_task.assert_called_once()
    
    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_multiple_invocations(self, mock_task):
        """Test multiple calls work independently."""
        # Call multiple times
        trigger_graduation_check()
        trigger_graduation_check()
        trigger_graduation_check()
        
        # Should be called three times
        self.assertEqual(mock_task.call_count, 3)
    
    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_handles_exception_from_background_task(self, mock_task):
        """Test exception from background task is propagated."""
        mock_task.side_effect = Exception("Task scheduling failed")
        
        with self.assertRaises(Exception):
            trigger_graduation_check()


class TasksIntegrationTest(TestCase):
    """Test tasks module integration scenarios."""
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    @patch('academic_directory.tasks.process_pending_notifications_async')
    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_all_tasks_can_be_called_together(
        self, mock_graduation, mock_process, mock_summary, 
        mock_bulk_verify, mock_new_submission
    ):
        """Test all task triggers can be called in sequence."""
        # Call all triggers
        trigger_new_submission_email(1)
        trigger_bulk_verification_email([1, 2], 99)
        trigger_daily_summary()
        trigger_process_notifications()
        trigger_graduation_check()
        
        # All should be called
        mock_new_submission.assert_called_once()
        mock_bulk_verify.assert_called_once()
        mock_summary.assert_called_once()
        mock_process.assert_called_once()
        mock_graduation.assert_called_once()
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_new_submission_workflow(self, mock_async):
        """Test typical new submission workflow."""
        # Simulate new submission for representative ID 42
        representative_id = 42
        
        # Trigger email
        trigger_new_submission_email(representative_id)
        
        # Should queue email
        mock_async.assert_called_once_with(42)
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_bulk_verification_workflow(self, mock_async):
        """Test typical bulk verification workflow."""
        # Simulate admin verifying 5 representatives
        representative_ids = [1, 2, 3, 4, 5]
        verifier_id = 99
        
        # Trigger email
        trigger_bulk_verification_email(representative_ids, verifier_id)
        
        # Should queue email
        mock_async.assert_called_once_with(representative_ids, verifier_id)
    
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_daily_summary_workflow(self, mock_async):
        """Test typical daily summary workflow."""
        # Simulate cron job triggering daily summary
        trigger_daily_summary()
        
        # Should queue email
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_notification_processing_workflow(self, mock_async):
        """Test typical notification processing workflow."""
        # Simulate cron job processing notifications
        trigger_process_notifications()
        
        # Should queue processing
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_graduation_check_workflow(self, mock_task):
        """Test typical graduation check workflow."""
        # Simulate cron job checking graduations
        trigger_graduation_check()
        
        # Should schedule task
        mock_task.assert_called_once()


class TasksErrorHandlingTest(TestCase):
    """Test error handling in tasks module."""
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_new_submission_email_error(self, mock_async):
        """Test error handling for new submission email."""
        mock_async.side_effect = Exception("SMTP connection failed")
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            trigger_new_submission_email(1)
        
        self.assertIn("SMTP", str(context.exception))
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_bulk_verification_email_error(self, mock_async):
        """Test error handling for bulk verification email."""
        mock_async.side_effect = Exception("Invalid template")
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            trigger_bulk_verification_email([1, 2], 99)
        
        self.assertIn("Invalid", str(context.exception))
    
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_daily_summary_error(self, mock_async):
        """Test error handling for daily summary."""
        mock_async.side_effect = Exception("No admin emails")
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            trigger_daily_summary()
        
        self.assertIn("admin", str(context.exception))
    
    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_process_notifications_error(self, mock_async):
        """Test error handling for notification processing."""
        mock_async.side_effect = Exception("Database error")
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            trigger_process_notifications()
        
        self.assertIn("Database", str(context.exception))
    
    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_graduation_check_error(self, mock_task):
        """Test error handling for graduation check."""
        mock_task.side_effect = Exception("Background tasks not running")
        
        # Should raise exception
        with self.assertRaises(Exception) as context:
            trigger_graduation_check()
        
        self.assertIn("Background", str(context.exception))


class TasksEdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_new_submission_with_none_id(self, mock_async):
        """Test new submission with None ID."""
        # Should still call (let background_utils handle None)
        trigger_new_submission_email(None)
        
        mock_async.assert_called_once_with(None)
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_new_submission_with_zero_id(self, mock_async):
        """Test new submission with zero ID."""
        trigger_new_submission_email(0)
        
        mock_async.assert_called_once_with(0)
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_new_submission_with_negative_id(self, mock_async):
        """Test new submission with negative ID."""
        # Should still call (let background_utils validate)
        trigger_new_submission_email(-1)
        
        mock_async.assert_called_once_with(-1)
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_bulk_verification_with_none_verifier(self, mock_async):
        """Test bulk verification with None verifier ID."""
        trigger_bulk_verification_email([1, 2], None)
        
        # Should still call
        call_args = mock_async.call_args[0]
        self.assertIsNone(call_args[1])
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_bulk_verification_with_duplicate_ids(self, mock_async):
        """Test bulk verification with duplicate representative IDs."""
        representative_ids = [1, 1, 2, 2, 3]
        verifier_id = 99
        
        trigger_bulk_verification_email(representative_ids, verifier_id)
        
        # Should pass list as-is (let background_utils deduplicate if needed)
        call_args = mock_async.call_args[0]
        self.assertEqual(call_args[0], representative_ids)


class TasksPerformanceTest(TestCase):
    """Test performance characteristics of task triggers."""
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_new_submission_quick_execution(self, mock_async):
        """Test new submission trigger executes quickly."""
        import time
        
        start_time = time.time()
        trigger_new_submission_email(123)
        end_time = time.time()
        
        # Should complete very quickly (< 0.1 seconds)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.1)
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_bulk_verification_quick_execution(self, mock_async):
        """Test bulk verification trigger executes quickly."""
        import time
        
        representative_ids = list(range(1, 101))  # 100 IDs
        
        start_time = time.time()
        trigger_bulk_verification_email(representative_ids, 99)
        end_time = time.time()
        
        # Should complete very quickly (< 0.1 seconds)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.1)
    
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_daily_summary_quick_execution(self, mock_async):
        """Test daily summary trigger executes quickly."""
        import time
        
        start_time = time.time()
        trigger_daily_summary()
        end_time = time.time()
        
        # Should complete very quickly (< 0.1 seconds)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 0.1)


class TasksDocumentationTest(TestCase):
    """Test that functions have proper documentation."""
    
    def test_new_submission_email_has_docstring(self):
        """Test trigger_new_submission_email has docstring."""
        self.assertIsNotNone(trigger_new_submission_email.__doc__)
        self.assertIn('Queue', trigger_new_submission_email.__doc__)
    
    def test_bulk_verification_email_has_docstring(self):
        """Test trigger_bulk_verification_email has docstring."""
        self.assertIsNotNone(trigger_bulk_verification_email.__doc__)
        self.assertIn('Queue', trigger_bulk_verification_email.__doc__)
    
    def test_daily_summary_has_docstring(self):
        """Test trigger_daily_summary has docstring."""
        self.assertIsNotNone(trigger_daily_summary.__doc__)
        self.assertIn('Queue', trigger_daily_summary.__doc__)
    
    def test_process_notifications_has_docstring(self):
        """Test trigger_process_notifications has docstring."""
        self.assertIsNotNone(trigger_process_notifications.__doc__)
        self.assertIn('Queue', trigger_process_notifications.__doc__)
    
    def test_graduation_check_has_docstring(self):
        """Test trigger_graduation_check has docstring."""
        self.assertIsNotNone(trigger_graduation_check.__doc__)
        self.assertIn('Schedule', trigger_graduation_check.__doc__)


class TasksImportTest(TestCase):
    """Test that tasks module imports correctly."""
    
    def test_imports_background_utils_functions(self):
        """Test that background_utils functions are imported."""
        from academic_directory import tasks
        
        # Should have access to imported functions via module
        self.assertTrue(hasattr(tasks, 'send_new_submission_email_async'))
        self.assertTrue(hasattr(tasks, 'send_bulk_verification_email_async'))
        self.assertTrue(hasattr(tasks, 'send_daily_summary_email_async'))
        self.assertTrue(hasattr(tasks, 'process_pending_notifications_async'))
        self.assertTrue(hasattr(tasks, 'check_graduation_statuses_task'))
    
    def test_all_trigger_functions_defined(self):
        """Test all trigger functions are defined in module."""
        from academic_directory import tasks
        
        self.assertTrue(hasattr(tasks, 'trigger_new_submission_email'))
        self.assertTrue(hasattr(tasks, 'trigger_bulk_verification_email'))
        self.assertTrue(hasattr(tasks, 'trigger_daily_summary'))
        self.assertTrue(hasattr(tasks, 'trigger_process_notifications'))
        self.assertTrue(hasattr(tasks, 'trigger_graduation_check'))
    
    def test_logger_imported(self):
        """Test logger is imported."""
        from academic_directory import tasks
        
        self.assertTrue(hasattr(tasks, 'logger'))


class TasksRealWorldScenariosTest(TestCase):
    """Test realistic usage scenarios."""
    
    @patch('academic_directory.tasks.send_new_submission_email_async')
    def test_submission_api_endpoint_flow(self, mock_async):
        """Test typical flow from public API submission."""
        # Simulate API creating representative with ID 123
        representative_id = 123
        
        # API would call trigger after creation
        trigger_new_submission_email(representative_id)
        
        # Email should be queued
        mock_async.assert_called_once_with(123)
    
    @patch('academic_directory.tasks.send_bulk_verification_email_async')
    def test_admin_bulk_action_flow(self, mock_async):
        """Test typical flow from admin bulk action."""
        # Simulate admin selecting 10 representatives to verify
        representative_ids = list(range(1, 11))
        admin_id = 5
        
        # Admin action would call trigger after verification
        trigger_bulk_verification_email(representative_ids, admin_id)
        
        # Email should be queued
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.send_daily_summary_email_async')
    def test_cron_daily_summary_flow(self, mock_async):
        """Test typical flow from cron job."""
        # Simulate daily cron job at 8 AM
        trigger_daily_summary()
        
        # Summary should be queued
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.process_pending_notifications_async')
    def test_cron_notification_batch_flow(self, mock_async):
        """Test typical flow from periodic cron job."""
        # Simulate cron job running every 10 minutes
        trigger_process_notifications()
        
        # Processing should be queued
        mock_async.assert_called_once()
    
    @patch('academic_directory.tasks.check_graduation_statuses_task')
    def test_cron_graduation_check_flow(self, mock_task):
        """Test typical flow from daily graduation check."""
        # Simulate daily cron job at 1 AM
        trigger_graduation_check()
        
        # Task should be scheduled
        mock_task.assert_called_once()