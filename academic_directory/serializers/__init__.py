"""
Academic Directory Serializers

This package contains all serializers for the Academic Directory API.
"""

from .university import UniversitySerializer, UniversityListSerializer
from .faculty import FacultySerializer, FacultyListSerializer
from .department import DepartmentSerializer, DepartmentListSerializer
from .program_duration import ProgramDurationSerializer
from .representative import (
    RepresentativeSerializer,
    RepresentativeListSerializer,
    RepresentativeDetailSerializer,
    RepresentativeVerificationSerializer,
)
from .bulk_submission import BulkSubmissionSerializer, SingleSubmissionSerializer
from .admin import (
    RepresentativeHistorySerializer,
    SubmissionNotificationSerializer,
    DashboardStatsSerializer,
)

__all__ = [
    'UniversitySerializer',
    'UniversityListSerializer',
    'FacultySerializer',
    'FacultyListSerializer',
    'DepartmentSerializer',
    'DepartmentListSerializer',
    'ProgramDurationSerializer',
    'RepresentativeSerializer',
    'RepresentativeListSerializer',
    'RepresentativeDetailSerializer',
    'RepresentativeVerificationSerializer',
    'BulkSubmissionSerializer',
    'SingleSubmissionSerializer',
    'RepresentativeHistorySerializer',
    'SubmissionNotificationSerializer',
    'DashboardStatsSerializer',
]
