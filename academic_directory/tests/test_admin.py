# academic_directory/tests/test_admin.py
"""
Comprehensive test suite for academic_directory admin interface.

Test Coverage:
- UniversityAdmin (display, filters, search, autocomplete)
- FacultyAdmin (display, filters, relationships)
- DepartmentAdmin (display, filters, autocomplete)
- ProgramDurationAdmin (configuration)
- RepresentativeAdmin (display, actions, save_model)
- RepresentativeHistoryAdmin (readonly, permissions)
- SubmissionNotificationAdmin (display, permissions)
- Bulk actions (verify, dispute, deactivate)
- Badge rendering
- Fieldsets and readonly fields
"""

from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, Mock
from academic_directory.admin import (
    UniversityAdmin, FacultyAdmin, DepartmentAdmin,
    ProgramDurationAdmin, RepresentativeAdmin,
    RepresentativeHistoryAdmin, SubmissionNotificationAdmin
)
from academic_directory.models import (
    University, Faculty, Department, ProgramDuration,
    Representative, RepresentativeHistory, SubmissionNotification
)

User = get_user_model()


class AdminTestBase(TestCase):
    """Base class for admin tests."""
    
    def setUp(self):
        """Create common test data."""
        self.factory = RequestFactory()
        self.site = AdminSite()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create test data
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


class UniversityAdminTest(AdminTestBase):
    """Test UniversityAdmin."""
    
    def setUp(self):
        super().setUp()
        self.admin = UniversityAdmin(University, self.site)
    
    def test_list_display(self):
        """Test list_display configuration."""
        expected = ['abbreviation', 'name', 'state', 'type_badge', 'is_active']
        self.assertEqual(list(self.admin.list_display), expected)
    
    def test_list_filter(self):
        """Test list_filter configuration."""
        expected = ['type', 'state', 'is_active']
        self.assertEqual(list(self.admin.list_filter), expected)
    
    def test_search_fields(self):
        """Test search_fields configuration."""
        expected = ['name', 'abbreviation', 'state']
        self.assertEqual(list(self.admin.search_fields), expected)
    
    def test_ordering(self):
        """Test default ordering."""
        expected = ['name']
        self.assertEqual(list(self.admin.ordering), expected)
    
    def test_type_badge_federal(self):
        """Test type_badge renders correct color for FEDERAL."""
        badge_html = self.admin.type_badge(self.university)
        
        self.assertIn('#064E3B', badge_html)
        self.assertIn('Federal', badge_html)
    
    def test_type_badge_state(self):
        """Test type_badge renders correct color for STATE."""
        state_uni = University.objects.create(
            name="Lagos State University",
            abbreviation="LASU",
            state="LAGOS",
            type="STATE"
        )
        
        badge_html = self.admin.type_badge(state_uni)
        
        self.assertIn('#1D4ED8', badge_html)
        self.assertIn('State', badge_html)
    
    def test_type_badge_private(self):
        """Test type_badge renders correct color for PRIVATE."""
        private_uni = University.objects.create(
            name="Covenant University",
            abbreviation="CU",
            state="OGUN",
            type="PRIVATE"
        )
        
        badge_html = self.admin.type_badge(private_uni)
        
        self.assertIn('#7C3AED', badge_html)
        self.assertIn('Private', badge_html)
    
    def test_fieldsets_structure(self):
        """Test fieldsets configuration."""
        fieldsets = self.admin.fieldsets
        
        self.assertEqual(len(fieldsets), 3)
        self.assertEqual(fieldsets[0][0], 'Identity')
        self.assertEqual(fieldsets[1][0], 'Location & Classification')
        self.assertEqual(fieldsets[2][0], 'Status')


class FacultyAdminTest(AdminTestBase):
    """Test FacultyAdmin."""
    
    def setUp(self):
        super().setUp()
        self.admin = FacultyAdmin(Faculty, self.site)
    
    def test_list_display(self):
        """Test list_display configuration."""
        expected = ['abbreviation', 'name', 'university', 'is_active']
        self.assertEqual(list(self.admin.list_display), expected)
    
    def test_list_filter(self):
        """Test list_filter configuration."""
        expected = ['university', 'is_active']
        self.assertEqual(list(self.admin.list_filter), expected)
    
    def test_autocomplete_fields(self):
        """Test autocomplete is enabled for university."""
        expected = ['university']
        self.assertEqual(list(self.admin.autocomplete_fields), expected)
    
    def test_ordering(self):
        """Test ordering by university then faculty name."""
        expected = ['university__name', 'name']
        self.assertEqual(list(self.admin.ordering), expected)


class DepartmentAdminTest(AdminTestBase):
    """Test DepartmentAdmin."""
    
    def setUp(self):
        super().setUp()
        self.admin = DepartmentAdmin(Department, self.site)
    
    def test_list_display(self):
        """Test list_display configuration."""
        expected = ['abbreviation', 'name', 'faculty', 'university_display', 'is_active']
        self.assertEqual(list(self.admin.list_display), expected)
    
    def test_autocomplete_fields(self):
        """Test autocomplete is enabled for faculty."""
        expected = ['faculty']
        self.assertEqual(list(self.admin.autocomplete_fields), expected)
    
    def test_university_display(self):
        """Test university_display shows university abbreviation."""
        result = self.admin.university_display(self.department)
        
        self.assertEqual(result, 'UNN')


class ProgramDurationAdminTest(AdminTestBase):
    """Test ProgramDurationAdmin."""
    
    def setUp(self):
        super().setUp()
        self.admin = ProgramDurationAdmin(ProgramDuration, self.site)
        self.program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
    
    def test_list_display(self):
        """Test list_display configuration."""
        expected = ['department', 'duration_years', 'program_type']
        self.assertEqual(list(self.admin.list_display), expected)
    
    def test_autocomplete_fields(self):
        """Test autocomplete is enabled for department."""
        expected = ['department']
        self.assertEqual(list(self.admin.autocomplete_fields), expected)


class RepresentativeAdminTest(AdminTestBase):
    """Test RepresentativeAdmin."""
    
    def setUp(self):
        super().setUp()
        self.admin = RepresentativeAdmin(Representative, self.site)
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_list_display(self):
        """Test list_display configuration."""
        expected = [
            'display_name', 'phone_number', 'role_badge',
            'department', 'level_display', 'verification_badge', 
            'is_active', 'created_at'
        ]
        self.assertEqual(list(self.admin.list_display), expected)
    
    def test_list_filter(self):
        """Test list_filter configuration."""
        expected = [
            'role', 'verification_status', 'is_active',
            'university', 'faculty', 'submission_source'
        ]
        self.assertEqual(list(self.admin.list_filter), expected)
    
    def test_readonly_fields(self):
        """Test readonly fields configuration."""
        readonly = self.admin.readonly_fields
        
        self.assertIn('university', readonly)
        self.assertIn('faculty', readonly)
        self.assertIn('current_level_display', readonly)
        self.assertIn('verified_by', readonly)
        self.assertIn('verified_at', readonly)
    
    def test_autocomplete_fields(self):
        """Test autocomplete is enabled for department."""
        expected = ['department']
        self.assertEqual(list(self.admin.autocomplete_fields), expected)
    
    def test_role_badge_class_rep(self):
        """Test role_badge renders correct color for CLASS_REP."""
        badge_html = self.admin.role_badge(self.rep)
        
        self.assertIn('#064E3B', badge_html)
        self.assertIn('Class Rep', badge_html)
    
    def test_role_badge_dept_president(self):
        """Test role_badge renders correct color for DEPT_PRESIDENT."""
        dept_pres = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT"
        )
        
        badge_html = self.admin.role_badge(dept_pres)
        
        self.assertIn('#F59E0B', badge_html)
        self.assertIn('Dept. President', badge_html)
    
    def test_verification_badge_unverified(self):
        """Test verification_badge for UNVERIFIED status."""
        badge_html = self.admin.verification_badge(self.rep)
        
        self.assertIn('#F59E0B', badge_html)
        self.assertIn('Unverified', badge_html)
    
    def test_verification_badge_verified(self):
        """Test verification_badge for VERIFIED status."""
        self.rep.verification_status = 'VERIFIED'
        self.rep.save()
        
        badge_html = self.admin.verification_badge(self.rep)
        
        self.assertIn('#064E3B', badge_html)
        self.assertIn('Verified', badge_html)
    
    def test_level_display_for_class_rep(self):
        """Test level_display shows level for class reps."""
        result = self.admin.level_display(self.rep)
        
        # Should show level (currently 600 Level for 2020 entry in 2026)
        self.assertIn('Level', result)
    
    def test_level_display_for_non_class_rep(self):
        """Test level_display shows N/A for non-class reps."""
        dept_pres = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="DEPT_PRESIDENT"
        )
        
        result = self.admin.level_display(dept_pres)
        
        self.assertEqual(result, 'N/A')
    
    def test_actions_registered(self):
        """Test bulk actions are registered."""
        actions = self.admin.actions
        
        self.assertIn('verify_representatives', actions)
        self.assertIn('dispute_representatives', actions)
        self.assertIn('deactivate_representatives', actions)


