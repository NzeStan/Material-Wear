"""
Tests for Academic Directory Admin Configuration.

Tests cover:
- Admin site registration
- List display configuration
- Filters and search
- Actions (bulk verify, dispute, deactivate)
- save_model override (auto-populate verification metadata)
- Inline configuration
- Permission enforcement
"""
import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.utils import timezone
from unittest.mock import patch, MagicMock

from academic_directory.admin import (
    UniversityAdmin,
    FacultyAdmin,
    DepartmentAdmin,
    ProgramDurationAdmin,
    RepresentativeAdmin,
    RepresentativeHistoryAdmin,
    SubmissionNotificationAdmin,
)
from academic_directory.models import (
    University,
    Faculty,
    Department,
    ProgramDuration,
    Representative,
    RepresentativeHistory,
    SubmissionNotification,
)


@pytest.fixture
def site():
    """Return an AdminSite instance."""
    return AdminSite()


@pytest.fixture
def request_factory():
    """Return a RequestFactory instance."""
    return RequestFactory()


@pytest.fixture
def admin_request(request_factory, admin_user):
    """Return a mock admin request."""
    request = request_factory.get('/admin/')
    request.user = admin_user
    return request


# =============================================================================
# University Admin Tests
# =============================================================================

class TestUniversityAdmin:
    """Tests for UniversityAdmin."""

    def test_admin_registered(self, site):
        """Test UniversityAdmin is properly configured."""
        admin = UniversityAdmin(University, site)
        assert admin is not None

    def test_list_display(self, site):
        """Test list_display configuration."""
        admin = UniversityAdmin(University, site)
        assert 'abbreviation' in admin.list_display
        assert 'name' in admin.list_display
        assert 'state' in admin.list_display
        assert 'is_active' in admin.list_display

    def test_list_filter(self, site):
        """Test list_filter configuration."""
        admin = UniversityAdmin(University, site)
        assert 'type' in admin.list_filter
        assert 'state' in admin.list_filter
        assert 'is_active' in admin.list_filter

    def test_search_fields(self, site):
        """Test search_fields configuration."""
        admin = UniversityAdmin(University, site)
        assert 'name' in admin.search_fields
        assert 'abbreviation' in admin.search_fields

    def test_type_badge_method(self, site, university):
        """Test type_badge method returns HTML."""
        admin = UniversityAdmin(University, site)
        badge = admin.type_badge(university)
        assert 'span' in badge
        assert university.get_type_display() in badge


# =============================================================================
# Faculty Admin Tests
# =============================================================================

class TestFacultyAdmin:
    """Tests for FacultyAdmin."""

    def test_admin_registered(self, site):
        """Test FacultyAdmin is properly configured."""
        admin = FacultyAdmin(Faculty, site)
        assert admin is not None

    def test_list_display(self, site):
        """Test list_display configuration."""
        admin = FacultyAdmin(Faculty, site)
        assert 'abbreviation' in admin.list_display
        assert 'name' in admin.list_display
        assert 'university' in admin.list_display

    def test_autocomplete_fields(self, site):
        """Test autocomplete_fields configuration."""
        admin = FacultyAdmin(Faculty, site)
        assert 'university' in admin.autocomplete_fields


# =============================================================================
# Department Admin Tests
# =============================================================================

class TestDepartmentAdmin:
    """Tests for DepartmentAdmin."""

    def test_admin_registered(self, site):
        """Test DepartmentAdmin is properly configured."""
        admin = DepartmentAdmin(Department, site)
        assert admin is not None

    def test_list_display(self, site):
        """Test list_display configuration."""
        admin = DepartmentAdmin(Department, site)
        assert 'abbreviation' in admin.list_display
        assert 'name' in admin.list_display
        assert 'faculty' in admin.list_display

    def test_autocomplete_fields(self, site):
        """Test autocomplete_fields configuration."""
        admin = DepartmentAdmin(Department, site)
        assert 'faculty' in admin.autocomplete_fields

    def test_university_display_method(self, site, department):
        """Test university_display method."""
        admin = DepartmentAdmin(Department, site)
        display = admin.university_display(department)
        assert display == department.faculty.university.abbreviation


