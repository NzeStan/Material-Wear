"""
Pytest fixtures for Academic Directory tests.

Provides reusable fixtures for models, users, and API clients.
"""
import pytest
from datetime import datetime
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academic_directory.models import (
    University,
    Faculty,
    Department,
    ProgramDuration,
    Representative,
    RepresentativeHistory,
    SubmissionNotification,
)

User = get_user_model()


# =============================================================================
# User Fixtures
# =============================================================================

@pytest.fixture
def admin_user(db):
    """Create an admin/staff user for authenticated tests."""
    user = User.objects.create_user(
        username='admin_test',
        email='admin@test.com',
        password='testpass123',
        is_staff=True,
        is_superuser=True,
    )
    return user


@pytest.fixture
def regular_user(db):
    """Create a regular (non-admin) user."""
    user = User.objects.create_user(
        username='regular_test',
        email='regular@test.com',
        password='testpass123',
        is_staff=False,
        is_superuser=False,
    )
    return user


# =============================================================================
# API Client Fixtures
# =============================================================================

@pytest.fixture
def api_client():
    """Return an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def admin_api_client(admin_user):
    """Return an API client authenticated as admin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def regular_api_client(regular_user):
    """Return an API client authenticated as regular user."""
    client = APIClient()
    client.force_authenticate(user=regular_user)
    return client


# =============================================================================
# University Fixtures
# =============================================================================

@pytest.fixture
def university(db):
    """Create a single university."""
    return University.objects.create(
        name='University of Nigeria, Nsukka',
        abbreviation='UNN',
        state='ENUGU',
        type='FEDERAL',
        is_active=True,
    )


@pytest.fixture
def inactive_university(db):
    """Create an inactive university."""
    return University.objects.create(
        name='Inactive University',
        abbreviation='IU',
        state='LAGOS',
        type='PRIVATE',
        is_active=False,
    )


@pytest.fixture
def multiple_universities(db):
    """Create multiple universities for testing lists."""
    universities = [
        University.objects.create(
            name='University of Benin',
            abbreviation='UNIBEN',
            state='EDO',
            type='FEDERAL',
            is_active=True,
        ),
        University.objects.create(
            name='University of Lagos',
            abbreviation='UNILAG',
            state='LAGOS',
            type='FEDERAL',
            is_active=True,
        ),
        University.objects.create(
            name='Lagos State University',
            abbreviation='LASU',
            state='LAGOS',
            type='STATE',
            is_active=True,
        ),
    ]
    return universities


# =============================================================================
# Faculty Fixtures
# =============================================================================

@pytest.fixture
def faculty(university):
    """Create a faculty within a university."""
    return Faculty.objects.create(
        university=university,
        name='Faculty of Engineering',
        abbreviation='ENG',
        is_active=True,
    )


@pytest.fixture
def faculty_science(university):
    """Create a science faculty."""
    return Faculty.objects.create(
        university=university,
        name='Faculty of Physical Sciences',
        abbreviation='SCI',
        is_active=True,
    )


@pytest.fixture
def inactive_faculty(university):
    """Create an inactive faculty."""
    return Faculty.objects.create(
        university=university,
        name='Inactive Faculty',
        abbreviation='IF',
        is_active=False,
    )


# =============================================================================
# Department Fixtures
# =============================================================================

@pytest.fixture
def department(faculty):
    """Create a department within a faculty."""
    return Department.objects.create(
        faculty=faculty,
        name='Computer Science',
        abbreviation='CSC',
        is_active=True,
    )


@pytest.fixture
def department_ee(faculty):
    """Create an electrical engineering department."""
    return Department.objects.create(
        faculty=faculty,
        name='Electrical Engineering',
        abbreviation='EEE',
        is_active=True,
    )


@pytest.fixture
def inactive_department(faculty):
    """Create an inactive department."""
    return Department.objects.create(
        faculty=faculty,
        name='Inactive Department',
        abbreviation='ID',
        is_active=False,
    )


