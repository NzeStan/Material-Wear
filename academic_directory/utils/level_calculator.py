"""
Level Calculator Utility

Handles academic progression calculations for class representatives.
"""

from datetime import datetime
from typing import Optional, Tuple


def calculate_current_level(entry_year: int, program_duration: int) -> Optional[int]:
    """
    Calculate current academic level based on entry year and program duration.
    
    The calculation accounts for:
    - Current calendar year
    - Years elapsed since entry
    - Capping at final year (doesn't go beyond program duration)
    - Handling students who haven't started yet
    
    Args:
        entry_year: Year the student entered the program (e.g., 2022)
        program_duration: Duration of program in years (4-7)
    
    Returns:
        int: Current level in Nigerian format (100, 200, 300, 400, 500, 600, 700)
             or None if invalid inputs or student hasn't started
    
    Examples:
        >>> calculate_current_level(2022, 4)  # Current year: 2025
        400  # 4th year (final year for 4-year program)
        
        >>> calculate_current_level(2023, 5)  # Current year: 2025
        300  # 3rd year
        
        >>> calculate_current_level(2026, 4)  # Current year: 2025, future entry
        None  # Student hasn't started yet
    """
    if not entry_year or not program_duration:
        return None
    
    # Validate program duration
    if program_duration < 4 or program_duration > 7:
        return None
    
    current_year = datetime.now().year
    
    # Calculate years elapsed
    years_elapsed = current_year - entry_year + 1
    
    # Student hasn't started yet
    if years_elapsed <= 0:
        return None
    
    # Cap at final year (don't go beyond program duration)
    current_level_year = min(years_elapsed, program_duration)
    
    # Convert to Nigerian level format (100L, 200L, etc.)
    return current_level_year * 100


def get_academic_year_range(current_year: Optional[int] = None) -> Tuple[int, int]:
    """
    Get the current academic year range.
    
    Nigerian universities typically run from September to August.
    So academic year 2024/2025 runs from Sept 2024 to Aug 2025.
    
    Args:
        current_year: Optional specific year to check (defaults to current year)
    
    Returns:
        Tuple[int, int]: Start and end years of current academic session
    
    Examples:
        >>> get_academic_year_range()  # Called in March 2025
        (2024, 2025)  # Academic year 2024/2025
        
        >>> get_academic_year_range()  # Called in October 2025
        (2025, 2026)  # Academic year 2025/2026
    """
    if current_year is None:
        now = datetime.now()
        current_year = now.year
        current_month = now.month
    else:
        # Assume middle of academic year if only year provided
        current_month = 3
    
    # If we're in September or later, we're in the new academic year
    if current_month >= 9:
        return (current_year, current_year + 1)
    else:
        return (current_year - 1, current_year)


def calculate_expected_graduation_year(entry_year: int, program_duration: int) -> Optional[int]:
    """
    Calculate expected graduation year.
    
    Args:
        entry_year: Year the student entered the program
        program_duration: Duration of program in years (4-7)
    
    Returns:
        int: Expected graduation year or None if invalid inputs
    
    Examples:
        >>> calculate_expected_graduation_year(2022, 4)
        2026  # Entered 2022, 4-year program, graduates 2026
    """
    if not entry_year or not program_duration:
        return None
    
    if program_duration < 4 or program_duration > 7:
        return None
    
    return entry_year + program_duration


def has_graduated(entry_year: int, program_duration: int) -> bool:
    """
    Check if a student has graduated based on entry year and program duration.
    
    Args:
        entry_year: Year the student entered the program
        program_duration: Duration of program in years (4-7)
    
    Returns:
        bool: True if graduated, False otherwise
    
    Examples:
        >>> has_graduated(2020, 4)  # Current year: 2025
        True  # Should have graduated in 2024
        
        >>> has_graduated(2023, 4)  # Current year: 2025
        False  # Should graduate in 2027
    """
    grad_year = calculate_expected_graduation_year(entry_year, program_duration)
    if not grad_year:
        return False
    
    current_year = datetime.now().year
    return current_year > grad_year


def is_final_year(entry_year: int, program_duration: int) -> bool:
    """
    Check if a student is in their final year.
    
    Args:
        entry_year: Year the student entered the program
        program_duration: Duration of program in years (4-7)
    
    Returns:
        bool: True if in final year, False otherwise
    
    Examples:
        >>> is_final_year(2022, 4)  # Current year: 2025
        True  # 4th year of 4-year program
        
        >>> is_final_year(2023, 5)  # Current year: 2025
        False  # 3rd year of 5-year program
    """
    if has_graduated(entry_year, program_duration):
        return False
    
    current_level = calculate_current_level(entry_year, program_duration)
    if not current_level:
        return False
    
    # Final year is when current_level equals program_duration * 100
    return current_level == (program_duration * 100)


def get_level_display(entry_year: int, program_duration: int) -> Optional[str]:
    """
    Get formatted level display string (e.g., '300L').
    
    Args:
        entry_year: Year the student entered the program
        program_duration: Duration of program in years (4-7)
    
    Returns:
        str: Formatted level (e.g., '300L') or None if invalid/graduated
    
    Examples:
        >>> get_level_display(2023, 4)  # Current year: 2025
        '300L'
    """
    level = calculate_current_level(entry_year, program_duration)
    return f"{level}L" if level else None


def get_cohort_year(entry_year: int) -> str:
    """
    Get cohort year display (e.g., '2022/2023' for entry in 2022).
    
    Args:
        entry_year: Year the student entered the program
    
    Returns:
        str: Cohort year in Nigerian format (e.g., '2022/2023')
    
    Examples:
        >>> get_cohort_year(2022)
        '2022/2023'
    """
    return f"{entry_year}/{entry_year + 1}"


# Validation helpers

def validate_entry_year(entry_year: int, min_year: int = 2000) -> bool:
    """
    Validate that entry year is reasonable.
    
    Args:
        entry_year: Year to validate
        min_year: Minimum acceptable year (default: 2000)
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not entry_year:
        return False
    
    current_year = datetime.now().year
    
    # Entry year shouldn't be before min_year or more than 2 years in future
    return min_year <= entry_year <= (current_year + 2)


def validate_program_duration(duration: int) -> bool:
    """
    Validate program duration is within acceptable range.
    
    Args:
        duration: Program duration in years
    
    Returns:
        bool: True if valid (4-7 years), False otherwise
    """
    return 4 <= duration <= 7
