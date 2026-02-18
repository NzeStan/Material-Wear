"""
Tests for Academic Directory Utility Functions.

Tests cover:
- validators.py: Phone validation, email validation, year validation, data validation
- level_calculator.py: Level calculation, graduation detection, cohort years
- deduplication.py: Record merging, duplicate detection
- notifications.py: Notification helpers
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError

from academic_directory.utils.validators import (
    validate_nigerian_phone,
    normalize_phone_number,
    validate_email,
    validate_academic_year,
    validate_entry_year_for_class_rep,
    validate_tenure_year,
    validate_role_specific_fields,
    validate_submission_source,
    validate_representative_data,
    sanitize_text_input,
)
from academic_directory.utils.level_calculator import (
    calculate_current_level,
    get_academic_year_range,
    calculate_expected_graduation_year,
    has_graduated,
    is_final_year,
    get_level_display,
    get_cohort_year,
    validate_entry_year,
    validate_program_duration,
)
from academic_directory.utils.deduplication import (
    merge_representative_records,
    find_existing_representative,
    check_for_potential_duplicates,
    preview_merge_changes,
    handle_submission_with_deduplication,
)
from academic_directory.utils.notifications import (
    get_unread_notification_count,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    create_submission_notification,
    get_representative_email_context,
)


# =============================================================================
# Validator Tests
# =============================================================================

class TestPhoneValidation:
    """Tests for Nigerian phone number validation."""

    def test_valid_phone_with_plus234(self):
        """Test valid phone with +234 prefix."""
        assert validate_nigerian_phone('+2348012345678') is True

    def test_valid_phone_with_234(self):
        """Test valid phone with 234 prefix (no plus)."""
        assert validate_nigerian_phone('2348012345678') is True

    def test_valid_phone_with_zero(self):
        """Test valid phone with 0 prefix."""
        assert validate_nigerian_phone('08012345678') is True

    def test_valid_phone_ten_digits(self):
        """Test valid phone with just 10 digits."""
        assert validate_nigerian_phone('8012345678') is True

    def test_invalid_phone_empty(self):
        """Test empty phone is invalid."""
        assert validate_nigerian_phone('') is False

    def test_invalid_phone_none(self):
        """Test None phone is invalid."""
        assert validate_nigerian_phone(None) is False

    def test_invalid_phone_too_short(self):
        """Test too short phone is invalid."""
        assert validate_nigerian_phone('123456') is False

    def test_invalid_phone_wrong_prefix(self):
        """Test wrong starting digit is invalid."""
        assert validate_nigerian_phone('05012345678') is False

    def test_valid_phone_with_spaces(self):
        """Test phone with spaces is cleaned and validated."""
        assert validate_nigerian_phone('+234 801 234 5678') is True

    def test_valid_phone_with_dashes(self):
        """Test phone with dashes is cleaned and validated."""
        assert validate_nigerian_phone('+234-801-234-5678') is True

    def test_valid_mtn_number(self):
        """Test MTN number (0803, 0806, etc.)."""
        assert validate_nigerian_phone('08031234567') is True

    def test_valid_glo_number(self):
        """Test GLO number (0805, 0807, etc.)."""
        assert validate_nigerian_phone('08051234567') is True

    def test_valid_airtel_number(self):
        """Test Airtel number (0802, 0808, etc.)."""
        assert validate_nigerian_phone('08021234567') is True

    def test_valid_9mobile_number(self):
        """Test 9mobile number (0809, 0817, etc.)."""
        assert validate_nigerian_phone('08091234567') is True


class TestPhoneNormalization:
    """Tests for phone number normalization."""

    def test_normalize_zero_prefix(self):
        """Test normalizing 0-prefixed number."""
        assert normalize_phone_number('08012345678') == '+2348012345678'

    def test_normalize_234_prefix(self):
        """Test normalizing 234-prefixed number."""
        assert normalize_phone_number('2348012345678') == '+2348012345678'

    def test_normalize_already_correct(self):
        """Test already correct format remains unchanged."""
        assert normalize_phone_number('+2348012345678') == '+2348012345678'

    def test_normalize_ten_digits(self):
        """Test normalizing 10-digit number."""
        assert normalize_phone_number('8012345678') == '+2348012345678'

    def test_normalize_with_spaces(self):
        """Test normalizing number with spaces."""
        assert normalize_phone_number('080 1234 5678') == '+2348012345678'

    def test_normalize_invalid_raises(self):
        """Test normalizing invalid number raises ValidationError."""
        with pytest.raises(ValidationError):
            normalize_phone_number('invalid')


class TestEmailValidation:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email passes."""
        assert validate_email('test@example.com') is True

    def test_valid_email_with_subdomain(self):
        """Test email with subdomain passes."""
        assert validate_email('test@mail.example.com') is True

    def test_valid_email_with_plus(self):
        """Test email with plus sign passes."""
        assert validate_email('test+tag@example.com') is True

    def test_empty_email_is_valid(self):
        """Test empty email is valid (optional field)."""
        assert validate_email('') is True
        assert validate_email(None) is True

    def test_invalid_email_no_at(self):
        """Test email without @ is invalid."""
        assert validate_email('testexample.com') is False

    def test_invalid_email_no_domain(self):
        """Test email without domain is invalid."""
        assert validate_email('test@') is False