# =============================================================================
# Program Duration Fixtures
# =============================================================================

@pytest.fixture
def program_duration(department):
    """Create a program duration (4 years, B.Sc)."""
    return ProgramDuration.objects.create(
        department=department,
        duration_years=4,
        program_type='BSC',
    )


@pytest.fixture
def program_duration_5years(department_ee):
    """Create a 5-year engineering program duration."""
    return ProgramDuration.objects.create(
        department=department_ee,
        duration_years=5,
        program_type='BENG',
    )


# =============================================================================
# Representative Fixtures
# =============================================================================

@pytest.fixture
def class_rep(department, program_duration):
    """Create a class representative."""
    current_year = datetime.now().year
    return Representative.objects.create(
        full_name='John Doe',
        nickname='Johnny',
        phone_number='+2348012345678',
        email='john.doe@example.com',
        department=department,
        faculty=department.faculty,
        university=department.faculty.university,
        role='CLASS_REP',
        entry_year=current_year - 2,  # Currently in 3rd year
        submission_source='WEBSITE',
        verification_status='UNVERIFIED',
        is_active=True,
    )


@pytest.fixture
def final_year_class_rep(department, program_duration):
    """Create a final year class representative."""
    current_year = datetime.now().year
    return Representative.objects.create(
        full_name='Final Year Student',
        phone_number='+2348023456789',
        department=department,
        faculty=department.faculty,
        university=department.faculty.university,
        role='CLASS_REP',
        entry_year=current_year - 3,  # 4th year in 4-year program
        submission_source='WEBSITE',
        verification_status='UNVERIFIED',
        is_active=True,
    )


@pytest.fixture
def graduated_class_rep(department, program_duration):
    """Create a graduated class representative."""
    current_year = datetime.now().year
    return Representative.objects.create(
        full_name='Graduated Student',
        phone_number='+2348034567890',
        department=department,
        faculty=department.faculty,
        university=department.faculty.university,
        role='CLASS_REP',
        entry_year=current_year - 5,  # Graduated
        submission_source='WEBSITE',
        verification_status='UNVERIFIED',
        is_active=True,
    )


@pytest.fixture
def dept_president(department):
    """Create a department president."""
    current_year = datetime.now().year
    return Representative.objects.create(
        full_name='Dept President',
        phone_number='+2348045678901',
        department=department,
        faculty=department.faculty,
        university=department.faculty.university,
        role='DEPT_PRESIDENT',
        tenure_start_year=current_year,
        submission_source='MANUAL',
        verification_status='VERIFIED',
        is_active=True,
    )


@pytest.fixture
def faculty_president(faculty):
    """Create a faculty president."""
    current_year = datetime.now().year
    dept = Department.objects.create(
        faculty=faculty,
        name='President Dept',
        abbreviation='PD',
        is_active=True,
    )
    return Representative.objects.create(
        full_name='Faculty President',
        phone_number='+2348056789012',
        department=dept,
        faculty=faculty,
        university=faculty.university,
        role='FACULTY_PRESIDENT',
        tenure_start_year=current_year,
        submission_source='MANUAL',
        verification_status='VERIFIED',
        is_active=True,
    )


@pytest.fixture
def verified_representative(department):
    """Create a verified representative."""
    current_year = datetime.now().year
    return Representative.objects.create(
        full_name='Verified Rep',
        phone_number='+2348067890123',
        department=department,
        faculty=department.faculty,
        university=department.faculty.university,
        role='CLASS_REP',
        entry_year=current_year - 1,
        submission_source='WEBSITE',
        verification_status='VERIFIED',
        is_active=True,
    )


