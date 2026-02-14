# academic_directory/tests/utils/test_validators.py
"""
Comprehensive test suite for validators utility.

Test Coverage:
- Nigerian phone number validation
- Phone number normalization
- Email validation
- Representative data validation
- Role-specific field validation
- Submission source validation
- Text sanitization
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from academic_directory.utils.validators import (
    validate_nigerian_phone,
    normalize_phone_number,
    validate_email,
    validate_role_specific_fields,
    validate_submission_source,
    validate_representative_data,
    sanitize_text_input
)


class ValidateNigerianPhoneTest(TestCase):
    """Test Nigerian phone number validation."""
    
    def test_valid_phone_with_plus_234(self):
        """Test valid phone starting with +234."""
        self.assertTrue(validate_nigerian_phone('+2348012345678'))
        self.assertTrue(validate_nigerian_phone('+2347012345678'))
        self.assertTrue(validate_nigerian_phone('+2349012345678'))
    
    def test_valid_phone_with_234(self):
        """Test valid phone starting with 234."""
        self.assertTrue(validate_nigerian_phone('2348012345678'))
        self.assertTrue(validate_nigerian_phone('2347012345678'))
    
    def test_valid_phone_with_zero(self):
        """Test valid phone starting with 0."""
        self.assertTrue(validate_nigerian_phone('08012345678'))
        self.assertTrue(validate_nigerian_phone('07012345678'))
        self.assertTrue(validate_nigerian_phone('09012345678'))
    
    def test_valid_phone_without_zero(self):
        """Test valid phone 10 digits without leading zero."""
        self.assertTrue(validate_nigerian_phone('8012345678'))
        self.assertTrue(validate_nigerian_phone('7012345678'))
    
    def test_phone_with_spaces(self):
        """Test phone with spaces is valid after cleaning."""
        self.assertTrue(validate_nigerian_phone('0801 234 5678'))
        self.assertTrue(validate_nigerian_phone('+234 801 234 5678'))
    
    def test_phone_with_dashes(self):
        """Test phone with dashes is valid after cleaning."""
        self.assertTrue(validate_nigerian_phone('0801-234-5678'))
        self.assertTrue(validate_nigerian_phone('+234-801-234-5678'))
    
    def test_invalid_phone_too_short(self):
        """Test phone number too short is invalid."""
        self.assertFalse(validate_nigerian_phone('0801234'))
        self.assertFalse(validate_nigerian_phone('801234'))
    
    def test_invalid_phone_too_long(self):
        """Test phone number too long is invalid."""
        self.assertFalse(validate_nigerian_phone('080123456789999'))
    
    def test_invalid_phone_wrong_prefix(self):
        """Test phone with wrong prefix is invalid."""
        self.assertFalse(validate_nigerian_phone('0601234567'))  # Should start with 07, 08, or 09
        self.assertFalse(validate_nigerian_phone('1234567890'))
    
    def test_invalid_phone_empty(self):
        """Test empty phone is invalid."""
        self.assertFalse(validate_nigerian_phone(''))
        self.assertFalse(validate_nigerian_phone(None))
    
    def test_invalid_phone_letters(self):
        """Test phone with letters is invalid."""
        self.assertFalse(validate_nigerian_phone('08012ABCDEF'))


class NormalizePhoneNumberTest(TestCase):
    """Test phone number normalization."""
    
    def test_normalize_from_plus_234(self):
        """Test normalization from +234 format."""
        self.assertEqual(
            normalize_phone_number('+2348012345678'),
            '+2348012345678'
        )
    
    def test_normalize_from_234(self):
        """Test normalization from 234 format."""
        self.assertEqual(
            normalize_phone_number('2348012345678'),
            '+2348012345678'
        )
    
    def test_normalize_from_zero(self):
        """Test normalization from 0 format."""
        self.assertEqual(
            normalize_phone_number('08012345678'),
            '+2348012345678'
        )
    
    def test_normalize_from_ten_digits(self):
        """Test normalization from 10 digits."""
        self.assertEqual(
            normalize_phone_number('8012345678'),
            '+2348012345678'
        )
    
    def test_normalize_with_spaces(self):
        """Test normalization removes spaces."""
        self.assertEqual(
            normalize_phone_number('0801 234 5678'),
            '+2348012345678'
        )
    
    def test_normalize_with_dashes(self):
        """Test normalization removes dashes."""
        self.assertEqual(
            normalize_phone_number('0801-234-5678'),
            '+2348012345678'
        )
    
    def test_normalize_invalid_raises_error(self):
        """Test normalization of invalid phone raises ValidationError."""
        with self.assertRaises(ValidationError):
            normalize_phone_number('1234567890')
    
    def test_normalize_empty_raises_error(self):
        """Test normalization of empty phone raises ValidationError."""
        with self.assertRaises(ValidationError):
            normalize_phone_number('')


class ValidateEmailTest(TestCase):
    """Test email validation."""
    
    def test_valid_email(self):
        """Test valid email addresses."""
        self.assertTrue(validate_email('test@example.com'))
        self.assertTrue(validate_email('user.name@domain.co.uk'))
        self.assertTrue(validate_email('user+tag@example.com'))
    
    def test_empty_email_is_valid(self):
        """Test empty email is valid (optional field)."""
        self.assertTrue(validate_email(''))
        self.assertTrue(validate_email(None))
    
    def test_invalid_email_no_at(self):
        """Test email without @ is invalid."""
        self.assertFalse(validate_email('invalidemail.com'))
    
    def test_invalid_email_no_domain(self):
        """Test email without domain is invalid."""
        self.assertFalse(validate_email('user@'))
    
    def test_invalid_email_no_extension(self):
        """Test email without extension is invalid."""
        self.assertFalse(validate_email('user@domain'))


class ValidateRoleSpecificFieldsTest(TestCase):
    """Test role-specific field validation."""
    
    def test_class_rep_requires_entry_year(self):
        """Test CLASS_REP requires entry_year."""
        is_valid, error = validate_role_specific_fields('CLASS_REP', None, None)
        self.assertFalse(is_valid)
        self.assertIn('entry_year', error.lower())
    
    def test_class_rep_valid_with_entry_year(self):
        """Test CLASS_REP is valid with entry_year."""
        is_valid, error = validate_role_specific_fields('CLASS_REP', 2020, None)
        self.assertTrue(is_valid)
        self.assertEqual(error, '')
    
    def test_class_rep_cannot_have_tenure_year(self):
        """Test CLASS_REP cannot have tenure_start_year."""
        is_valid, error = validate_role_specific_fields('CLASS_REP', 2020, 2024)
        self.assertFalse(is_valid)
        self.assertIn('tenure', error.lower())
    
    def test_dept_president_requires_tenure_year(self):
        """Test DEPT_PRESIDENT requires tenure_start_year."""
        is_valid, error = validate_role_specific_fields('DEPT_PRESIDENT', None, None)
        self.assertFalse(is_valid)
        self.assertIn('tenure', error.lower())
    
    def test_dept_president_valid_with_tenure_year(self):
        """Test DEPT_PRESIDENT is valid with tenure_start_year."""
        is_valid, error = validate_role_specific_fields('DEPT_PRESIDENT', None, 2024)
        self.assertTrue(is_valid)
    
    def test_dept_president_cannot_have_entry_year(self):
        """Test DEPT_PRESIDENT cannot have entry_year."""
        is_valid, error = validate_role_specific_fields('DEPT_PRESIDENT', 2020, 2024)
        self.assertFalse(is_valid)
        self.assertIn('entry_year', error.lower())
    
    def test_faculty_president_requires_tenure_year(self):
        """Test FACULTY_PRESIDENT requires tenure_start_year."""
        is_valid, error = validate_role_specific_fields('FACULTY_PRESIDENT', None, None)
        self.assertFalse(is_valid)
    
    def test_faculty_president_valid_with_tenure_year(self):
        """Test FACULTY_PRESIDENT is valid with tenure_start_year."""
        is_valid, error = validate_role_specific_fields('FACULTY_PRESIDENT', None, 2024)
        self.assertTrue(is_valid)


class ValidateSubmissionSourceTest(TestCase):
    """Test submission source validation."""
    
    def test_valid_standard_sources(self):
        """Test valid standard submission sources."""
        valid_sources = ['WEBSITE', 'WHATSAPP', 'EMAIL', 'PHONE', 'SMS', 'MANUAL', 'IMPORT']
        for source in valid_sources:
            is_valid, error = validate_submission_source(source, None)
            self.assertTrue(is_valid, f"{source} should be valid")
    
    def test_other_requires_description(self):
        """Test OTHER source requires submission_source_other."""
        is_valid, error = validate_submission_source('OTHER', None)
        self.assertFalse(is_valid)
        self.assertIn('specify', error.lower())
    
    def test_other_valid_with_description(self):
        """Test OTHER source is valid with description."""
        is_valid, error = validate_submission_source('OTHER', 'In-person at event')
        self.assertTrue(is_valid)


class ValidateRepresentativeDataTest(TestCase):
    """Test comprehensive representative data validation."""
    
    def test_valid_data(self):
        """Test validation passes for valid data."""
        data = {
            'phone_number': '08012345678',
            'email': 'test@example.com',
            'role': 'CLASS_REP',
            'entry_year': 2020,
            'submission_source': 'WEBSITE'
        }
        is_valid, errors = validate_representative_data(data)
        
        self.assertTrue(is_valid)
        self.assertEqual(errors, {})
    
    def test_missing_phone_number(self):
        """Test validation fails for missing phone."""
        data = {
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        is_valid, errors = validate_representative_data(data)
        
        self.assertFalse(is_valid)
        self.assertIn('phone_number', errors)
    
    def test_invalid_phone_number(self):
        """Test validation fails for invalid phone."""
        data = {
            'phone_number': 'invalid',
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        is_valid, errors = validate_representative_data(data)
        
        self.assertFalse(is_valid)
        self.assertIn('phone_number', errors)
    
    def test_invalid_email(self):
        """Test validation fails for invalid email."""
        data = {
            'phone_number': '08012345678',
            'email': 'invalid-email',
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        is_valid, errors = validate_representative_data(data)
        
        self.assertFalse(is_valid)
        self.assertIn('email', errors)
    
    def test_role_validation_integrated(self):
        """Test role validation is integrated."""
        data = {
            'phone_number': '08012345678',
            'role': 'CLASS_REP',
            # Missing entry_year
        }
        is_valid, errors = validate_representative_data(data)
        
        self.assertFalse(is_valid)
        self.assertIn('entry_year', errors)
    
    def test_submission_source_validation_integrated(self):
        """Test submission source validation is integrated."""
        data = {
            'phone_number': '08012345678',
            'role': 'CLASS_REP',
            'entry_year': 2020,
            'submission_source': 'OTHER'
            # Missing submission_source_other
        }
        is_valid, errors = validate_representative_data(data)
        
        self.assertFalse(is_valid)
        self.assertIn('submission_source', errors)


class SanitizeTextInputTest(TestCase):
    """Test text input sanitization."""
    
    def test_trims_whitespace(self):
        """Test whitespace is trimmed."""
        self.assertEqual(sanitize_text_input('  test  '), 'test')
        self.assertEqual(sanitize_text_input('\ntest\n'), 'test')
    
    def test_limits_length(self):
        """Test length is limited when max_length specified."""
        long_text = 'a' * 100
        result = sanitize_text_input(long_text, max_length=50)
        self.assertEqual(len(result), 50)
    
    def test_handles_empty(self):
        """Test empty input returns empty string."""
        self.assertEqual(sanitize_text_input(''), '')
        self.assertEqual(sanitize_text_input(None), '')
    
    def test_no_length_limit_without_max_length(self):
        """Test no length limit when max_length not specified."""
        long_text = 'a' * 1000
        result = sanitize_text_input(long_text)
        self.assertEqual(len(result), 1000)