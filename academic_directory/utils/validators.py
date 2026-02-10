"""
Validators Utility

Custom validation functions for the Academic Directory app.
"""

import re
from typing import Optional, Tuple
from django.core.exceptions import ValidationError
from datetime import datetime


def validate_nigerian_phone(phone_number: str) -> bool:
    """
    Validate Nigerian phone number format.
    
    Accepts formats:
    - +2348012345678
    - 2348012345678
    - 08012345678
    - 8012345678
    
    Args:
        phone_number: Phone number to validate
    
    Returns:
        bool: True if valid, False otherwise
    
    Examples:
        >>> validate_nigerian_phone('+2348012345678')
        True
        >>> validate_nigerian_phone('08012345678')
        True
        >>> validate_nigerian_phone('1234567890')
        False
    """
    if not phone_number:
        return False
    
    # Remove spaces and dashes
    cleaned = phone_number.replace(' ', '').replace('-', '')
    
    # Pattern 1: +234XXXXXXXXXX (11 digits after +234)
    pattern1 = r'^\+234[7-9][0-1]\d{8}$'
    
    # Pattern 2: 234XXXXXXXXXX (11 digits after 234)
    pattern2 = r'^234[7-9][0-1]\d{8}$'
    
    # Pattern 3: 0XXXXXXXXXX (11 digits starting with 0)
    pattern3 = r'^0[7-9][0-1]\d{8}$'
    
    # Pattern 4: XXXXXXXXXX (10 digits)
    pattern4 = r'^[7-9][0-1]\d{8}$'
    
    patterns = [pattern1, pattern2, pattern3, pattern4]
    
    return any(re.match(pattern, cleaned) for pattern in patterns)


def normalize_phone_number(phone_number: str) -> str:
    """
    Normalize Nigerian phone number to international format (+234...).
    
    Args:
        phone_number: Phone number to normalize
    
    Returns:
        str: Normalized phone number in format +234XXXXXXXXXX
    
    Raises:
        ValidationError: If phone number is invalid
    
    Examples:
        >>> normalize_phone_number('08012345678')
        '+2348012345678'
        >>> normalize_phone_number('2348012345678')
        '+2348012345678'
    """
    if not validate_nigerian_phone(phone_number):
        raise ValidationError(f"Invalid Nigerian phone number: {phone_number}")
    
    # Remove spaces and dashes
    cleaned = phone_number.replace(' ', '').replace('-', '')
    
    # Already in correct format
    if cleaned.startswith('+234'):
        return cleaned
    
    # Has 234 prefix but no +
    if cleaned.startswith('234'):
        return f'+{cleaned}'
    
    # Starts with 0
    if cleaned.startswith('0'):
        return f'+234{cleaned[1:]}'
    
    # Just the 10 digits
    return f'+234{cleaned}'


def validate_email(email: Optional[str]) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate (can be None/empty)
    
    Returns:
        bool: True if valid or empty, False otherwise
    """
    if not email:
        return True  # Email is optional
    
    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_academic_year(year: int, min_year: int = 2000) -> Tuple[bool, Optional[str]]:
    """
    Validate academic year is reasonable.
    
    Args:
        year: Year to validate
        min_year: Minimum acceptable year (default: 2000)
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    
    Examples:
        >>> validate_academic_year(2022)
        (True, None)
        >>> validate_academic_year(1990)
        (False, 'Academic year cannot be before 2000')
    """
    if not year:
        return False, "Academic year is required"
    
    current_year = datetime.now().year
    
    if year < min_year:
        return False, f"Academic year cannot be before {min_year}"
    
    if year > current_year + 2:
        return False, f"Academic year cannot be more than 2 years in the future"
    
    return True, None


def validate_entry_year_for_class_rep(entry_year: int, program_duration: int) -> Tuple[bool, Optional[str]]:
    """
    Validate entry year for a class representative.
    
    Ensures:
    - Entry year is valid
    - Student hasn't graduated yet
    
    Args:
        entry_year: Year student entered program
        program_duration: Duration of program in years
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    # Validate the year itself
    is_valid, error = validate_academic_year(entry_year)
    if not is_valid:
        return False, error
    
    # Check if already graduated
    from .level_calculator import has_graduated
    
    if has_graduated(entry_year, program_duration):
        expected_grad_year = entry_year + program_duration
        return False, f"Student has already graduated (expected graduation: {expected_grad_year})"
    
    return True, None


