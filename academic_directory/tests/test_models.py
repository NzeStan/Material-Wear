"""
Tests for Academic Directory Models.

Tests cover:
- University model: creation, validation, properties, clean method
- Faculty model: creation, validation, relationships, properties
- Department model: creation, validation, relationships, properties
- ProgramDuration model: creation, validation, constraints
- Representative model: creation, validation, computed properties, methods
- RepresentativeHistory model: creation, snapshots
- SubmissionNotification model: creation, methods
"""
import pytest
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from academic_directory.models import (
    University,
    Faculty,
    Department,
    ProgramDuration,
    Representative,
    RepresentativeHistory,
    SubmissionNotification,
)


# =============================================================================
# University Model Tests
# =============================================================================

class TestUniversityModel:
    """Tests for the University model."""

    def test_create_university(self, db):
        """Test creating a basic university."""
        university = University.objects.create(
            name='Test University',
            abbreviation='TU',
            state='LAGOS',
            type='FEDERAL',
        )
        assert university.name == 'Test University'
        assert university.abbreviation == 'TU'
        assert university.state == 'LAGOS'
        assert university.type == 'FEDERAL'
        assert university.is_active is True
        assert university.id is not None

    def test_university_str_representation(self, university):
        """Test string representation of university."""
        assert str(university) == f"{university.abbreviation} - {university.name}"

    def test_university_abbreviation_uppercase(self, db):
        """Test that abbreviation is converted to uppercase."""
        university = University.objects.create(
            name='Lowercase Test',
            abbreviation='lt',
            state='LAGOS',
            type='FEDERAL',
        )
        assert university.abbreviation == 'LT'

    def test_university_name_cannot_be_empty(self, db):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            University.objects.create(
                name='   ',
                abbreviation='TEST',
                state='LAGOS',
                type='FEDERAL',
            )
        assert 'name' in str(exc_info.value)

    def test_university_name_unique(self, university, db):
        """Test that duplicate names are not allowed."""
        with pytest.raises(IntegrityError):
            University.objects.create(
                name=university.name,
                abbreviation='DIFF',
                state='LAGOS',
                type='FEDERAL',
            )

    def test_university_abbreviation_unique(self, university, db):
        """Test that duplicate abbreviations are not allowed."""
        with pytest.raises(IntegrityError):
            University.objects.create(
                name='Different University',
                abbreviation=university.abbreviation,
                state='LAGOS',
                type='FEDERAL',
            )

    def test_university_abbreviation_only_letters(self, db):
        """Test abbreviation validation (uppercase letters only)."""
        with pytest.raises(ValidationError):
            university = University(
                name='Test Uni',
                abbreviation='TEST123',
                state='LAGOS',
                type='FEDERAL',
            )
            university.full_clean()

    def test_university_faculties_count(self, university, faculty, faculty_science, inactive_faculty):
        """Test faculties_count property returns only active faculties."""
        assert university.faculties_count == 2  # faculty and faculty_science, not inactive

    def test_university_departments_count(self, university, faculty, department, department_ee, inactive_department):
        """Test departments_count property."""
        assert university.departments_count == 2  # department and department_ee, not inactive

    def test_university_representatives_count(self, university, class_rep, dept_president):
        """Test representatives_count property."""
        # Both reps are in the same university
        assert university.representatives_count == 2

    def test_university_type_choices(self, db):
        """Test valid university types."""
        for uni_type, _ in University.UNIVERSITY_TYPES:
            university = University.objects.create(
                name=f'Test {uni_type} University',
                abbreviation=uni_type[:3],
                state='LAGOS',
                type=uni_type,
            )
            assert university.type == uni_type

    def test_university_state_choices(self, db):
        """Test that all Nigerian states are valid."""
        assert len(University.NIGERIAN_STATES) == 37


# =============================================================================
# Faculty Model Tests
# =============================================================================

