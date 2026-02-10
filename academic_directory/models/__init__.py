"""
Academic Directory Models

This package contains all models for the Academic Directory app.
"""

from .university import University
from .faculty import Faculty
from .department import Department
from .program_duration import ProgramDuration
from .representative import Representative
from .representative_history import RepresentativeHistory
from .submission_notification import SubmissionNotification

__all__ = [
    'University',
    'Faculty',
    'Department',
    'ProgramDuration',
    'Representative',
    'RepresentativeHistory',
    'SubmissionNotification',
]
