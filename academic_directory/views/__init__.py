"""
Academic Directory Views

This package contains all views for the Academic Directory API.
"""

from .public_submission import PublicSubmissionView
from .representative import RepresentativeViewSet
from .university import UniversityViewSet
from .faculty import FacultyViewSet
from .department import DepartmentViewSet
from .pdf_generation import PDFGenerationView
from .dashboard import DashboardView, NotificationViewSet

__all__ = [
    'PublicSubmissionView',
    'RepresentativeViewSet',
    'UniversityViewSet',
    'FacultyViewSet',
    'DepartmentViewSet',
    'PDFGenerationView',
    'DashboardView',
    'NotificationViewSet',
]
