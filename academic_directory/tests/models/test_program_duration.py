# academic_directory/tests/models/test_program_duration.py
"""
Comprehensive test suite for ProgramDuration model.

Test Coverage:
- Model creation and basic functionality
- Field validation and constraints
- Duration years validation (4-7 years)
- Program type choices
- One-to-one relationship with Department
- Clean method validation
- Save hooks
- Properties (faculty, university)
- String representation
- Edge cases and boundary conditions
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from academic_directory.models import University, Faculty, Department, ProgramDuration
import uuid


class ProgramDurationCreationTest(TestCase):
    """Test basic program duration creation and model functionality."""
    
    def setUp(self):
        """Create test university, faculty, and department."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_create_program_duration_with_valid_data(self):
        """Test creating a program duration with all valid data."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.assertIsNotNone(program.id)
        self.assertIsInstance(program.id, uuid.UUID)
        self.assertEqual(program.department, self.department)
        self.assertEqual(program.duration_years, 4)
        self.assertEqual(program.program_type, "BSC")
        self.assertIsNotNone(program.created_at)
        self.assertIsNotNone(program.updated_at)
    
    def test_create_4_year_program(self):
        """Test creating a 4-year program (standard B.Sc)."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.assertEqual(program.duration_years, 4)
    
    def test_create_5_year_program(self):
        """Test creating a 5-year program (Engineering)."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=5,
            program_type="BENG"
        )
        
        self.assertEqual(program.duration_years, 5)
    
    def test_create_6_year_program(self):
        """Test creating a 6-year program (Medicine)."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=6,
            program_type="MBBS"
        )
        
        self.assertEqual(program.duration_years, 6)
    
    def test_create_7_year_program(self):
        """Test creating a 7-year program (Extended Medicine)."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=7,
            program_type="MBBS"
        )
        
        self.assertEqual(program.duration_years, 7)
    
    def test_create_with_notes(self):
        """Test creating program duration with notes."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=5,
            program_type="BENG",
            notes="Includes industrial training year"
        )
        
        self.assertEqual(program.notes, "Includes industrial training year")
    
    def test_create_without_notes(self):
        """Test creating program duration without notes."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.assertIsNone(program.notes)


class ProgramDurationFieldValidationTest(TestCase):
    """Test field-level validation."""
    
    def setUp(self):
        """Create test department."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_duration_less_than_4_fails_validation(self):
        """Test that duration less than 4 years fails validation."""
        program = ProgramDuration(
            department=self.department,
            duration_years=3,
            program_type="BSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('duration_years', context.exception.message_dict)
    
    def test_duration_greater_than_7_fails_validation(self):
        """Test that duration greater than 7 years fails validation."""
        program = ProgramDuration(
            department=self.department,
            duration_years=8,
            program_type="MBBS"
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('duration_years', context.exception.message_dict)
    
    def test_duration_zero_fails_validation(self):
        """Test that duration of 0 fails validation."""
        program = ProgramDuration(
            department=self.department,
            duration_years=0,
            program_type="BSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('duration_years', context.exception.message_dict)
    
    def test_negative_duration_fails_validation(self):
        """Test that negative duration fails validation."""
        program = ProgramDuration(
            department=self.department,
            duration_years=-1,
            program_type="BSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('duration_years', context.exception.message_dict)
    
    def test_valid_program_types(self):
        """Test all valid program types."""
        valid_types = [
            'BSC', 'BENG', 'BTECH', 'BA', 'MBBS',
            'LLB', 'BARCH', 'BAGRICULTURE', 'BPHARM', 'OTHER'
        ]
        
        for index, prog_type in enumerate(valid_types):
            # Create different department for each to avoid one-to-one conflict
            dept = Department.objects.create(
                faculty=self.faculty,
                name=f"Department {index}",
                abbreviation=f"D{index}"
            )
            
            program = ProgramDuration.objects.create(
                department=dept,
                duration_years=4,
                program_type=prog_type
            )
            self.assertEqual(program.program_type, prog_type)
    
    def test_invalid_program_type_fails_validation(self):
        """Test that invalid program type fails validation."""
        program = ProgramDuration(
            department=self.department,
            duration_years=4,
            program_type="INVALID"
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('program_type', context.exception.message_dict)
    
    def test_null_department_fails_validation(self):
        """Test that null department fails validation."""
        program = ProgramDuration(
            duration_years=4,
            program_type="BSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            program.full_clean()
        
        self.assertIn('department', context.exception.message_dict)
    
    def test_default_program_type_is_bsc(self):
        """Test that program_type defaults to BSC."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4
        )
        
        self.assertEqual(program.program_type, "BSC")


class ProgramDurationOneToOneConstraintTest(TestCase):
    """Test one-to-one relationship with Department."""
    
    def setUp(self):
        """Create test department."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_one_to_one_relationship(self):
        """Test that department can have only one program duration."""
        program1 = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        # Attempting to create another program duration for same department
        with self.assertRaises(IntegrityError):
            ProgramDuration.objects.create(
                department=self.department,
                duration_years=5,
                program_type="BENG"
            )
    
    def test_different_departments_can_have_program_durations(self):
        """Test that different departments can each have program durations."""
        dept2 = Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        
        program1 = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        program2 = ProgramDuration.objects.create(
            department=dept2,
            duration_years=5,
            program_type="BENG"
        )
        
        self.assertEqual(ProgramDuration.objects.count(), 2)
    
    def test_department_programduration_reverse_relation(self):
        """Test reverse relation from department to program duration."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        # Access via reverse relation
        self.assertEqual(self.department.programduration, program)
    
    def test_department_without_program_duration(self):
        """Test accessing programduration on department without one raises error."""
        with self.assertRaises(ProgramDuration.DoesNotExist):
            _ = self.department.programduration


class ProgramDurationCleanMethodTest(TestCase):
    """Test the clean() method validation."""
    
    def setUp(self):
        """Create test department."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_clean_validates_duration_range(self):
        """Test that clean() validates duration is 4-7 years."""
        program = ProgramDuration(
            department=self.department,
            duration_years=3,
            program_type="BSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            program.clean()
        
        self.assertIn('duration_years', str(context.exception))
    
    def test_clean_allows_valid_duration(self):
        """Test that clean() allows valid duration."""
        program = ProgramDuration(
            department=self.department,
            duration_years=5,
            program_type="BENG"
        )
        
        # Should not raise
        program.clean()
    
    def test_clean_called_on_save(self):
        """Test that save() calls clean()."""
        program = ProgramDuration(
            department=self.department,
            duration_years=3,  # invalid
            program_type="BSC"
        )
        
        with self.assertRaises(ValidationError):
            program.save()


class ProgramDurationCascadeDeleteTest(TestCase):
    """Test cascade delete behavior."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_delete_department_deletes_program_duration(self):
        """Test that deleting department deletes program duration."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.assertEqual(ProgramDuration.objects.count(), 1)
        
        self.department.delete()
        
        # Program duration should be deleted
        self.assertEqual(ProgramDuration.objects.count(), 0)
    
    def test_delete_faculty_deletes_program_duration(self):
        """Test that deleting faculty deletes program duration."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.faculty.delete()
        
        # Department and program duration should be deleted
        self.assertEqual(Department.objects.count(), 0)
        self.assertEqual(ProgramDuration.objects.count(), 0)
    
    def test_delete_university_deletes_program_duration(self):
        """Test that deleting university deletes program duration."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.university.delete()
        
        # Everything should be deleted
        self.assertEqual(Faculty.objects.count(), 0)
        self.assertEqual(Department.objects.count(), 0)
        self.assertEqual(ProgramDuration.objects.count(), 0)


class ProgramDurationPropertiesTest(TestCase):
    """Test computed properties."""
    
    def setUp(self):
        """Set up test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        self.program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
    
    def test_faculty_property(self):
        """Test faculty property returns correct faculty."""
        self.assertEqual(self.program.faculty.id, self.faculty.id)
        self.assertEqual(self.program.faculty.name, "Faculty of Engineering")
    
    def test_university_property(self):
        """Test university property returns correct university."""
        self.assertEqual(self.program.university.id, self.university.id)
        self.assertEqual(self.program.university.name, "University of Benin")
    
    def test_properties_traverse_relationships_correctly(self):
        """Test that properties correctly traverse relationships."""
        # Create another complete hierarchy
        university2 = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        faculty2 = Faculty.objects.create(
            university=university2,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        dept2 = Department.objects.create(
            faculty=faculty2,
            name="Mathematics",
            abbreviation="MTH"
        )
        program2 = ProgramDuration.objects.create(
            department=dept2,
            duration_years=4,
            program_type="BSC"
        )
        
        # Verify each program points to correct faculty and university
        self.assertEqual(self.program.faculty.id, self.faculty.id)
        self.assertEqual(self.program.university.id, self.university.id)
        self.assertEqual(program2.faculty.id, faculty2.id)
        self.assertEqual(program2.university.id, university2.id)


class ProgramDurationStringRepresentationTest(TestCase):
    """Test string representation."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_str_format(self):
        """Test __str__ returns correct format."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        expected = f"{self.department.full_name} - 4 years (Bachelor of Science (B.Sc))"
        self.assertEqual(str(program), expected)
    
    def test_str_with_different_program_types(self):
        """Test __str__ with different program types."""
        # Create different departments for each
        dept2 = Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        dept3 = Department.objects.create(
            faculty=self.faculty,
            name="Medicine",
            abbreviation="MED"
        )
        
        program1 = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        program2 = ProgramDuration.objects.create(
            department=dept2,
            duration_years=5,
            program_type="BENG"
        )
        program3 = ProgramDuration.objects.create(
            department=dept3,
            duration_years=6,
            program_type="MBBS"
        )
        
        self.assertIn("Bachelor of Science", str(program1))
        self.assertIn("Bachelor of Engineering", str(program2))
        self.assertIn("Bachelor of Medicine", str(program3))


class ProgramDurationMetaOptionsTest(TestCase):
    """Test model Meta options."""
    
    def setUp(self):
        """Create test data."""
        self.university1 = University.objects.create(
            name="Alpha University",
            abbreviation="AU",
            state="LAGOS",
            type="FEDERAL"
        )
        self.university2 = University.objects.create(
            name="Beta University",
            abbreviation="BU",
            state="LAGOS",
            type="FEDERAL"
        )
        self.faculty1 = Faculty.objects.create(
            university=self.university1,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.faculty2 = Faculty.objects.create(
            university=self.university2,
            name="Faculty of Science",
            abbreviation="SCI"
        )
    
    def test_ordering_by_university_department_name(self):
        """Test that program durations are ordered by university, then department."""
        dept1 = Department.objects.create(
            faculty=self.faculty1,
            name="Computer Science",
            abbreviation="CSC"
        )
        dept2 = Department.objects.create(
            faculty=self.faculty1,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        dept3 = Department.objects.create(
            faculty=self.faculty2,
            name="Mathematics",
            abbreviation="MTH"
        )
        
        ProgramDuration.objects.create(
            department=dept3,
            duration_years=4,
            program_type="BSC"
        )
        ProgramDuration.objects.create(
            department=dept2,
            duration_years=5,
            program_type="BENG"
        )
        ProgramDuration.objects.create(
            department=dept1,
            duration_years=4,
            program_type="BSC"
        )
        
        programs = list(ProgramDuration.objects.all())
        # Should be ordered by university name (Alpha before Beta)
        # Then by department name within same university
        self.assertEqual(programs[0].university.name, "Alpha University")
        self.assertEqual(programs[0].department.name, "Computer Science")
        self.assertEqual(programs[1].university.name, "Alpha University")
        self.assertEqual(programs[1].department.name, "Electrical Engineering")
        self.assertEqual(programs[2].university.name, "Beta University")
    
    def test_verbose_name(self):
        """Test verbose_name is set correctly."""
        self.assertEqual(ProgramDuration._meta.verbose_name, "Program Duration")
    
    def test_verbose_name_plural(self):
        """Test verbose_name_plural is set correctly."""
        self.assertEqual(ProgramDuration._meta.verbose_name_plural, "Program Durations")


class ProgramDurationEdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        """Create test department."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_duration_boundary_4_years(self):
        """Test minimum valid duration (4 years)."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.assertEqual(program.duration_years, 4)
    
    def test_duration_boundary_7_years(self):
        """Test maximum valid duration (7 years)."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=7,
            program_type="MBBS"
        )
        
        self.assertEqual(program.duration_years, 7)
    
    def test_very_long_notes(self):
        """Test program duration with very long notes."""
        long_notes = "A" * 1000  # Long text
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=5,
            program_type="BENG",
            notes=long_notes
        )
        
        self.assertEqual(len(program.notes), 1000)
    
    def test_notes_with_special_characters(self):
        """Test notes with special characters and unicode."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=5,
            program_type="BENG",
            notes="Includes 1 year SIWES (Students' Industrial Work Experience Scheme) & internship"
        )
        
        self.assertIn("&", program.notes)
        self.assertIn("'", program.notes)
    
    def test_update_duration_years(self):
        """Test updating duration_years."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        program.duration_years = 5
        program.save()
        
        program.refresh_from_db()
        self.assertEqual(program.duration_years, 5)
    
    def test_update_program_type(self):
        """Test updating program_type."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        program.program_type = "BTECH"
        program.save()
        
        program.refresh_from_db()
        self.assertEqual(program.program_type, "BTECH")
    
    def test_update_notes(self):
        """Test updating notes."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=5,
            program_type="BENG"
        )
        
        program.notes = "Updated notes"
        program.save()
        
        program.refresh_from_db()
        self.assertEqual(program.notes, "Updated notes")
    
    def test_clear_notes(self):
        """Test clearing notes (set to null)."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=5,
            program_type="BENG",
            notes="Some notes"
        )
        
        program.notes = None
        program.save()
        
        program.refresh_from_db()
        self.assertIsNone(program.notes)


class ProgramDurationTimestampsTest(TestCase):
    """Test created_at and updated_at timestamps."""
    
    def setUp(self):
        """Create test department."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_created_at_auto_set_on_creation(self):
        """Test that created_at is automatically set."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.assertIsNotNone(program.created_at)
    
    def test_updated_at_auto_set_on_creation(self):
        """Test that updated_at is automatically set."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.assertIsNotNone(program.updated_at)
    
    def test_updated_at_changes_on_update(self):
        """Test that updated_at changes when model is updated."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        original_updated_at = program.updated_at
        
        # Wait a moment and update
        import time
        time.sleep(0.01)
        
        program.duration_years = 5
        program.save()
        
        program.refresh_from_db()
        self.assertGreater(program.updated_at, original_updated_at)
    
    def test_created_at_does_not_change_on_update(self):
        """Test that created_at does not change on update."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        original_created_at = program.created_at
        
        program.duration_years = 5
        program.save()
        
        program.refresh_from_db()
        self.assertEqual(program.created_at, original_created_at)


class ProgramDurationGetProgramTypeDisplayTest(TestCase):
    """Test get_program_type_display() method."""
    
    def setUp(self):
        """Create test department."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_get_program_type_display_bsc(self):
        """Test display name for B.Sc."""
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type="BSC"
        )
        
        self.assertEqual(program.get_program_type_display(), "Bachelor of Science (B.Sc)")
    
    def test_get_program_type_display_beng(self):
        """Test display name for B.Eng."""
        dept2 = Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        program = ProgramDuration.objects.create(
            department=dept2,
            duration_years=5,
            program_type="BENG"
        )
        
        self.assertEqual(program.get_program_type_display(), "Bachelor of Engineering (B.Eng)")
    
    def test_get_program_type_display_mbbs(self):
        """Test display name for MBBS."""
        dept2 = Department.objects.create(
            faculty=self.faculty,
            name="Medicine",
            abbreviation="MED"
        )
        program = ProgramDuration.objects.create(
            department=dept2,
            duration_years=6,
            program_type="MBBS"
        )
        
        self.assertEqual(
            program.get_program_type_display(),
            "Bachelor of Medicine, Bachelor of Surgery (MBBS)"
        )