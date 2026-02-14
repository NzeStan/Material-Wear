# academic_directory/tests/utils/test_level_calculator.py
"""
Comprehensive test suite for level_calculator utility.

Test Coverage:
- Current level calculation
- Academic year range calculation
- Expected graduation year calculation
- Graduation status checking
- Final year detection
- Level display formatting
- Entry year validation
- Program duration validation
"""

from django.test import TestCase
from freezegun import freeze_time
from academic_directory.utils.level_calculator import (
    calculate_current_level,
    get_academic_year_range,
    calculate_expected_graduation_year,
    has_graduated,
    is_final_year,
    get_level_display,
    get_cohort_year,
    validate_entry_year,
    validate_program_duration
)


@freeze_time("2025-03-15")  # Mid academic year 2024/2025
class CalculateCurrentLevelTest(TestCase):
    """Test current level calculation."""
    
    def test_first_year_student(self):
        """Test first year student (100L)."""
        # Entered 2024, currently in 2025 = 1st year
        level = calculate_current_level(2024, 4)
        self.assertEqual(level, 100)
    
    def test_second_year_student(self):
        """Test second year student (200L)."""
        level = calculate_current_level(2023, 4)
        self.assertEqual(level, 200)
    
    def test_third_year_student(self):
        """Test third year student (300L)."""
        level = calculate_current_level(2022, 4)
        self.assertEqual(level, 300)
    
    def test_fourth_year_student(self):
        """Test fourth year student (400L)."""
        level = calculate_current_level(2021, 4)
        self.assertEqual(level, 400)
    
    def test_fifth_year_program(self):
        """Test 5-year program student."""
        level = calculate_current_level(2021, 5)
        self.assertEqual(level, 500)
    
    def test_caps_at_final_year(self):
        """Test that level doesn't exceed program duration."""
        # Entered 2020, 4-year program, should cap at 400L
        level = calculate_current_level(2020, 4)
        self.assertEqual(level, 400)  # Not 600L
    
    def test_graduated_student_shows_final_level(self):
        """Test graduated student shows final level."""
        # Entered 2019, should have graduated in 2023
        level = calculate_current_level(2019, 4)
        self.assertEqual(level, 400)  # Caps at final year
    
    def test_future_entry_returns_none(self):
        """Test future entry year returns None."""
        level = calculate_current_level(2026, 4)
        self.assertIsNone(level)
    
    def test_invalid_duration_returns_none(self):
        """Test invalid program duration returns None."""
        self.assertIsNone(calculate_current_level(2022, 3))  # Too short
        self.assertIsNone(calculate_current_level(2022, 8))  # Too long
    
    def test_none_inputs_return_none(self):
        """Test None inputs return None."""
        self.assertIsNone(calculate_current_level(None, 4))
        self.assertIsNone(calculate_current_level(2022, None))


@freeze_time("2025-03-15")  # March 2025
class GetAcademicYearRangeTest(TestCase):
    """Test academic year range calculation."""
    
    def test_march_returns_current_session(self):
        """Test March returns 2024/2025 session."""
        start, end = get_academic_year_range()
        self.assertEqual(start, 2024)
        self.assertEqual(end, 2025)
    
    @freeze_time("2025-09-15")  # September 2025
    def test_september_returns_new_session(self):
        """Test September starts new academic year."""
        start, end = get_academic_year_range()
        self.assertEqual(start, 2025)
        self.assertEqual(end, 2026)
    
    @freeze_time("2025-08-31")  # End of August
    def test_august_still_previous_session(self):
        """Test August is still previous session."""
        start, end = get_academic_year_range()
        self.assertEqual(start, 2024)
        self.assertEqual(end, 2025)
    
    def test_specific_year_provided(self):
        """Test with specific year provided."""
        start, end = get_academic_year_range(2023)
        self.assertEqual(start, 2022)
        self.assertEqual(end, 2023)


@freeze_time("2025-03-15")
class CalculateExpectedGraduationYearTest(TestCase):
    """Test expected graduation year calculation."""
    
    def test_four_year_program(self):
        """Test 4-year program graduation."""
        grad_year = calculate_expected_graduation_year(2022, 4)
        self.assertEqual(grad_year, 2026)
    
    def test_five_year_program(self):
        """Test 5-year program graduation."""
        grad_year = calculate_expected_graduation_year(2022, 5)
        self.assertEqual(grad_year, 2027)
    
    def test_six_year_program(self):
        """Test 6-year program graduation (e.g., MBBS)."""
        grad_year = calculate_expected_graduation_year(2020, 6)
        self.assertEqual(grad_year, 2026)
    
    def test_invalid_inputs_return_none(self):
        """Test invalid inputs return None."""
        self.assertIsNone(calculate_expected_graduation_year(None, 4))
        self.assertIsNone(calculate_expected_graduation_year(2022, None))
        self.assertIsNone(calculate_expected_graduation_year(2022, 3))