class TestAcademicYearValidation:
    """Tests for academic year validation."""

    def test_valid_current_year(self):
        """Test current year is valid."""
        current_year = datetime.now().year
        is_valid, error = validate_academic_year(current_year)
        assert is_valid is True
        assert error is None

    def test_valid_past_year(self):
        """Test past year (since 2000) is valid."""
        is_valid, error = validate_academic_year(2010)
        assert is_valid is True

    def test_invalid_too_old(self):
        """Test year before 2000 is invalid."""
        is_valid, error = validate_academic_year(1999)
        assert is_valid is False
        assert '2000' in error

    def test_invalid_far_future(self):
        """Test year too far in future is invalid."""
        current_year = datetime.now().year
        is_valid, error = validate_academic_year(current_year + 5)
        assert is_valid is False
        assert 'future' in error

    def test_invalid_none_year(self):
        """Test None year is invalid."""
        is_valid, error = validate_academic_year(None)
        assert is_valid is False


class TestRoleSpecificValidation:
    """Tests for role-specific field validation."""

    def test_class_rep_valid(self):
        """Test valid class rep fields."""
        is_valid, error = validate_role_specific_fields('CLASS_REP', 2022, None)
        assert is_valid is True

    def test_class_rep_missing_entry_year(self):
        """Test class rep without entry year is invalid."""
        is_valid, error = validate_role_specific_fields('CLASS_REP', None, None)
        assert is_valid is False
        assert 'entry year' in error.lower()

    def test_class_rep_with_tenure_invalid(self):
        """Test class rep with tenure is invalid."""
        is_valid, error = validate_role_specific_fields('CLASS_REP', 2022, 2022)
        assert is_valid is False
        assert 'tenure' in error.lower()

    def test_dept_president_valid(self):
        """Test valid dept president fields."""
        is_valid, error = validate_role_specific_fields('DEPT_PRESIDENT', None, 2022)
        assert is_valid is True

    def test_president_missing_tenure(self):
        """Test president without tenure is invalid."""
        is_valid, error = validate_role_specific_fields('DEPT_PRESIDENT', None, None)
        assert is_valid is False
        assert 'tenure' in error.lower()

    def test_president_with_entry_year_invalid(self):
        """Test president with entry year is invalid."""
        is_valid, error = validate_role_specific_fields('FACULTY_PRESIDENT', 2022, 2022)
        assert is_valid is False
        assert 'entry_year' in error.lower()

    def test_invalid_role(self):
        """Test invalid role is rejected."""
        is_valid, error = validate_role_specific_fields('INVALID', None, None)
        assert is_valid is False


