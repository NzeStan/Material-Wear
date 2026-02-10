"""
Academic Directory Utilities

This package contains utility functions for the Academic Directory app.
"""

from .level_calculator import calculate_current_level, get_academic_year_range
from .validators import (
    validate_nigerian_phone,
    validate_academic_year,
    normalize_phone_number
)
from .deduplication import merge_representative_records
from .notifications import (
    send_new_submission_email,
    send_bulk_verification_email,
    get_unread_notification_count
)

__all__ = [
    'calculate_current_level',
    'get_academic_year_range',
    'validate_nigerian_phone',
    'validate_academic_year',
    'normalize_phone_number',
    'merge_representative_records',
    'send_new_submission_email',
    'send_bulk_verification_email',
    'get_unread_notification_count',
]