@pytest.fixture
def disputed_representative(department):
    """Create a disputed representative."""
    current_year = datetime.now().year
    return Representative.objects.create(
        full_name='Disputed Rep',
        phone_number='+2348078901234',
        department=department,
        faculty=department.faculty,
        university=department.faculty.university,
        role='CLASS_REP',
        entry_year=current_year - 1,
        submission_source='WEBSITE',
        verification_status='DISPUTED',
        is_active=True,
    )


@pytest.fixture
def multiple_representatives(department, program_duration):
    """Create multiple representatives for list testing."""
    current_year = datetime.now().year
    reps = []
    for i in range(5):
        rep = Representative.objects.create(
            full_name=f'Representative {i}',
            phone_number=f'+234801234567{i}',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year - (i % 4),
            submission_source='WEBSITE',
            verification_status=['UNVERIFIED', 'VERIFIED', 'DISPUTED'][i % 3],
            is_active=True,
        )
        reps.append(rep)
    return reps


# =============================================================================
# Representative History Fixtures
# =============================================================================

@pytest.fixture
def representative_history(class_rep):
    """Create a history entry for a representative."""
    return RepresentativeHistory.objects.create(
        representative=class_rep,
        full_name=class_rep.full_name,
        phone_number=class_rep.phone_number,
        department=class_rep.department,
        faculty=class_rep.faculty,
        university=class_rep.university,
        role=class_rep.role,
        entry_year=class_rep.entry_year,
        verification_status=class_rep.verification_status,
        is_active=class_rep.is_active,
        notes='Initial snapshot',
    )


# =============================================================================
# Submission Notification Fixtures
# =============================================================================

@pytest.fixture
def unread_notification(class_rep):
    """Get or create an unread submission notification."""
    # Signal already creates notification when rep is created
    notification, _ = SubmissionNotification.objects.get_or_create(
        representative=class_rep,
        defaults={'is_read': False, 'is_emailed': False}
    )
    # Ensure it's unread
    notification.is_read = False
    notification.is_emailed = False
    notification.save()
    return notification


@pytest.fixture
def read_notification(dept_president, admin_user):
    """Get or create a read submission notification."""
    from django.utils import timezone
    # Signal already creates notification when rep is created
    notification, _ = SubmissionNotification.objects.get_or_create(
        representative=dept_president,
    )
    # Mark as read
    notification.is_read = True
    notification.is_emailed = True
    notification.read_by = admin_user
    notification.read_at = timezone.now()
    notification.save()
    return notification


@pytest.fixture
def multiple_notifications(multiple_representatives):
    """Get multiple notifications for testing (created by signal)."""
    notifications = []
    for rep in multiple_representatives:
        # Signal creates notifications when reps are created
        notif, _ = SubmissionNotification.objects.get_or_create(
            representative=rep,
            defaults={'is_read': False, 'is_emailed': False}
        )
        # Ensure they're unread for testing
        notif.is_read = False
        notif.is_emailed = False
        notif.save()
        notifications.append(notif)
    return notifications


# =============================================================================
# Submission Data Fixtures
# =============================================================================

@pytest.fixture
def valid_class_rep_submission_data(department):
    """Return valid submission data for a class rep."""
    current_year = datetime.now().year
    return {
        'full_name': 'New Student',
        'phone_number': '08098765432',
        'email': 'new.student@example.com',
        'department_id': str(department.id),
        'role': 'CLASS_REP',
        'entry_year': current_year - 1,
        'submission_source': 'WEBSITE',
    }


@pytest.fixture
def valid_president_submission_data(department):
    """Return valid submission data for a president."""
    current_year = datetime.now().year
    return {
        'full_name': 'New President',
        'phone_number': '08087654321',
        'department_id': str(department.id),
        'role': 'DEPT_PRESIDENT',
        'tenure_start_year': current_year,
        'submission_source': 'MANUAL',
    }


@pytest.fixture
def invalid_submission_data():
    """Return invalid submission data for error testing."""
    return {
        'full_name': '',  # Empty name
        'phone_number': '1234',  # Invalid phone
        'role': 'INVALID_ROLE',
    }