class TestSubmissionSourceValidation:
    """Tests for submission source validation."""

    def test_valid_website_source(self):
        """Test WEBSITE source is valid."""
        is_valid, error = validate_submission_source('WEBSITE', None)
        assert is_valid is True

    def test_valid_other_with_detail(self):
        """Test OTHER source with detail is valid."""
        is_valid, error = validate_submission_source('OTHER', 'Social media')
        assert is_valid is True

    def test_other_without_detail_invalid(self):
        """Test OTHER source without detail is invalid."""
        is_valid, error = validate_submission_source('OTHER', None)
        assert is_valid is False

    def test_invalid_source(self):
        """Test invalid source is rejected."""
        is_valid, error = validate_submission_source('INVALID_SOURCE', None)
        assert is_valid is False


class TestRepresentativeDataValidation:
    """Tests for comprehensive representative data validation."""

    def test_valid_class_rep_data(self):
        """Test valid class rep data passes."""
        data = {
            'phone_number': '08012345678',
            'role': 'CLASS_REP',
            'entry_year': 2022,
        }
        is_valid, errors = validate_representative_data(data)
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_phone_number(self):
        """Test missing phone number is caught."""
        data = {
            'role': 'CLASS_REP',
            'entry_year': 2022,
        }
        is_valid, errors = validate_representative_data(data)
        assert is_valid is False
        assert 'phone_number' in errors

    def test_invalid_phone_format(self):
        """Test invalid phone format is caught."""
        data = {
            'phone_number': '123',
            'role': 'CLASS_REP',
            'entry_year': 2022,
        }
        is_valid, errors = validate_representative_data(data)
        assert is_valid is False
        assert 'phone_number' in errors

    def test_invalid_email_caught(self):
        """Test invalid email is caught."""
        data = {
            'phone_number': '08012345678',
            'email': 'invalid-email',
            'role': 'CLASS_REP',
            'entry_year': 2022,
        }
        is_valid, errors = validate_representative_data(data)
        assert is_valid is False
        assert 'email' in errors


class TestTextSanitization:
    """Tests for text input sanitization."""

    def test_trim_whitespace(self):
        """Test whitespace is trimmed."""
        assert sanitize_text_input('  hello  ') == 'hello'

    def test_max_length_enforced(self):
        """Test max length is enforced."""
        result = sanitize_text_input('hello world', max_length=5)
        assert result == 'hello'

    def test_empty_input(self):
        """Test empty input returns empty string."""
        assert sanitize_text_input('') == ''
        assert sanitize_text_input(None) == ''


# =============================================================================
# Level Calculator Tests
# =============================================================================

class TestLevelCalculation:
    """Tests for academic level calculation."""

    def test_calculate_first_year(self):
        """Test first year level calculation."""
        current_year = datetime.now().year
        level = calculate_current_level(current_year, 4)
        assert level == 100

    def test_calculate_second_year(self):
        """Test second year level calculation."""
        current_year = datetime.now().year
        level = calculate_current_level(current_year - 1, 4)
        assert level == 200

    def test_calculate_final_year_4_year(self):
        """Test final year for 4-year program."""
        current_year = datetime.now().year
        level = calculate_current_level(current_year - 3, 4)
        assert level == 400

    def test_calculate_final_year_5_year(self):
        """Test final year for 5-year program."""
        current_year = datetime.now().year
        level = calculate_current_level(current_year - 4, 5)
        assert level == 500

    def test_level_capped_at_final(self):
        """Test level is capped at final year."""
        current_year = datetime.now().year
        # Entry 6 years ago, 4-year program
        level = calculate_current_level(current_year - 5, 4)
        assert level == 400  # Capped at 400L

    def test_future_entry_returns_none(self):
        """Test future entry year returns None."""
        current_year = datetime.now().year
        level = calculate_current_level(current_year + 2, 4)
        assert level is None

    def test_invalid_duration_returns_none(self):
        """Test invalid duration returns None."""
        level = calculate_current_level(2022, 3)
        assert level is None
        level = calculate_current_level(2022, 8)
        assert level is None

    def test_none_inputs_return_none(self):
        """Test None inputs return None."""
        assert calculate_current_level(None, 4) is None
        assert calculate_current_level(2022, None) is None


class TestGraduationCalculation:
    """Tests for graduation year and status calculation."""

    def test_expected_graduation_year(self):
        """Test expected graduation year calculation."""
        result = calculate_expected_graduation_year(2022, 4)
        assert result == 2026

    def test_has_graduated_true(self):
        """Test has_graduated returns True for past graduation."""
        current_year = datetime.now().year
        # Entered 6 years ago, 4-year program
        assert has_graduated(current_year - 6, 4) is True

    def test_has_graduated_false(self):
        """Test has_graduated returns False for current student."""
        current_year = datetime.now().year
        assert has_graduated(current_year - 1, 4) is False

    def test_is_final_year_true(self):
        """Test is_final_year returns True for final year student."""
        current_year = datetime.now().year
        # 4th year of 4-year program
        assert is_final_year(current_year - 3, 4) is True

    def test_is_final_year_false(self):
        """Test is_final_year returns False for non-final year."""
        current_year = datetime.now().year
        # 2nd year of 4-year program
        assert is_final_year(current_year - 1, 4) is False

    def test_is_final_year_graduated_returns_false(self):
        """Test is_final_year returns False for graduated student."""
        current_year = datetime.now().year
        # Graduated student
        assert is_final_year(current_year - 6, 4) is False


class TestLevelDisplay:
    """Tests for level display formatting."""

    def test_level_display_format(self):
        """Test level display format (e.g., '300L')."""
        current_year = datetime.now().year
        display = get_level_display(current_year - 2, 4)
        assert display == '300L'

    def test_level_display_none_for_graduated(self):
        """Test level display returns formatted value even for graduated."""
        current_year = datetime.now().year
        display = get_level_display(current_year - 5, 4)
        # Returns 400L (capped)
        assert display == '400L'


class TestCohortYear:
    """Tests for cohort year formatting."""

    def test_cohort_year_format(self):
        """Test cohort year format (e.g., '2022/2023')."""
        assert get_cohort_year(2022) == '2022/2023'
        assert get_cohort_year(2023) == '2023/2024'


class TestAcademicYearRange:
    """Tests for academic year range calculation."""

    @patch('academic_directory.utils.level_calculator.datetime')
    def test_academic_year_before_september(self, mock_datetime):
        """Test academic year before September."""
        mock_datetime.now.return_value = datetime(2025, 3, 15)
        start, end = get_academic_year_range()
        assert start == 2024
        assert end == 2025

    @patch('academic_directory.utils.level_calculator.datetime')
    def test_academic_year_after_september(self, mock_datetime):
        """Test academic year after September."""
        mock_datetime.now.return_value = datetime(2025, 10, 15)
        start, end = get_academic_year_range()
        assert start == 2025
        assert end == 2026


class TestValidationHelpers:
    """Tests for validation helper functions."""

    def test_validate_entry_year_valid(self):
        """Test valid entry year passes."""
        current_year = datetime.now().year
        assert validate_entry_year(current_year) is True
        assert validate_entry_year(2020) is True

    def test_validate_entry_year_invalid(self):
        """Test invalid entry year fails."""
        assert validate_entry_year(1999) is False
        assert validate_entry_year(None) is False

    def test_validate_program_duration_valid(self):
        """Test valid duration passes."""
        for years in range(4, 8):
            assert validate_program_duration(years) is True

    def test_validate_program_duration_invalid(self):
        """Test invalid duration fails."""
        assert validate_program_duration(3) is False
        assert validate_program_duration(8) is False


# =============================================================================
# Deduplication Tests
# =============================================================================