def validate_tenure_year(tenure_start_year: int) -> Tuple[bool, Optional[str]]:
    """
    Validate tenure start year for department/faculty presidents.
    
    Args:
        tenure_start_year: Year representative took office
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    return validate_academic_year(tenure_start_year)


def validate_role_specific_fields(role: str, entry_year: Optional[int], 
                                  tenure_start_year: Optional[int]) -> Tuple[bool, Optional[str]]:
    """
    Validate that role-specific fields are provided correctly.
    
    Rules:
    - CLASS_REP must have entry_year, not tenure_start_year
    - DEPT_PRESIDENT and FACULTY_PRESIDENT must have tenure_start_year, not entry_year
    
    Args:
        role: Representative role
        entry_year: Entry year (for class reps)
        tenure_start_year: Tenure start year (for presidents)
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    if role == 'CLASS_REP':
        if not entry_year:
            return False, "Entry year is required for class representatives"
        if tenure_start_year:
            return False, "Class representatives should not have tenure_start_year"
    
    elif role in ['DEPT_PRESIDENT', 'FACULTY_PRESIDENT']:
        if not tenure_start_year:
            return False, "Tenure start year is required for presidents"
        if entry_year:
            return False, "Presidents should not have entry_year (use tenure_start_year instead)"
    
    else:
        return False, f"Invalid role: {role}"
    
    return True, None


def validate_submission_source(source: str, source_other: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate submission source fields.
    
    Args:
        source: Submission source choice
        source_other: Free text if source is 'OTHER'
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    valid_sources = ['WEBSITE', 'WHATSAPP', 'EMAIL', 'PHONE', 'SMS', 'MANUAL', 'IMPORT', 'OTHER']
    
    if source not in valid_sources:
        return False, f"Invalid submission source: {source}"
    
    if source == 'OTHER' and not source_other:
        return False, "Please specify the submission source when 'Other' is selected"
    
    return True, None


def validate_representative_data(data: dict) -> Tuple[bool, dict]:
    """
    Comprehensive validation for representative data.
    
    Args:
        data: Dictionary containing representative data
    
    Returns:
        Tuple[bool, dict]: (is_valid, errors_dict)
    
    Example:
        >>> data = {'phone_number': '08012345678', 'role': 'CLASS_REP', 'entry_year': 2022}
        >>> is_valid, errors = validate_representative_data(data)
    """
    errors = {}
    
    # Validate phone number
    phone = data.get('phone_number')
    if not phone:
        errors['phone_number'] = "Phone number is required"
    elif not validate_nigerian_phone(phone):
        errors['phone_number'] = "Invalid Nigerian phone number format"
    
    # Validate email (if provided)
    email = data.get('email')
    if email and not validate_email(email):
        errors['email'] = "Invalid email address format"
    
    # Validate role-specific fields
    role = data.get('role')
    entry_year = data.get('entry_year')
    tenure_start_year = data.get('tenure_start_year')
    
    if role:
        is_valid, error = validate_role_specific_fields(role, entry_year, tenure_start_year)
        if not is_valid:
            if 'entry_year' in error.lower():
                errors['entry_year'] = error
            elif 'tenure' in error.lower():
                errors['tenure_start_year'] = error
            else:
                errors['role'] = error
    
    # Validate submission source
    source = data.get('submission_source')
    source_other = data.get('submission_source_other')
    if source:
        is_valid, error = validate_submission_source(source, source_other)
        if not is_valid:
            errors['submission_source'] = error
    
    return len(errors) == 0, errors


def sanitize_text_input(text: Optional[str], max_length: Optional[int] = None) -> str:
    """
    Sanitize text input by trimming whitespace and optionally limiting length.
    
    Args:
        text: Text to sanitize
        max_length: Optional maximum length
    
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Trim whitespace
    sanitized = text.strip()
    
    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized
