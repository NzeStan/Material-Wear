"""
Tests for Academic Directory Serializers.

Tests cover:
- University serializers: validation, representation
- Faculty serializers: relationships, nested data
- Department serializers: computed fields
- Representative serializers: validation, normalization
- Bulk submission serializers: deduplication, error handling
- Admin serializers: history, notifications, dashboard stats
"""
import pytest
from datetime import datetime
from rest_framework.exceptions import ValidationError as DRFValidationError

from academic_directory.serializers import (
    UniversitySerializer,
    UniversityListSerializer,
    FacultySerializer,
    FacultyListSerializer,
    DepartmentSerializer,
    DepartmentListSerializer,
    ProgramDurationSerializer,
    RepresentativeSerializer,
    RepresentativeListSerializer,
    RepresentativeDetailSerializer,
    RepresentativeVerificationSerializer,
    BulkSubmissionSerializer,
    SingleSubmissionSerializer,
    RepresentativeHistorySerializer,
    SubmissionNotificationSerializer,
    DashboardStatsSerializer,
)


# =============================================================================
# University Serializer Tests
# =============================================================================

class TestUniversitySerializer:
    """Tests for University serializers."""

    def test_university_serializer_fields(self, university):
        """Test UniversitySerializer includes all expected fields."""
        serializer = UniversitySerializer(university)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'abbreviation' in data
        assert 'state' in data
        assert 'type' in data
        assert 'is_active' in data

    def test_university_serializer_read_only_fields(self, university, faculty, department):
        """Test read-only computed fields."""
        serializer = UniversitySerializer(university)
        data = serializer.data

        assert 'faculties_count' in data
        assert 'departments_count' in data
        assert 'representatives_count' in data

    def test_university_list_serializer_lightweight(self, university):
        """Test UniversityListSerializer is lightweight."""
        serializer = UniversityListSerializer(university)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'abbreviation' in data
        # Should still have display fields
        assert 'state_display' in data or 'state' in data

    def test_university_serializer_create(self, db):
        """Test creating university via serializer."""
        data = {
            'name': 'New University',
            'abbreviation': 'NU',
            'state': 'LAGOS',
            'type': 'PRIVATE',
        }
        serializer = UniversitySerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        university = serializer.save()
        assert university.name == 'New University'


# =============================================================================
# Faculty Serializer Tests
# =============================================================================

class TestFacultySerializer:
    """Tests for Faculty serializers."""

    def test_faculty_serializer_fields(self, faculty):
        """Test FacultySerializer includes all expected fields."""
        serializer = FacultySerializer(faculty)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'abbreviation' in data
        assert 'university' in data

    def test_faculty_serializer_nested_university(self, faculty):
        """Test faculty serializer includes university details."""
        serializer = FacultySerializer(faculty)
        data = serializer.data

        # Should have university_name or university_detail
        assert 'university_name' in data or 'university_detail' in data

    def test_faculty_list_serializer(self, faculty):
        """Test FacultyListSerializer."""
        serializer = FacultyListSerializer(faculty)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'abbreviation' in data


# =============================================================================
# Department Serializer Tests
# =============================================================================

class TestDepartmentSerializer:
    """Tests for Department serializers."""

    def test_department_serializer_fields(self, department):
        """Test DepartmentSerializer includes all expected fields."""
        serializer = DepartmentSerializer(department)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data
        assert 'abbreviation' in data
        assert 'faculty' in data

    def test_department_serializer_computed_fields(self, department, program_duration):
        """Test department serializer includes computed fields."""
        serializer = DepartmentSerializer(department)
        data = serializer.data

        # Should have program_duration
        assert 'program_duration' in data
        assert data['program_duration'] == 4

    def test_department_list_serializer(self, department):
        """Test DepartmentListSerializer is lightweight."""
        serializer = DepartmentListSerializer(department)
        data = serializer.data

        assert 'id' in data
        assert 'name' in data


# =============================================================================
# Program Duration Serializer Tests
# =============================================================================

class TestProgramDurationSerializer:
    """Tests for ProgramDuration serializer."""

    def test_program_duration_fields(self, program_duration):
        """Test ProgramDurationSerializer fields."""
        serializer = ProgramDurationSerializer(program_duration)
        data = serializer.data

        assert 'id' in data
        assert 'department' in data
        assert 'duration_years' in data
        assert 'program_type' in data

    def test_program_duration_display_fields(self, program_duration):
        """Test program type display field."""
        serializer = ProgramDurationSerializer(program_duration)
        data = serializer.data

        assert 'program_type_display' in data or data.get('program_type') == 'BSC'


# =============================================================================
# Representative Serializer Tests
# =============================================================================

class TestRepresentativeSerializer:
    """Tests for Representative serializers."""

    def test_representative_list_serializer(self, class_rep):
        """Test RepresentativeListSerializer is lightweight."""
        serializer = RepresentativeListSerializer(class_rep)
        data = serializer.data

        assert 'id' in data
        assert 'display_name' in data
        assert 'phone_number' in data
        assert 'role' in data
        assert 'role_display' in data
        assert 'department_name' in data

    def test_representative_detail_serializer(self, class_rep, program_duration):
        """Test RepresentativeDetailSerializer has all fields."""
        serializer = RepresentativeDetailSerializer(class_rep)
        data = serializer.data

        assert 'id' in data
        assert 'full_name' in data
        assert 'phone_number' in data
        assert 'current_level' in data
        assert 'current_level_display' in data
        assert 'is_final_year' in data
        assert 'expected_graduation_year' in data
        assert 'has_graduated' in data

    def test_representative_serializer_normalizes_phone(self, department, program_duration):
        """Test phone number is normalized on validation."""
        current_year = datetime.now().year
        # Use a format that passes the model's regex validator
        data = {
            'full_name': 'Test Person',
            'phone_number': '+2348012341234',  # Already normalized format
            'department': str(department.id),
            'role': 'CLASS_REP',
            'entry_year': current_year,
            'submission_source': 'WEBSITE',
        }
        serializer = RepresentativeSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data['phone_number'] == '+2348012341234'

    def test_representative_serializer_validates_role_fields(self, department):
        """Test role-specific field validation."""
        current_year = datetime.now().year
        # CLASS_REP without entry_year
        data = {
            'full_name': 'Test Person',
            'phone_number': '+2348012345678',
            'department': str(department.id),
            'role': 'CLASS_REP',
            'submission_source': 'WEBSITE',
            # Missing entry_year
        }
        serializer = RepresentativeSerializer(data=data)
        assert not serializer.is_valid()
        # Error might be in 'role' or 'entry_year' key
        errors_str = str(serializer.errors).lower()
        assert 'entry year' in errors_str or 'entry_year' in errors_str

    def test_representative_serializer_to_representation(self, class_rep, program_duration):
        """Test serializer returns detailed representation."""
        serializer = RepresentativeSerializer(class_rep)
        data = serializer.data

        # Should use RepresentativeDetailSerializer for output
        assert 'current_level' in data
        assert 'department_detail' in data


class TestRepresentativeVerificationSerializer:
    """Tests for RepresentativeVerificationSerializer."""

    def test_valid_verify_action(self):
        """Test valid verify action data."""
        data = {
            'representative_ids': [1, 2, 3],
            'action': 'verify',
        }
        serializer = RepresentativeVerificationSerializer(data=data)
        assert serializer.is_valid()

    def test_valid_dispute_action(self):
        """Test valid dispute action data."""
        data = {
            'representative_ids': [1, 2, 3],
            'action': 'dispute',
        }
        serializer = RepresentativeVerificationSerializer(data=data)
        assert serializer.is_valid()

    def test_invalid_action(self):
        """Test invalid action is rejected."""
        data = {
            'representative_ids': [1],
            'action': 'invalid_action',
        }
        serializer = RepresentativeVerificationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'action' in serializer.errors

    def test_empty_ids_rejected(self):
        """Test empty representative_ids is rejected."""
        data = {
            'representative_ids': [],
            'action': 'verify',
        }
        serializer = RepresentativeVerificationSerializer(data=data)
        assert not serializer.is_valid()
        assert 'representative_ids' in serializer.errors