class TestFindExistingRepresentative:
    """Tests for finding existing representatives."""

    def test_find_by_exact_phone(self, class_rep):
        """Test finding by exact phone number."""
        found = find_existing_representative(class_rep.phone_number)
        assert found == class_rep

    def test_find_by_unnormalized_phone(self, class_rep):
        """Test finding by unnormalized phone format."""
        # class_rep phone is +2348012345678, search with 08012345678
        unnormalized = class_rep.phone_number.replace('+234', '0')
        found = find_existing_representative(unnormalized)
        assert found == class_rep

    def test_find_nonexistent_returns_none(self, db):
        """Test finding nonexistent phone returns None."""
        found = find_existing_representative('+2348099999999')
        assert found is None

    def test_find_invalid_phone_returns_none(self, db):
        """Test finding with invalid phone returns None."""
        found = find_existing_representative('invalid')
        assert found is None


class TestMergeRecords:
    """Tests for merging representative records."""

    def test_merge_updates_fields(self, class_rep):
        """Test merge updates fields correctly."""
        new_data = {
            'full_name': 'Updated Name',
            'email': 'updated@example.com',
        }
        updated, changes = merge_representative_records(class_rep, new_data)
        assert updated.full_name == 'Updated Name'
        assert updated.email == 'updated@example.com'
        assert 'full_name' in changes
        assert 'email' in changes

    def test_merge_creates_history(self, class_rep):
        """Test merge creates history snapshot."""
        from academic_directory.models import RepresentativeHistory
        initial_count = RepresentativeHistory.objects.filter(representative=class_rep).count()

        new_data = {'full_name': 'New Name'}
        merge_representative_records(class_rep, new_data)

        new_count = RepresentativeHistory.objects.filter(representative=class_rep).count()
        # Merge creates history, and save() may also create history
        assert new_count > initial_count

    def test_merge_resets_verified_status(self, verified_representative):
        """Test merge resets VERIFIED status to UNVERIFIED."""
        new_data = {'full_name': 'Changed Name'}
        updated, changes = merge_representative_records(verified_representative, new_data)
        assert updated.verification_status == 'UNVERIFIED'
        assert 'verification_status' in changes

    def test_merge_preserves_unverified_status(self, class_rep):
        """Test merge preserves UNVERIFIED status."""
        assert class_rep.verification_status == 'UNVERIFIED'
        new_data = {'full_name': 'New Name'}
        updated, _ = merge_representative_records(class_rep, new_data)
        assert updated.verification_status == 'UNVERIFIED'

    def test_merge_no_changes_when_same(self, class_rep):
        """Test merge returns no changes when data is same."""
        new_data = {'full_name': class_rep.full_name}
        _, changes = merge_representative_records(class_rep, new_data)
        # No changes since it's the same value
        assert 'full_name' not in changes


class TestCheckDuplicates:
    """Tests for checking potential duplicates."""

    def test_check_duplicate_by_email(self, class_rep, department, program_duration):
        """Test finding duplicate by email."""
        from academic_directory.models import Representative
        current_year = datetime.now().year

        # Create another rep with same email
        other_rep = Representative.objects.create(
            full_name='Other Person',
            phone_number='+2348199999999',
            email=class_rep.email,
            department=department,
            faculty=department.faculty,
            university=department.faculty.university,
            role='CLASS_REP',
            entry_year=current_year,
        )

        data = {
            'phone_number': '+2348188888888',
            'email': class_rep.email,
        }
        duplicates = check_for_potential_duplicates(data)
        assert len(duplicates) >= 1

    def test_check_no_duplicates(self, class_rep):
        """Test no duplicates found for unique data."""
        data = {
            'phone_number': '+2348177777777',
            'email': 'unique@example.com',
            'full_name': 'Unique Person',
        }
        duplicates = check_for_potential_duplicates(data)
        assert len(duplicates) == 0


class TestPreviewMerge:
    """Tests for previewing merge changes."""

    def test_preview_shows_changes(self, class_rep):
        """Test preview shows field changes."""
        new_data = {
            'full_name': 'Preview Name',
            'email': 'preview@example.com',
        }
        preview = preview_merge_changes(class_rep, new_data)
        assert 'changes' in preview
        assert 'full_name' in preview['changes']
        assert preview['changes']['full_name']['incoming'] == 'Preview Name'

    def test_preview_shows_unchanged(self, class_rep):
        """Test preview shows unchanged fields."""
        new_data = {}
        preview = preview_merge_changes(class_rep, new_data)
        assert 'unchanged' in preview
        assert 'full_name' in preview['unchanged']