class RepresentativeAdminSaveModelTest(AdminTestBase):
    """Test RepresentativeAdmin.save_model() method."""
    
    def setUp(self):
        super().setUp()
        self.admin = RepresentativeAdmin(Representative, self.site)
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            verification_status='UNVERIFIED'
        )
    
    def test_save_model_sets_verified_by_on_verification(self):
        """Test save_model sets verified_by when verifying."""
        request = self.factory.post('/')
        request.user = self.admin_user
        
        # Change status to VERIFIED
        self.rep.verification_status = 'VERIFIED'
        
        # Mock form
        form = Mock()
        
        self.admin.save_model(request, self.rep, form, change=True)
        
        # Should set verified_by
        self.assertEqual(self.rep.verified_by, self.admin_user)
        self.assertIsNotNone(self.rep.verified_at)
    
    def test_save_model_clears_verified_by_on_dispute(self):
        """Test save_model clears verified_by when disputing."""
        # First verify
        self.rep.verification_status = 'VERIFIED'
        self.rep.verified_by = self.admin_user
        self.rep.verified_at = timezone.now()
        self.rep.save()
        
        request = self.factory.post('/')
        request.user = self.admin_user
        
        # Change status to DISPUTED
        self.rep.verification_status = 'DISPUTED'
        
        form = Mock()
        
        self.admin.save_model(request, self.rep, form, change=True)
        
        # Should clear verification metadata
        self.assertIsNone(self.rep.verified_by)
        self.assertIsNone(self.rep.verified_at)
    
    def test_save_model_clears_verified_by_on_unverify(self):
        """Test save_model clears verified_by when changing back to UNVERIFIED."""
        # First verify
        self.rep.verification_status = 'VERIFIED'
        self.rep.verified_by = self.admin_user
        self.rep.verified_at = timezone.now()
        self.rep.save()
        
        request = self.factory.post('/')
        request.user = self.admin_user
        
        # Change back to UNVERIFIED
        self.rep.verification_status = 'UNVERIFIED'
        
        form = Mock()
        
        self.admin.save_model(request, self.rep, form, change=True)
        
        # Should clear verification metadata
        self.assertIsNone(self.rep.verified_by)
        self.assertIsNone(self.rep.verified_at)
    
    def test_save_model_preserves_verified_by_when_status_unchanged(self):
        """Test save_model preserves verified_by when status doesn't change."""
        # First verify
        self.rep.verification_status = 'VERIFIED'
        self.rep.verified_by = self.admin_user
        verified_at = timezone.now()
        self.rep.verified_at = verified_at
        self.rep.save()
        
        request = self.factory.post('/')
        request.user = self.admin_user
        
        # Change some other field
        self.rep.notes = "Updated notes"
        
        form = Mock()
        
        self.admin.save_model(request, self.rep, form, change=True)
        
        # Should preserve verification metadata
        self.assertEqual(self.rep.verified_by, self.admin_user)
        self.assertEqual(self.rep.verified_at, verified_at)


class RepresentativeAdminBulkActionsTest(AdminTestBase):
    """Test RepresentativeAdmin bulk actions."""
    
    def setUp(self):
        super().setUp()
        self.admin = RepresentativeAdmin(Representative, self.site)
        
        # Create multiple representatives
        self.reps = []
        for i in range(3):
            rep = Representative.objects.create(
                full_name=f"Student {i}",
                phone_number=f"0801234567{i}",
                department=self.department,
                faculty=self.faculty,
                university=self.university,
                role="CLASS_REP",
                entry_year=2020
            )
            self.reps.append(rep)
    
    @patch('academic_directory.admin.send_bulk_verification_email')
    def test_verify_representatives_action(self, mock_send_email):
        """Test verify_representatives bulk action."""
        request = self.factory.post('/')
        request.user = self.admin_user
        request._messages = Mock()
        
        queryset = Representative.objects.filter(id__in=[r.id for r in self.reps])
        
        self.admin.verify_representatives(request, queryset)
        
        # All should be verified
        for rep in self.reps:
            rep.refresh_from_db()
            self.assertEqual(rep.verification_status, 'VERIFIED')
            self.assertEqual(rep.verified_by, self.admin_user)
            self.assertIsNotNone(rep.verified_at)
        
        # Should send email
        mock_send_email.assert_called_once()
    
    def test_dispute_representatives_action(self):
        """Test dispute_representatives bulk action."""
        # First verify all
        for rep in self.reps:
            rep.verification_status = 'VERIFIED'
            rep.verified_by = self.admin_user
            rep.verified_at = timezone.now()
            rep.save()
        
        request = self.factory.post('/')
        request.user = self.admin_user
        request._messages = Mock()
        
        queryset = Representative.objects.filter(id__in=[r.id for r in self.reps])
        
        self.admin.dispute_representatives(request, queryset)
        
        # All should be disputed
        for rep in self.reps:
            rep.refresh_from_db()
            self.assertEqual(rep.verification_status, 'DISPUTED')
            self.assertIsNone(rep.verified_by)
            self.assertIsNone(rep.verified_at)
    
    def test_deactivate_representatives_action(self):
        """Test deactivate_representatives bulk action."""
        request = self.factory.post('/')
        request.user = self.admin_user
        request._messages = Mock()
        
        queryset = Representative.objects.filter(id__in=[r.id for r in self.reps])
        
        self.admin.deactivate_representatives(request, queryset)
        
        # All should be deactivated
        for rep in self.reps:
            rep.refresh_from_db()
            self.assertFalse(rep.is_active)
            self.assertIn('Bulk deactivation by admin', rep.notes or '')