class TestFacultyModel:
    """Tests for the Faculty model."""

    def test_create_faculty(self, university):
        """Test creating a basic faculty."""
        faculty = Faculty.objects.create(
            university=university,
            name='Faculty of Arts',
            abbreviation='ARTS',
        )
        assert faculty.name == 'Faculty of Arts'
        assert faculty.abbreviation == 'ARTS'
        assert faculty.university == university
        assert faculty.is_active is True

    def test_faculty_str_representation(self, faculty):
        """Test string representation of faculty."""
        expected = f"{faculty.university.abbreviation} - {faculty.name}"
        assert str(faculty) == expected

    def test_faculty_abbreviation_uppercase(self, university):
        """Test that abbreviation is converted to uppercase."""
        faculty = Faculty.objects.create(
            university=university,
            name='Test Faculty',
            abbreviation='test',
        )
        assert faculty.abbreviation == 'TEST'

    def test_faculty_name_cannot_be_empty(self, university):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError):
            Faculty.objects.create(
                university=university,
                name='   ',
                abbreviation='TEST',
            )

    def test_faculty_unique_together(self, faculty):
        """Test that same name cannot exist in same university."""
        with pytest.raises(IntegrityError):
            Faculty.objects.create(
                university=faculty.university,
                name=faculty.name,
                abbreviation='DIFF',
            )

    def test_faculty_departments_count(self, faculty, department, department_ee, inactive_department):
        """Test departments_count property returns only active departments."""
        assert faculty.departments_count == 2

    def test_faculty_representatives_count(self, faculty, class_rep, dept_president):
        """Test representatives_count property."""
        assert faculty.representatives_count == 2

    def test_faculty_full_name(self, faculty):
        """Test full_name property."""
        expected = f"{faculty.university.abbreviation} - {faculty.name}"
        assert faculty.full_name == expected

    def test_faculty_cascade_delete(self, faculty, department):
        """Test that deleting university cascades to faculties."""
        university = faculty.university
        university.delete()
        assert not Faculty.objects.filter(id=faculty.id).exists()


# =============================================================================
# Department Model Tests
# =============================================================================

class TestDepartmentModel:
    """Tests for the Department model."""

    def test_create_department(self, faculty):
        """Test creating a basic department."""
        department = Department.objects.create(
            faculty=faculty,
            name='Physics',
            abbreviation='PHY',
        )
        assert department.name == 'Physics'
        assert department.abbreviation == 'PHY'
        assert department.faculty == faculty
        assert department.is_active is True

    def test_department_str_representation(self, department):
        """Test string representation of department."""
        expected = f"{department.faculty.university.abbreviation} - {department.faculty.abbreviation} - {department.name}"
        assert str(department) == expected

    def test_department_abbreviation_uppercase(self, faculty):
        """Test that abbreviation is converted to uppercase."""
        department = Department.objects.create(
            faculty=faculty,
            name='Test Dept',
            abbreviation='test',
        )
        assert department.abbreviation == 'TEST'

    def test_department_university_property(self, department):
        """Test university property returns correct university."""
        assert department.university == department.faculty.university

    def test_department_representatives_count(self, department, class_rep, dept_president):
        """Test representatives_count property."""
        # Both reps are in the same department
        assert department.representatives_count == 2

    def test_department_program_duration_property(self, department, program_duration):
        """Test program_duration property returns correct value."""
        assert department.program_duration == 4

    def test_department_program_duration_none(self, faculty):
        """Test program_duration returns None when not set."""
        department = Department.objects.create(
            faculty=faculty,
            name='No Duration Dept',
            abbreviation='NDD',
        )
        assert department.program_duration is None

    def test_department_full_name(self, department):
        """Test full_name property."""
        expected = f"{department.faculty.university.abbreviation} - {department.faculty.abbreviation} - {department.name}"
        assert department.full_name == expected

    def test_department_unique_together(self, department):
        """Test that same name cannot exist in same faculty."""
        with pytest.raises(IntegrityError):
            Department.objects.create(
                faculty=department.faculty,
                name=department.name,
                abbreviation='DIFF',
            )


