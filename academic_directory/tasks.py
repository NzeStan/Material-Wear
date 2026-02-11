# academic_directory/tasks.py
"""
Background Tasks for Academic Directory

This module bridges scheduled work to jmw/background_utils.py.
No Celery — uses threading for quick email tasks and
django-background-tasks for heavy periodic jobs.

Scheduled via management commands (see management/commands/):
  - run_graduation_check   → daily via cron
  - send_academic_summary  → daily via cron
  - process_academic_notifications → every 5-10 min via cron
"""
import logging
from jmw.background_utils import (
    send_new_submission_email_async,
    send_bulk_verification_email_async,
    send_daily_summary_email_async,
    process_pending_notifications_async,
    check_graduation_statuses_task,
)

logger = logging.getLogger(__name__)


def trigger_new_submission_email(representative_id):
    """
    Queue new submission notification email.
    Call after a Representative is created.
    """
    send_new_submission_email_async(representative_id)


def trigger_bulk_verification_email(representative_ids, verifier_id):
    """
    Queue bulk verification notification email.
    Call after bulk verify/dispute action.
    """
    send_bulk_verification_email_async(representative_ids, verifier_id)


def trigger_daily_summary():
    """
    Queue daily summary email to admins.
    Called from management command: send_academic_summary
    """
    send_daily_summary_email_async()


def trigger_process_notifications():
    """
    Queue batch pending notification email.
    Called from management command: process_academic_notifications
    """
    process_pending_notifications_async()


def trigger_graduation_check():
    """
    Schedule graduation status check via django-background-tasks.
    Called from management command: run_graduation_check
    """
    check_graduation_statuses_task()