class RepresentativeHistoryAdminTest(AdminTestBase):
    """Test RepresentativeHistoryAdmin."""
    
    def setUp(self):
        super().setUp()
        self.admin = RepresentativeHistoryAdmin(RepresentativeHistory, self.site)
        
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        self.history = RepresentativeHistory.objects.create(
            representative=rep,
            full_name=rep.full_name,
            phone_number=rep.phone_number,
            role=rep.role,
            entry_year=rep.entry_year,
            verification_status=rep.verification_status,
            is_active=rep.is_active,
            department=rep.department,
            faculty=rep.faculty,
            university=rep.university
        )
    
    def test_has_add_permission_false(self):
        """Test add permission is disabled."""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        self.assertFalse(self.admin.has_add_permission(request))
    
    def test_has_change_permission_false(self):
        """Test change permission is disabled."""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        self.assertFalse(self.admin.has_change_permission(request, self.history))
    
    def test_all_fields_readonly(self):
        """Test all important fields are readonly."""
        readonly = self.admin.readonly_fields
        
        self.assertIn('representative', readonly)
        self.assertIn('full_name', readonly)
        self.assertIn('phone_number', readonly)
        self.assertIn('role', readonly)
        self.assertIn('verification_status', readonly)


class SubmissionNotificationAdminTest(AdminTestBase):
    """Test SubmissionNotificationAdmin."""
    
    def setUp(self):
        super().setUp()
        self.admin = SubmissionNotificationAdmin(SubmissionNotification, self.site)
        
        rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        self.notification = SubmissionNotification.objects.create(
            representative=rep
        )
    
    def test_list_display(self):
        """Test list_display configuration."""
        expected = ['representative', 'is_read', 'is_emailed', 'created_at', 'read_at']
        self.assertEqual(list(self.admin.list_display), expected)
    
    def test_list_filter(self):
        """Test list_filter configuration."""
        expected = ['is_read', 'is_emailed']
        self.assertEqual(list(self.admin.list_filter), expected)
    
    def test_has_add_permission_false(self):
        """Test add permission is disabled."""
        request = self.factory.get('/')
        request.user = self.admin_user
        
        self.assertFalse(self.admin.has_add_permission(request))
    
    def test_readonly_fields(self):
        """Test readonly fields configuration."""
        readonly = self.admin.readonly_fields
        
        self.assertIn('representative', readonly)
        self.assertIn('is_emailed', readonly)
        self.assertIn('emailed_at', readonly)
        self.assertIn('created_at', readonly)
        self.assertIn('read_at', readonly)
        self.assertIn('read_by', readonly)


class AdminIntegrationTest(AdminTestBase):
    """Test admin interface integration scenarios."""
    
    def setUp(self):
        super().setUp()
        self.rep_admin = RepresentativeAdmin(Representative, self.site)
    
    def test_cascading_autocomplete_department_to_university(self):
        """Test that selecting department auto-fills university and faculty."""
        # This tests the readonly relationship fields
        rep = Representative.objects.create(
            full_name="Test Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        # University and faculty should be automatically set from department
        self.assertEqual(rep.university, self.department.faculty.university)
        self.assertEqual(rep.faculty, self.department.faculty)
    
    @patch('academic_directory.admin.send_bulk_verification_email')
    def test_bulk_verify_then_dispute(self, mock_send_email):
        """Test bulk verify followed by bulk dispute."""
        rep = Representative.objects.create(
            full_name="Test Student",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        request = self.factory.post('/')
        request.user = self.admin_user
        request._messages = Mock()
        
        queryset = Representative.objects.filter(id=rep.id)
        
        # Verify
        self.rep_admin.verify_representatives(request, queryset)
        rep.refresh_from_db()
        self.assertEqual(rep.verification_status, 'VERIFIED')
        
        # Dispute
        self.rep_admin.dispute_representatives(request, queryset)
        rep.refresh_from_db()
        self.assertEqual(rep.verification_status, 'DISPUTED')
        self.assertIsNone(rep.verified_by)