# =============================================================================
# ProgramDuration Model Tests
# =============================================================================

class TestProgramDurationModel:
    """Tests for the ProgramDuration model."""

    def test_create_program_duration(self, department):
        """Test creating a basic program duration."""
        program = ProgramDuration.objects.create(
            department=department,
            duration_years=4,
            program_type='BSC',
        )
        assert program.duration_years == 4
        assert program.program_type == 'BSC'
        assert program.department == department

    def test_program_duration_str_representation(self, program_duration):
        """Test string representation."""
        assert str(program_duration.department.full_name) in str(program_duration)
        assert '4 years' in str(program_duration)

    def test_program_duration_min_years(self, department):
        """Test minimum duration validation (4 years)."""
        with pytest.raises(ValidationError):
            ProgramDuration.objects.create(
                department=department,
                duration_years=3,
                program_type='BSC',
            )

    def test_program_duration_max_years(self, department):
        """Test maximum duration validation (7 years)."""
        with pytest.raises(ValidationError):
            ProgramDuration.objects.create(
                department=department,
                duration_years=8,
                program_type='MBBS',
            )

    def test_program_duration_valid_range(self, faculty):
        """Test all valid duration values."""
        for years in range(4, 8):  # 4, 5, 6, 7
            department = Department.objects.create(
                faculty=faculty,
                name=f'Dept {years}',
                abbreviation=f'D{years}',
            )
            program = ProgramDuration.objects.create(
                department=department,
                duration_years=years,
                program_type='BSC',
            )
            assert program.duration_years == years

    def test_program_duration_one_to_one(self, program_duration, department):
        """Test that department can only have one program duration."""
        with pytest.raises(IntegrityError):
            ProgramDuration.objects.create(
                department=department,
                duration_years=5,
                program_type='BENG',
            )

    def test_program_duration_faculty_property(self, program_duration):
        """Test faculty property."""
        assert program_duration.faculty == program_duration.department.faculty

    def test_program_duration_university_property(self, program_duration):
        """Test university property."""
        assert program_duration.university == program_duration.department.faculty.university

    def test_program_duration_types(self, faculty):
        """Test all program types are valid."""
        for i, (prog_type, _) in enumerate(ProgramDuration.PROGRAM_TYPES):
            dept = Department.objects.create(
                faculty=faculty,
                name=f'Type Test {i}',
                abbreviation=f'TT{i}',
            )
            program = ProgramDuration.objects.create(
                department=dept,
                duration_years=4,
                program_type=prog_type,
            )
            assert program.program_type == prog_type


# =============================================================================
# Representative Model Tests
# =============================================================================

class TestRepresentativeModel:
    """Tests for the Representative model."""

    def test_create_class_rep(self, department, program_duration):
        """Test creating a class representative."""
        current_year = datetime.now().year
        rep = Representative.objects.create(
            full_name='Test Student',
            phone_number='+2348111111111',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year - 1,
            submission_source='WEBSITE',
        )
        assert rep.full_name == 'Test Student'
        assert rep.role == 'CLASS_REP'
        assert rep.entry_year == current_year - 1
        assert rep.is_active is True
        assert rep.verification_status == 'UNVERIFIED'

    def test_create_dept_president(self, department):
        """Test creating a department president."""
        current_year = datetime.now().year
        rep = Representative.objects.create(
            full_name='Dept Pres',
            phone_number='+2348222222222',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='DEPT_PRESIDENT',
            tenure_start_year=current_year,
            submission_source='MANUAL',
        )
        assert rep.role == 'DEPT_PRESIDENT'
        assert rep.tenure_start_year == current_year

    def test_representative_str_representation(self, class_rep):
        """Test string representation."""
        expected = f"{class_rep.display_name} - {class_rep.get_role_display()} ({class_rep.department.abbreviation})"
        assert str(class_rep) == expected

    def test_representative_phone_number_unique(self, class_rep, department):
        """Test phone number uniqueness."""
        current_year = datetime.now().year
        with pytest.raises(IntegrityError):
            Representative.objects.create(
                full_name='Duplicate Phone',
                phone_number=class_rep.phone_number,
                department=department,
                faculty=department.faculty,
                university=department.faculty.university,
                role='CLASS_REP',
                entry_year=current_year,
            )

    def test_phone_number_auto_format_0_prefix(self, department, program_duration):
        """Test phone number starting with 0 is auto-formatted."""
        current_year = datetime.now().year
        rep = Representative.objects.create(
            full_name='Phone Test',
            phone_number='08099999999',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year,
        )
        assert rep.phone_number == '+2348099999999'

    def test_phone_number_auto_format_234_prefix(self, department, program_duration):
        """Test phone number starting with 234 is auto-formatted."""
        current_year = datetime.now().year
        rep = Representative.objects.create(
            full_name='Phone Test 2',
            phone_number='2348088888888',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year,
        )
        assert rep.phone_number == '+2348088888888'

    def test_denormalized_fields_auto_populated(self, department):
        """Test faculty and university are auto-populated from department."""
        current_year = datetime.now().year
        rep = Representative(
            full_name='Denorm Test',
            phone_number='+2348077777777',
            department=department,
            role='DEPT_PRESIDENT',
            tenure_start_year=current_year,
        )
        rep.save()
        assert rep.faculty == department.faculty
        assert rep.university == department.faculty.university

    def test_class_rep_requires_entry_year(self, department):
        """Test class rep without entry_year raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Representative.objects.create(
                full_name='No Entry Year',
                phone_number='+2348066666666',
                department=department,
                faculty=department.faculty,
                university=department.faculty.university,
                role='CLASS_REP',
            )
        assert 'entry_year' in str(exc_info.value)

    def test_class_rep_cannot_have_tenure(self, department, program_duration):
        """Test class rep with tenure_start_year raises validation error."""
        current_year = datetime.now().year
        with pytest.raises(ValidationError) as exc_info:
            Representative.objects.create(
                full_name='Invalid Class Rep',
                phone_number='+2348055555555',
                department=department,
                faculty=department.faculty,
                university=department.faculty.university,
                role='CLASS_REP',
                entry_year=current_year,
                tenure_start_year=current_year,
            )
        assert 'tenure_start_year' in str(exc_info.value)

    def test_president_requires_tenure(self, department):
        """Test president without tenure_start_year raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Representative.objects.create(
                full_name='No Tenure Pres',
                phone_number='+2348044444444',
                department=department,
                faculty=department.faculty,
                university=department.faculty.university,
                role='DEPT_PRESIDENT',
            )
        assert 'tenure_start_year' in str(exc_info.value)

    def test_president_cannot_have_entry_year(self, department):
        """Test president with entry_year raises validation error."""
        current_year = datetime.now().year
        with pytest.raises(ValidationError) as exc_info:
            Representative.objects.create(
                full_name='Invalid Pres',
                phone_number='+2348033333333',
                department=department,
                faculty=department.faculty,
                university=department.faculty.university,
                role='DEPT_PRESIDENT',
                entry_year=current_year,
                tenure_start_year=current_year,
            )
        assert 'entry_year' in str(exc_info.value)

    def test_other_submission_source_requires_detail(self, department, program_duration):
        """Test OTHER submission source requires submission_source_other."""
        current_year = datetime.now().year
        with pytest.raises(ValidationError) as exc_info:
            Representative.objects.create(
                full_name='Other Source',
                phone_number='+2348022222222',
                department=department,
                faculty=department.faculty,
                university=department.faculty.university,
                role='CLASS_REP',
                entry_year=current_year,
                submission_source='OTHER',
            )
        assert 'submission_source_other' in str(exc_info.value)

    def test_display_name_with_nickname(self, class_rep):
        """Test display_name returns nickname when available."""
        class_rep.nickname = 'JD'
        class_rep.save()
        assert class_rep.display_name == 'JD'

    def test_display_name_without_nickname(self, dept_president):
        """Test display_name returns full_name when no nickname."""
        dept_president.nickname = None
        dept_president.save()
        assert dept_president.display_name == dept_president.full_name

    def test_current_level_calculation(self, class_rep, program_duration):
        """Test current level calculation."""
        current_year = datetime.now().year
        class_rep.entry_year = current_year - 2
        class_rep.save()
        # 3rd year = 300L
        assert class_rep.current_level == 300

    def test_current_level_display(self, class_rep, program_duration):
        """Test current level display format."""
        current_year = datetime.now().year
        class_rep.entry_year = current_year - 2
        class_rep.save()
        assert class_rep.current_level_display == '300L'

    def test_current_level_none_for_president(self, dept_president):
        """Test current_level returns None for presidents."""
        assert dept_president.current_level is None

    def test_is_final_year(self, final_year_class_rep, program_duration):
        """Test is_final_year detection."""
        assert final_year_class_rep.is_final_year is True

    def test_is_not_final_year(self, class_rep, program_duration):
        """Test is_final_year returns False for non-final year."""
        current_year = datetime.now().year
        class_rep.entry_year = current_year - 1
        class_rep.save()
        assert class_rep.is_final_year is False

    def test_expected_graduation_year(self, class_rep, program_duration):
        """Test expected graduation year calculation."""
        expected = class_rep.entry_year + 4  # 4-year program
        assert class_rep.expected_graduation_year == expected

    def test_has_graduated(self, graduated_class_rep, program_duration):
        """Test has_graduated detection."""
        assert graduated_class_rep.has_graduated is True

    def test_has_not_graduated(self, class_rep, program_duration):
        """Test has_graduated returns False for current students."""
        assert class_rep.has_graduated is False

    def test_verify_method(self, class_rep, admin_user):
        """Test verify method sets correct fields."""
        class_rep.verify(admin_user)
        assert class_rep.verification_status == 'VERIFIED'
        assert class_rep.verified_by == admin_user
        assert class_rep.verified_at is not None

    def test_dispute_method(self, verified_representative):
        """Test dispute method clears verification."""
        verified_representative.dispute()
        assert verified_representative.verification_status == 'DISPUTED'
        assert verified_representative.verified_by is None
        assert verified_representative.verified_at is None

    def test_deactivate_method(self, class_rep):
        """Test deactivate method."""
        class_rep.deactivate(reason='Test deactivation')
        assert class_rep.is_active is False
        assert 'Test deactivation' in class_rep.notes

    def test_check_and_update_status_graduates(self, graduated_class_rep, program_duration):
        """Test check_and_update_status auto-deactivates graduated reps."""
        result = graduated_class_rep.check_and_update_status()
        assert result is True
        graduated_class_rep.refresh_from_db()
        assert graduated_class_rep.is_active is False

    def test_check_and_update_status_current_student(self, class_rep, program_duration):
        """Test check_and_update_status does nothing for current students."""
        result = class_rep.check_and_update_status()
        assert result is False
        assert class_rep.is_active is True

    def test_history_created_on_update(self, class_rep):
        """Test that history entry is created when representative is updated."""
        initial_count = RepresentativeHistory.objects.filter(representative=class_rep).count()
        class_rep.full_name = 'Updated Name'
        class_rep.save()
        new_count = RepresentativeHistory.objects.filter(representative=class_rep).count()
        assert new_count == initial_count + 1