@freeze_time("2025-03-15")
class HasGraduatedTest(TestCase):
    """Test graduation status checking."""
    
    def test_graduated_student(self):
        """Test student who has graduated."""
        # Entered 2020, 4-year program, should graduate 2024
        self.assertTrue(has_graduated(2020, 4))
    
    def test_current_student(self):
        """Test current student has not graduated."""
        # Entered 2022, 4-year program, should graduate 2026
        self.assertFalse(has_graduated(2022, 4))
    
    def test_final_year_not_graduated(self):
        """Test final year student hasn't graduated yet."""
        # Entered 2021, 4-year program, should graduate 2025 (later this year)
        self.assertFalse(has_graduated(2021, 4))
    
    def test_just_graduated(self):
        """Test student who just graduated."""
        # Entered 2021, 4-year program, graduated 2025 (this year but past)
        # Current date is March, so if they graduated earlier, they have graduated
        # But graduation is typically later in the year, so they haven't yet
        self.assertFalse(has_graduated(2021, 4))


@freeze_time("2025-03-15")
class IsFinalYearTest(TestCase):
    """Test final year detection."""
    
    def test_final_year_student(self):
        """Test student in final year."""
        # Entered 2021, 4-year program, currently 400L
        self.assertTrue(is_final_year(2021, 4))
    
    def test_not_final_year(self):
        """Test student not in final year."""
        # Entered 2022, 4-year program, currently 300L
        self.assertFalse(is_final_year(2022, 4))
    
    def test_graduated_not_final_year(self):
        """Test graduated student is not in final year."""
        # Entered 2020, already graduated
        self.assertFalse(is_final_year(2020, 4))
    
    def test_five_year_final(self):
        """Test final year of 5-year program."""
        # Entered 2020, 5-year program, currently 500L
        self.assertTrue(is_final_year(2020, 5))


@freeze_time("2025-03-15")
class GetLevelDisplayTest(TestCase):
    """Test level display formatting."""
    
    def test_formats_level_with_L(self):
        """Test level is formatted with L suffix."""
        display = get_level_display(2022, 4)
        self.assertEqual(display, '300L')
    
    def test_returns_none_for_invalid(self):
        """Test returns None for invalid inputs."""
        self.assertIsNone(get_level_display(2026, 4))  # Future entry
        self.assertIsNone(get_level_display(None, 4))


class GetCohortYearTest(TestCase):
    """Test cohort year formatting."""
    
    def test_formats_cohort_year(self):
        """Test cohort year is formatted correctly."""
        cohort = get_cohort_year(2022)
        self.assertEqual(cohort, '2022/2023')
    
    def test_different_years(self):
        """Test different cohort years."""
        self.assertEqual(get_cohort_year(2020), '2020/2021')
        self.assertEqual(get_cohort_year(2025), '2025/2026')


class ValidateEntryYearTest(TestCase):
    """Test entry year validation."""
    
    @freeze_time("2025-03-15")
    def test_valid_recent_year(self):
        """Test recent year is valid."""
        self.assertTrue(validate_entry_year(2024))
        self.assertTrue(validate_entry_year(2023))
    
    @freeze_time("2025-03-15")
    def test_valid_future_year(self):
        """Test up to 2 years future is valid."""
        self.assertTrue(validate_entry_year(2026))
        self.assertTrue(validate_entry_year(2027))
    
    @freeze_time("2025-03-15")
    def test_invalid_too_far_future(self):
        """Test more than 2 years future is invalid."""
        self.assertFalse(validate_entry_year(2028))
    
    def test_invalid_too_old(self):
        """Test year before 2000 is invalid."""
        self.assertFalse(validate_entry_year(1999))
        self.assertFalse(validate_entry_year(1990))
    
    def test_valid_old_year(self):
        """Test year from 2000 onwards is valid."""
        self.assertTrue(validate_entry_year(2000))
        self.assertTrue(validate_entry_year(2010))
    
    def test_none_is_invalid(self):
        """Test None is invalid."""
        self.assertFalse(validate_entry_year(None))


class ValidateProgramDurationTest(TestCase):
    """Test program duration validation."""
    
    def test_valid_durations(self):
        """Test valid program durations (4-7 years)."""
        self.assertTrue(validate_program_duration(4))
        self.assertTrue(validate_program_duration(5))
        self.assertTrue(validate_program_duration(6))
        self.assertTrue(validate_program_duration(7))
    
    def test_invalid_too_short(self):
        """Test duration less than 4 years is invalid."""
        self.assertFalse(validate_program_duration(3))
        self.assertFalse(validate_program_duration(2))
    
    def test_invalid_too_long(self):
        """Test duration more than 7 years is invalid."""
        self.assertFalse(validate_program_duration(8))
        self.assertFalse(validate_program_duration(10))