class TestHandleSubmissionWithDeduplication:
    """Tests for the main submission handler."""

    def test_handle_new_submission(self, department, program_duration):
        """Test handling a new submission creates new record."""
        current_year = datetime.now().year
        data = {
            'phone_number': '08012349999',
            'full_name': 'New Submission',
            'department_id': str(department.id),
            'role': 'CLASS_REP',
            'entry_year': current_year,
            'submission_source': 'WEBSITE',
        }
        record, is_new, result = handle_submission_with_deduplication(data)
        assert is_new is True
        assert record.full_name == 'New Submission'
        assert record.phone_number == '+2348012349999'

    def test_handle_duplicate_submission(self, class_rep):
        """Test handling duplicate submission merges records."""
        # Use existing phone but different format
        phone = class_rep.phone_number.replace('+234', '0')
        data = {
            'phone_number': phone,
            'full_name': 'Updated Via Dedup',
        }
        record, is_new, changes = handle_submission_with_deduplication(data)
        assert is_new is False
        assert record.id == class_rep.id
        assert 'full_name' in changes


# =============================================================================
# Notification Utility Tests
# =============================================================================

class TestNotificationUtilities:
    """Tests for notification utility functions."""

    def test_get_unread_count(self, multiple_notifications):
        """Test getting unread notification count."""
        count = get_unread_notification_count()
        assert count == len(multiple_notifications)

    def test_mark_notification_as_read_success(self, unread_notification, admin_user):
        """Test marking notification as read."""
        result = mark_notification_as_read(unread_notification.id, admin_user)
        assert result is True
        unread_notification.refresh_from_db()
        assert unread_notification.is_read is True

    def test_mark_notification_as_read_not_found(self, db):
        """Test marking nonexistent notification returns False."""
        import uuid
        result = mark_notification_as_read(uuid.uuid4(), None)
        assert result is False

    def test_mark_all_as_read(self, multiple_notifications, admin_user):
        """Test marking all notifications as read."""
        count = mark_all_notifications_as_read(admin_user)
        assert count == len(multiple_notifications)

        from academic_directory.models import SubmissionNotification
        unread = SubmissionNotification.objects.filter(is_read=False).count()
        assert unread == 0

    def test_create_submission_notification(self, class_rep):
        """Test creating submission notification."""
        from academic_directory.models import SubmissionNotification
        # First delete any existing notification
        SubmissionNotification.objects.filter(representative=class_rep).delete()

        notification = create_submission_notification(class_rep)
        assert notification.representative == class_rep
        assert notification.is_read is False

    def test_create_notification_idempotent(self, class_rep):
        """Test creating notification is idempotent (get_or_create)."""
        from academic_directory.models import SubmissionNotification
        SubmissionNotification.objects.filter(representative=class_rep).delete()

        notif1 = create_submission_notification(class_rep)
        notif2 = create_submission_notification(class_rep)
        assert notif1.id == notif2.id


class TestEmailContext:
    """Tests for email context helper."""

    @pytest.fixture
    def mock_settings(self):
        """Mock Django settings."""
        with patch('academic_directory.utils.notifications.settings') as mock:
            mock.SITE_URL = 'https://example.com'
            mock.COMPANY_NAME = 'Test Company'
            yield mock

    def test_email_context_for_class_rep(self, class_rep, mock_settings):
        """Test email context for class rep."""
        context = get_representative_email_context(class_rep)

        assert context['representative'] == class_rep
        assert context['full_name'] == class_rep.full_name
        assert context['phone_number'] == class_rep.phone_number
        assert context['university'] == class_rep.university.name
        assert 'current_level' in context
        assert 'entry_year' in context

    def test_email_context_for_president(self, dept_president, mock_settings):
        """Test email context for president."""
        context = get_representative_email_context(dept_president)

        assert context['representative'] == dept_president
        assert 'tenure_start_year' in context
        assert 'current_level' not in context or context.get('current_level') is None