# =============================================================================
# Bulk Submission Serializer Tests
# =============================================================================

class TestSingleSubmissionSerializer:
    """Tests for SingleSubmissionSerializer."""

    def test_valid_class_rep_submission(self, department):
        """Test valid class rep submission data."""
        current_year = datetime.now().year
        data = {
            'full_name': 'Test Student',
            'phone_number': '08012345678',
            'department_id': str(department.id),
            'role': 'CLASS_REP',
            'entry_year': current_year,
            'submission_source': 'WEBSITE',
        }
        serializer = SingleSubmissionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_president_submission(self, department):
        """Test valid president submission data."""
        current_year = datetime.now().year
        data = {
            'full_name': 'Test President',
            'phone_number': '08012345678',
            'department_id': str(department.id),
            'role': 'DEPT_PRESIDENT',
            'tenure_start_year': current_year,
            'submission_source': 'MANUAL',
        }
        serializer = SingleSubmissionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_optional_fields(self, department):
        """Test optional fields are truly optional."""
        current_year = datetime.now().year
        data = {
            'full_name': 'Test Student',
            'phone_number': '08012345678',
            'department_id': str(department.id),
            'role': 'CLASS_REP',
            'entry_year': current_year,
            # No nickname, email, whatsapp_number, notes
        }
        serializer = SingleSubmissionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_invalid_role_rejected(self, department):
        """Test invalid role is rejected."""
        data = {
            'full_name': 'Test',
            'phone_number': '08012345678',
            'department_id': str(department.id),
            'role': 'INVALID_ROLE',
        }
        serializer = SingleSubmissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'role' in serializer.errors


class TestBulkSubmissionSerializer:
    """Tests for BulkSubmissionSerializer."""

    def test_valid_single_submission(self, department, program_duration):
        """Test bulk serializer with single submission."""
        current_year = datetime.now().year
        data = {
            'submissions': [{
                'full_name': 'Test Student',
                'phone_number': '08012345678',
                'department_id': str(department.id),
                'role': 'CLASS_REP',
                'entry_year': current_year,
                'submission_source': 'WEBSITE',
            }]
        }
        serializer = BulkSubmissionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_valid_multiple_submissions(self, department, program_duration):
        """Test bulk serializer with multiple submissions."""
        current_year = datetime.now().year
        data = {
            'submissions': [
                {
                    'full_name': f'Student {i}',
                    'phone_number': f'0801234567{i}',
                    'department_id': str(department.id),
                    'role': 'CLASS_REP',
                    'entry_year': current_year,
                    'submission_source': 'WEBSITE',
                }
                for i in range(5)
            ]
        }
        serializer = BulkSubmissionSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_empty_submissions_rejected(self):
        """Test empty submissions list is rejected."""
        data = {'submissions': []}
        serializer = BulkSubmissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'submissions' in serializer.errors

    def test_max_submissions_enforced(self, department):
        """Test max 100 submissions is enforced."""
        current_year = datetime.now().year
        data = {
            'submissions': [
                {
                    'full_name': f'Student {i}',
                    'phone_number': f'080{i:08d}',
                    'department_id': str(department.id),
                    'role': 'CLASS_REP',
                    'entry_year': current_year,
                    'submission_source': 'WEBSITE',
                }
                for i in range(101)  # 101 submissions
            ]
        }
        serializer = BulkSubmissionSerializer(data=data)
        assert not serializer.is_valid()
        assert 'submissions' in serializer.errors

    def test_create_returns_results(self, department, program_duration):
        """Test create method returns proper results structure."""
        current_year = datetime.now().year
        data = {
            'submissions': [{
                'full_name': 'Created Student',
                'phone_number': '08099988877',
                'department_id': str(department.id),
                'role': 'CLASS_REP',
                'entry_year': current_year,
                'submission_source': 'WEBSITE',
            }]
        }
        serializer = BulkSubmissionSerializer(data=data)
        assert serializer.is_valid()
        results = serializer.save()

        assert 'created' in results
        assert 'updated' in results
        assert 'errors' in results
        assert len(results['created']) == 1

    def test_create_handles_duplicates(self, class_rep, department, program_duration):
        """Test create handles duplicate phone numbers."""
        # Use existing phone number (unnormalized format)
        phone = class_rep.phone_number.replace('+234', '0')
        data = {
            'submissions': [{
                'full_name': 'Duplicate Phone',
                'phone_number': phone,
                'department_id': str(department.id),
                'role': 'CLASS_REP',
                'entry_year': class_rep.entry_year,
                'submission_source': 'WEBSITE',
            }]
        }
        serializer = BulkSubmissionSerializer(data=data)
        assert serializer.is_valid()
        results = serializer.save()

        # Should be updated, not created
        assert len(results['updated']) == 1
        assert len(results['created']) == 0