# =============================================================================
# Program Duration Admin Tests
# =============================================================================

class TestProgramDurationAdmin:
    """Tests for ProgramDurationAdmin."""

    def test_admin_registered(self, site):
        """Test ProgramDurationAdmin is properly configured."""
        admin = ProgramDurationAdmin(ProgramDuration, site)
        assert admin is not None

    def test_list_display(self, site):
        """Test list_display configuration."""
        admin = ProgramDurationAdmin(ProgramDuration, site)
        assert 'department' in admin.list_display
        assert 'duration_years' in admin.list_display
        assert 'program_type' in admin.list_display

    def test_autocomplete_fields(self, site):
        """Test autocomplete_fields configuration."""
        admin = ProgramDurationAdmin(ProgramDuration, site)
        assert 'department' in admin.autocomplete_fields


# =============================================================================
# Representative Admin Tests
# =============================================================================

class TestRepresentativeAdmin:
    """Tests for RepresentativeAdmin."""

    def test_admin_registered(self, site):
        """Test RepresentativeAdmin is properly configured."""
        admin = RepresentativeAdmin(Representative, site)
        assert admin is not None

    def test_list_display(self, site):
        """Test list_display configuration."""
        admin = RepresentativeAdmin(Representative, site)
        assert 'phone_number' in admin.list_display
        assert 'department' in admin.list_display
        assert 'is_active' in admin.list_display

    def test_list_filter(self, site):
        """Test list_filter configuration."""
        admin = RepresentativeAdmin(Representative, site)
        assert 'role' in admin.list_filter
        assert 'verification_status' in admin.list_filter
        assert 'is_active' in admin.list_filter

    def test_search_fields(self, site):
        """Test search_fields configuration."""
        admin = RepresentativeAdmin(Representative, site)
        assert 'full_name' in admin.search_fields
        assert 'phone_number' in admin.search_fields
        assert 'email' in admin.search_fields

    def test_readonly_fields(self, site):
        """Test readonly_fields configuration."""
        admin = RepresentativeAdmin(Representative, site)
        assert 'verified_by' in admin.readonly_fields
        assert 'verified_at' in admin.readonly_fields
        assert 'created_at' in admin.readonly_fields

    def test_role_badge_method(self, site, class_rep):
        """Test role_badge method returns HTML."""
        admin = RepresentativeAdmin(Representative, site)
        badge = admin.role_badge(class_rep)
        assert 'span' in badge
        assert class_rep.get_role_display() in badge

    def test_verification_badge_method(self, site, class_rep):
        """Test verification_badge method returns HTML."""
        admin = RepresentativeAdmin(Representative, site)
        badge = admin.verification_badge(class_rep)
        assert 'span' in badge

    def test_level_display_class_rep(self, site, class_rep, program_duration):
        """Test level_display for class rep."""
        admin = RepresentativeAdmin(Representative, site)
        display = admin.level_display(class_rep)
        # Should return level or dash
        assert display == class_rep.current_level_display or display == '—'

    def test_level_display_president(self, site, dept_president):
        """Test level_display for president."""
        admin = RepresentativeAdmin(Representative, site)
        display = admin.level_display(dept_president)
        assert display == 'N/A'

    def test_save_model_sets_verified_by(self, site, admin_request, class_rep):
        """Test save_model sets verified_by when status changes to VERIFIED."""
        admin = RepresentativeAdmin(Representative, site)

        # Mock form
        form = MagicMock()
        form.changed_data = ['verification_status']

        # Change status to VERIFIED
        class_rep.verification_status = 'VERIFIED'

        admin.save_model(admin_request, class_rep, form, change=True)

        assert class_rep.verified_by == admin_request.user
        assert class_rep.verified_at is not None

    def test_save_model_clears_verified_on_unverify(self, site, admin_request, verified_representative):
        """Test save_model clears verification metadata when un-verifying."""
        admin = RepresentativeAdmin(Representative, site)

        # Mock form
        form = MagicMock()

        # Change status to UNVERIFIED
        verified_representative.verification_status = 'UNVERIFIED'

        admin.save_model(admin_request, verified_representative, form, change=True)

        assert verified_representative.verified_by is None
        assert verified_representative.verified_at is None

    def test_verify_representatives_action(self, site, admin_request, multiple_representatives):
        """Test verify_representatives bulk action."""
        admin = RepresentativeAdmin(Representative, site)
        queryset = Representative.objects.filter(
            id__in=[r.id for r in multiple_representatives[:2]]
        )

        with patch('academic_directory.admin.send_bulk_verification_email'):
            with patch.object(admin, 'message_user'):
                admin.verify_representatives(admin_request, queryset)

        # Check all are verified
        for rep in queryset:
            rep.refresh_from_db()
            assert rep.verification_status == 'VERIFIED'

    def test_dispute_representatives_action(self, site, admin_request, multiple_representatives):
        """Test dispute_representatives bulk action."""
        admin = RepresentativeAdmin(Representative, site)
        queryset = Representative.objects.filter(
            id__in=[r.id for r in multiple_representatives[:2]]
        )

        with patch.object(admin, 'message_user'):
            admin.dispute_representatives(admin_request, queryset)

        # Check all are disputed
        for rep in queryset:
            rep.refresh_from_db()
            assert rep.verification_status == 'DISPUTED'

    def test_deactivate_representatives_action(self, site, admin_request, multiple_representatives):
        """Test deactivate_representatives bulk action."""
        admin = RepresentativeAdmin(Representative, site)
        queryset = Representative.objects.filter(
            id__in=[r.id for r in multiple_representatives[:2]]
        )

        with patch.object(admin, 'message_user'):
            admin.deactivate_representatives(admin_request, queryset)

        # Check all are deactivated
        for rep in queryset:
            rep.refresh_from_db()
            assert rep.is_active is False