# =============================================================================
# RepresentativeHistory Model Tests
# =============================================================================

class TestRepresentativeHistoryModel:
    """Tests for the RepresentativeHistory model."""

    def test_create_history(self, class_rep):
        """Test creating a history snapshot."""
        history = RepresentativeHistory.objects.create(
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
        )
        assert history.full_name == class_rep.full_name
        assert history.snapshot_date is not None

    def test_history_str_representation(self, representative_history):
        """Test string representation."""
        assert representative_history.full_name in str(representative_history)
        assert representative_history.role in str(representative_history)

    def test_create_from_representative_classmethod(self, class_rep):
        """Test create_from_representative class method."""
        history = RepresentativeHistory.create_from_representative(class_rep)
        assert history.representative == class_rep
        assert history.full_name == class_rep.full_name
        assert history.phone_number == class_rep.phone_number
        assert history.department == class_rep.department

    def test_role_display_property(self, representative_history):
        """Test role_display property."""
        assert representative_history.role_display == 'Class Representative'

    def test_history_ordering(self, class_rep):
        """Test history is ordered by -snapshot_date."""
        for i in range(3):
            RepresentativeHistory.create_from_representative(class_rep)

        histories = list(RepresentativeHistory.objects.filter(representative=class_rep))
        for i in range(len(histories) - 1):
            assert histories[i].snapshot_date >= histories[i + 1].snapshot_date


# =============================================================================
# SubmissionNotification Model Tests
# =============================================================================

class TestSubmissionNotificationModel:
    """Tests for the SubmissionNotification model."""

    def test_create_notification(self, department, program_duration):
        """Test creating a notification."""
        from datetime import datetime
        current_year = datetime.now().year
        # Create a new rep specifically for this test to avoid signal conflicts
        rep = Representative.objects.create(
            full_name='Notification Test Rep',
            phone_number='+2348012399999',
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year,
            submission_source='WEBSITE',
        )
        # Signal creates notification - get it
        notification = SubmissionNotification.objects.get(representative=rep)
        assert notification.is_read is False
        assert notification.is_emailed is False
        assert notification.created_at is not None

    def test_notification_str_representation(self, unread_notification):
        """Test string representation."""
        assert 'Unread' in str(unread_notification)
        assert unread_notification.representative.display_name in str(unread_notification)

    def test_mark_as_read_without_user(self, unread_notification):
        """Test mark_as_read without user."""
        unread_notification.mark_as_read()
        assert unread_notification.is_read is True
        assert unread_notification.read_at is not None
        assert unread_notification.read_by is None

    def test_mark_as_read_with_user(self, unread_notification, admin_user):
        """Test mark_as_read with user."""
        unread_notification.mark_as_read(admin_user)
        assert unread_notification.is_read is True
        assert unread_notification.read_by == admin_user

    def test_mark_as_emailed(self, unread_notification):
        """Test mark_as_emailed method."""
        unread_notification.mark_as_emailed()
        assert unread_notification.is_emailed is True
        assert unread_notification.emailed_at is not None

    def test_get_unread_count_classmethod(self, multiple_notifications):
        """Test get_unread_count class method."""
        count = SubmissionNotification.get_unread_count()
        assert count == len(multiple_notifications)

    def test_get_unread_count_excludes_read(self, multiple_notifications, admin_user):
        """Test get_unread_count excludes read notifications."""
        initial_count = SubmissionNotification.get_unread_count()
        multiple_notifications[0].mark_as_read(admin_user)
        new_count = SubmissionNotification.get_unread_count()
        assert new_count == initial_count - 1

    def test_get_pending_email_notifications(self, multiple_notifications):
        """Test get_pending_email_notifications class method."""
        pending = SubmissionNotification.get_pending_email_notifications()
        assert pending.count() == len(multiple_notifications)

    def test_get_pending_excludes_emailed(self, multiple_notifications):
        """Test pending notifications excludes already emailed."""
        initial_count = SubmissionNotification.get_pending_email_notifications().count()
        multiple_notifications[0].mark_as_emailed()
        new_count = SubmissionNotification.get_pending_email_notifications().count()
        assert new_count == initial_count - 1

    def test_notification_one_to_one(self, unread_notification, class_rep):
        """Test one-to-one relationship with representative."""
        with pytest.raises(IntegrityError):
            SubmissionNotification.objects.create(
                representative=class_rep,
            )