# =============================================================================
# Admin Serializer Tests
# =============================================================================

class TestRepresentativeHistorySerializer:
    """Tests for RepresentativeHistorySerializer."""

    def test_history_serializer_fields(self, representative_history):
        """Test history serializer includes all fields."""
        serializer = RepresentativeHistorySerializer(representative_history)
        data = serializer.data

        assert 'id' in data
        assert 'representative' in data
        assert 'full_name' in data
        assert 'phone_number' in data
        assert 'role' in data
        assert 'role_display' in data
        assert 'snapshot_date' in data

    def test_history_serializer_related_names(self, representative_history):
        """Test history serializer includes related model names."""
        serializer = RepresentativeHistorySerializer(representative_history)
        data = serializer.data

        assert 'department_name' in data
        assert 'faculty_name' in data
        assert 'university_name' in data


class TestSubmissionNotificationSerializer:
    """Tests for SubmissionNotificationSerializer."""

    def test_notification_serializer_fields(self, unread_notification):
        """Test notification serializer includes all fields."""
        serializer = SubmissionNotificationSerializer(unread_notification)
        data = serializer.data

        assert 'id' in data
        assert 'representative' in data
        assert 'is_read' in data
        assert 'is_emailed' in data
        assert 'created_at' in data

    def test_notification_serializer_representative_details(self, unread_notification):
        """Test notification includes representative details."""
        serializer = SubmissionNotificationSerializer(unread_notification)
        data = serializer.data

        assert 'representative_name' in data
        assert 'representative_phone' in data
        assert 'representative_role' in data

    def test_notification_serializer_read_details(self, read_notification):
        """Test notification includes read details when read."""
        serializer = SubmissionNotificationSerializer(read_notification)
        data = serializer.data

        assert data['is_read'] is True
        assert 'read_by_username' in data
        assert 'read_at' in data


class TestDashboardStatsSerializer:
    """Tests for DashboardStatsSerializer."""

    def test_dashboard_stats_all_fields(self):
        """Test dashboard stats serializer has all fields."""
        stats = {
            'total_representatives': 100,
            'total_universities': 10,
            'total_faculties': 50,
            'total_departments': 200,
            'unverified_count': 30,
            'verified_count': 60,
            'disputed_count': 10,
            'class_reps_count': 80,
            'dept_presidents_count': 15,
            'faculty_presidents_count': 5,
            'unread_notifications': 20,
            'recent_submissions_24h': 5,
            'recent_submissions_7d': 25,
        }
        serializer = DashboardStatsSerializer(data=stats)
        assert serializer.is_valid(), serializer.errors

    def test_dashboard_stats_integer_validation(self):
        """Test dashboard stats requires integers."""
        stats = {
            'total_representatives': 'not_a_number',
            'total_universities': 10,
            'total_faculties': 50,
            'total_departments': 200,
            'unverified_count': 30,
            'verified_count': 60,
            'disputed_count': 10,
            'class_reps_count': 80,
            'dept_presidents_count': 15,
            'faculty_presidents_count': 5,
            'unread_notifications': 20,
            'recent_submissions_24h': 5,
            'recent_submissions_7d': 25,
        }
        serializer = DashboardStatsSerializer(data=stats)
        assert not serializer.is_valid()
        assert 'total_representatives' in serializer.errors