# =============================================================================
# Representative History Admin Tests
# =============================================================================

class TestRepresentativeHistoryAdmin:
    """Tests for RepresentativeHistoryAdmin."""

    def test_admin_registered(self, site):
        """Test RepresentativeHistoryAdmin is properly configured."""
        admin = RepresentativeHistoryAdmin(RepresentativeHistory, site)
        assert admin is not None

    def test_list_display(self, site):
        """Test list_display configuration."""
        admin = RepresentativeHistoryAdmin(RepresentativeHistory, site)
        assert 'representative' in admin.list_display
        assert 'role' in admin.list_display
        assert 'snapshot_date' in admin.list_display

    def test_has_add_permission_false(self, site, admin_request):
        """Test cannot add history records."""
        admin = RepresentativeHistoryAdmin(RepresentativeHistory, site)
        assert admin.has_add_permission(admin_request) is False

    def test_has_change_permission_false(self, site, admin_request, representative_history):
        """Test cannot change history records."""
        admin = RepresentativeHistoryAdmin(RepresentativeHistory, site)
        assert admin.has_change_permission(admin_request, representative_history) is False


# =============================================================================
# Submission Notification Admin Tests
# =============================================================================

class TestSubmissionNotificationAdmin:
    """Tests for SubmissionNotificationAdmin."""

    def test_admin_registered(self, site):
        """Test SubmissionNotificationAdmin is properly configured."""
        admin = SubmissionNotificationAdmin(SubmissionNotification, site)
        assert admin is not None

    def test_list_display(self, site):
        """Test list_display configuration."""
        admin = SubmissionNotificationAdmin(SubmissionNotification, site)
        assert 'representative' in admin.list_display
        assert 'is_read' in admin.list_display
        assert 'is_emailed' in admin.list_display
        assert 'created_at' in admin.list_display

    def test_list_filter(self, site):
        """Test list_filter configuration."""
        admin = SubmissionNotificationAdmin(SubmissionNotification, site)
        assert 'is_read' in admin.list_filter
        assert 'is_emailed' in admin.list_filter

    def test_has_add_permission_false(self, site, admin_request):
        """Test cannot manually add notifications."""
        admin = SubmissionNotificationAdmin(SubmissionNotification, site)
        assert admin.has_add_permission(admin_request) is False

    def test_readonly_fields(self, site):
        """Test readonly fields are set."""
        admin = SubmissionNotificationAdmin(SubmissionNotification, site)
        assert 'representative' in admin.readonly_fields
        assert 'created_at' in admin.readonly_fields
