# academic_directory/tests/models/test_department.py
"""
Comprehensive test suite for Department model.

Test Coverage:
- Model creation and basic functionality
- Field validation and constraints
- Unique constraints (faculty + name)
- Abbreviation uppercase enforcement
- Clean method validation
- Save hooks
- Foreign key relationship with Faculty
- Cascade delete behavior
- Property (university)
- String representation  
- Edge cases and boundary conditions
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from academic_directory.models import University, Faculty, Department, Representative
import uuid


class DepartmentCreationTest(TestCase):
    """Test basic department creation and model functionality."""
    
    def setUp(self):
        """Create test university and faculty."""
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
    
    def test_create_department_with_valid_data(self):
        """Test creating a department with all valid data."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        self.assertIsNotNone(department.id)
        self.assertIsInstance(department.id, uuid.UUID)
        self.assertEqual(department.faculty, self.faculty)
        self.assertEqual(department.name, "Computer Science")
        self.assertEqual(department.abbreviation, "CSC")
        self.assertTrue(department.is_active)
        self.assertIsNotNone(department.created_at)
        self.assertIsNotNone(department.updated_at)
    
    def test_create_multiple_departments(self):
        """Test creating multiple departments for same faculty."""
        dept1 = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        dept2 = Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        
        self.assertEqual(Department.objects.count(), 2)
        self.assertEqual(dept1.faculty, self.faculty)
        self.assertEqual(dept2.faculty, self.faculty)
    
    def test_default_is_active_true(self):
        """Test that is_active defaults to True."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        self.assertTrue(department.is_active)
    
    def test_create_inactive_department(self):
        """Test creating an inactive department."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Inactive Department",
            abbreviation="ID",
            is_active=False
        )
        
        self.assertFalse(department.is_active)


class DepartmentFieldValidationTest(TestCase):
    """Test field-level validation."""
    
    def setUp(self):
        """Create test university and faculty."""
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
    
    def test_abbreviation_must_be_uppercase(self):
        """Test that lowercase abbreviation is converted to uppercase."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="csc"  # lowercase
        )
        
        department.refresh_from_db()
        self.assertEqual(department.abbreviation, "CSC")
    
    def test_abbreviation_mixed_case_converted_to_uppercase(self):
        """Test that mixed case abbreviation is converted to uppercase."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CsC"  # mixed case
        )
        
        department.refresh_from_db()
        self.assertEqual(department.abbreviation, "CSC")
    
    def test_abbreviation_with_numbers_fails_validation(self):
        """Test that abbreviation with numbers fails regex validation."""
        department = Department(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC123"
        )
        
        with self.assertRaises(ValidationError) as context:
            department.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_abbreviation_with_spaces_fails_validation(self):
        """Test that abbreviation with spaces fails validation."""
        department = Department(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CS C"
        )
        
        with self.assertRaises(ValidationError) as context:
            department.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_abbreviation_with_special_characters_fails_validation(self):
        """Test that abbreviation with special characters fails validation."""
        department = Department(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC-1"
        )
        
        with self.assertRaises(ValidationError) as context:
            department.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_empty_name_fails_validation(self):
        """Test that empty name fails validation."""
        department = Department(
            faculty=self.faculty,
            name="",
            abbreviation="CSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            department.full_clean()
        
        self.assertIn('name', context.exception.message_dict)
    
    def test_whitespace_only_name_fails_validation(self):
        """Test that whitespace-only name fails validation."""
        department = Department(
            faculty=self.faculty,
            name="   ",
            abbreviation="CSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            department.save()
        
        self.assertIn('name', str(context.exception))
    
    def test_null_faculty_fails_validation(self):
        """Test that null faculty fails validation."""
        department = Department(
            name="Computer Science",
            abbreviation="CSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            department.full_clean()
        
        self.assertIn('faculty', context.exception.message_dict)


class DepartmentUniqueConstraintsTest(TestCase):
    """Test unique constraints."""
    
    def setUp(self):
        """Create test universities, faculties, and department."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.faculty1 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        self.department = Department.objects.create(
            faculty=self.faculty1,
            name="Computer Science",
            abbreviation="CSC"
        )
    
    def test_duplicate_department_name_same_faculty_fails(self):
        """Test that duplicate department name in same faculty fails."""
        with self.assertRaises(IntegrityError):
            Department.objects.create(
                faculty=self.faculty1,
                name="Computer Science",  # duplicate
                abbreviation="CS"
            )
    
    def test_same_department_name_different_faculties_allowed(self):
        """Test that same department name in different faculties is allowed."""
        dept2 = Department.objects.create(
            faculty=self.faculty2,
            name="Computer Science",  # same name
            abbreviation="CSC"
        )
        
        self.assertIsNotNone(dept2.id)
        self.assertEqual(Department.objects.count(), 2)
    
    def test_different_abbreviations_same_faculty_allowed(self):
        """Test that different abbreviations for same faculty are allowed."""
        dept2 = Department.objects.create(
            faculty=self.faculty1,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        
        self.assertEqual(Department.objects.filter(faculty=self.faculty1).count(), 2)
    
    def test_case_sensitive_name_uniqueness(self):
        """Test name uniqueness case sensitivity."""
        try:
            dept2 = Department.objects.create(
                faculty=self.faculty1,
                name="computer science",  # different case
                abbreviation="CS"
            )
            # If it succeeds, names are case-sensitive
            self.assertIsNotNone(dept2.id)
        except IntegrityError:
            # If it fails, database is case-insensitive
            pass


class DepartmentCleanMethodTest(TestCase):
    """Test the clean() method validation."""
    
    def setUp(self):
        """Create test university and faculty."""
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
    
    def test_clean_converts_abbreviation_to_uppercase(self):
        """Test that clean() converts abbreviation to uppercase."""
        department = Department(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="csc"
        )
        
        department.clean()
        self.assertEqual(department.abbreviation, "CSC")
    
    def test_clean_validates_empty_name(self):
        """Test that clean() catches empty name."""
        department = Department(
            faculty=self.faculty,
            name="",
            abbreviation="CSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            department.clean()
        
        self.assertIn('name', str(context.exception))
    
    def test_clean_validates_whitespace_name(self):
        """Test that clean() catches whitespace-only name."""
        department = Department(
            faculty=self.faculty,
            name="   ",
            abbreviation="CSC"
        )
        
        with self.assertRaises(ValidationError) as context:
            department.clean()
        
        self.assertIn('name', str(context.exception))
    
    def test_clean_called_on_save(self):
        """Test that save() calls clean()."""
        department = Department(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="csc"  # lowercase
        )
        
        department.save()
        self.assertEqual(department.abbreviation, "CSC")


class DepartmentForeignKeyRelationshipTest(TestCase):
    """Test foreign key relationships."""
    
    def setUp(self):
        """Create test university and faculty."""
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
    
    def test_department_linked_to_faculty(self):
        """Test that department is properly linked to faculty."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        self.assertEqual(department.faculty.id, self.faculty.id)
        self.assertEqual(department.faculty.name, "Faculty of Engineering")
    
    def test_faculty_departments_reverse_relation(self):
        """Test reverse relation from faculty to departments."""
        dept1 = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        dept2 = Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        
        departments = self.faculty.departments.all()
        self.assertEqual(departments.count(), 2)
        self.assertIn(dept1, departments)
        self.assertIn(dept2, departments)
    
    def test_delete_faculty_cascades_to_departments(self):
        """Test that deleting faculty cascades to departments."""
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        
        self.assertEqual(Department.objects.count(), 2)
        
        self.faculty.delete()
        
        # All departments should be deleted
        self.assertEqual(Department.objects.count(), 0)
    
    def test_delete_university_cascades_to_departments(self):
        """Test that deleting university cascades to departments."""
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        self.assertEqual(Department.objects.count(), 1)
        
        self.university.delete()
        
        # Faculty and department should be deleted
        self.assertEqual(Faculty.objects.count(), 0)
        self.assertEqual(Department.objects.count(), 0)
    
    def test_department_survives_other_faculty_deletion(self):
        """Test that department survives when other faculty is deleted."""
        faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        dept1 = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        dept2 = Department.objects.create(
            faculty=faculty2,
            name="Mathematics",
            abbreviation="MTH"
        )
        
        faculty2.delete()
        
        # Only dept1 should remain
        self.assertEqual(Department.objects.count(), 1)
        self.assertTrue(Department.objects.filter(id=dept1.id).exists())
        self.assertFalse(Department.objects.filter(id=dept2.id).exists())


class DepartmentPropertiesTest(TestCase):
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
    
    def test_university_property_returns_correct_university(self):
        """Test that university property returns correct university."""
        self.assertEqual(self.department.university.id, self.university.id)
        self.assertEqual(self.department.university.name, "University of Benin")
    
    def test_university_property_traverses_faculty_relationship(self):
        """Test that university property correctly traverses faculty relationship."""
        # Create another university and verify property returns correct one
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
        
        self.assertEqual(self.department.university.id, self.university.id)
        self.assertEqual(dept2.university.id, university2.id)
        self.assertNotEqual(self.department.university.id, dept2.university.id)


class DepartmentStringRepresentationTest(TestCase):
    """Test string representation."""
    
    def setUp(self):
        """Create test university and faculty."""
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
    
    def test_str_format(self):
        """Test __str__ returns correct format."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        expected = f"{self.university.abbreviation} - {self.faculty.abbreviation} - {department.name}"
        self.assertEqual(str(department), expected)
        self.assertEqual(str(department), "UNIBEN - ENG - Computer Science")
    
    def test_str_with_different_data(self):
        """Test __str__ with different department data."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        
        self.assertEqual(str(department), "UNIBEN - ENG - Electrical Engineering")


class DepartmentMetaOptionsTest(TestCase):
    """Test model Meta options."""
    
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
    
    def test_ordering_by_university_faculty_name(self):
        """Test that departments are ordered by university, faculty, then name."""
        # Create another university and faculty for ordering test
        university2 = University.objects.create(
            name="Alpha University",  # Should come first alphabetically
            abbreviation="AU",
            state="LAGOS",
            type="FEDERAL"
        )
        faculty2 = Faculty.objects.create(
            university=university2,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        Department.objects.create(
            faculty=faculty2,
            name="Mathematics",
            abbreviation="MTH"
        )
        
        departments = list(Department.objects.all())
        # Should be ordered by university name (Alpha before Benin)
        # Then by faculty name within same university
        # Then by department name within same faculty
        self.assertEqual(departments[0].university.name, "Alpha University")
        self.assertEqual(departments[1].university.name, "University of Benin")
        self.assertEqual(departments[1].name, "Computer Science")
        self.assertEqual(departments[2].name, "Electrical Engineering")
    
    def test_verbose_name(self):
        """Test verbose_name is set correctly."""
        self.assertEqual(Department._meta.verbose_name, "Department")
    
    def test_verbose_name_plural(self):
        """Test verbose_name_plural is set correctly."""
        self.assertEqual(Department._meta.verbose_name_plural, "Departments")
    
    def test_unique_together_constraint(self):
        """Test unique_together constraint on faculty and name."""
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        # Should raise IntegrityError for duplicate faculty + name
        with self.assertRaises(IntegrityError):
            Department.objects.create(
                faculty=self.faculty,
                name="Computer Science",
                abbreviation="CS"
            )


class DepartmentEdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        """Create test university and faculty."""
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
    
    def test_very_long_name(self):
        """Test department with very long name."""
        long_name = "A" * 255  # Max length
        department = Department.objects.create(
            faculty=self.faculty,
            name=long_name,
            abbreviation="LONG"
        )
        
        self.assertEqual(department.name, long_name)
        self.assertEqual(len(department.name), 255)
    
    def test_name_exceeding_max_length_fails(self):
        """Test that name exceeding 255 characters fails."""
        long_name = "A" * 256  # Over max length
        department = Department(
            faculty=self.faculty,
            name=long_name,
            abbreviation="LONG"
        )
        
        with self.assertRaises(ValidationError):
            department.full_clean()
    
    def test_abbreviation_max_length(self):
        """Test abbreviation at max length."""
        abbr = "A" * 20  # Max length
        department = Department.objects.create(
            faculty=self.faculty,
            name="Test Department",
            abbreviation=abbr
        )
        
        self.assertEqual(len(department.abbreviation), 20)
    
    def test_abbreviation_exceeding_max_length_fails(self):
        """Test that abbreviation exceeding 20 characters fails."""
        abbr = "A" * 21  # Over max length
        department = Department(
            faculty=self.faculty,
            name="Test Department",
            abbreviation=abbr
        )
        
        with self.assertRaises(ValidationError):
            department.full_clean()
    
    def test_unicode_characters_in_name(self):
        """Test department name with unicode characters."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Département d'Informatique",  # with accents
            abbreviation="DI"
        )
        
        self.assertEqual(department.name, "Département d'Informatique")
    
    def test_special_characters_in_name(self):
        """Test department name with special characters."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science & Engineering",
            abbreviation="CSE"
        )
        
        self.assertIn("&", department.name)
    
    def test_update_department_name(self):
        """Test updating department name."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Old Name",
            abbreviation="ON"
        )
        
        department.name = "New Name"
        department.save()
        
        department.refresh_from_db()
        self.assertEqual(department.name, "New Name")
    
    def test_update_department_abbreviation(self):
        """Test updating department abbreviation."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Test Department",
            abbreviation="OLD"
        )
        
        department.abbreviation = "new"
        department.save()
        
        department.refresh_from_db()
        self.assertEqual(department.abbreviation, "NEW")  # should be uppercase
    
    def test_change_department_faculty(self):
        """Test changing department's faculty."""
        faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        department.faculty = faculty2
        department.save()
        
        department.refresh_from_db()
        self.assertEqual(department.faculty.id, faculty2.id)
    
    def test_toggle_is_active_status(self):
        """Test toggling is_active status."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Test Department",
            abbreviation="TD",
            is_active=True
        )
        
        department.is_active = False
        department.save()
        
        department.refresh_from_db()
        self.assertFalse(department.is_active)
        
        department.is_active = True
        department.save()
        
        department.refresh_from_db()
        self.assertTrue(department.is_active)


class DepartmentIndexingTest(TestCase):
    """Test database indexes."""
    
    def test_faculty_name_composite_index_exists(self):
        """Test that composite index on faculty and name exists."""
        indexes = [index.fields for index in Department._meta.indexes]
        self.assertIn(['faculty', 'name'], indexes)
    
    def test_abbreviation_index_exists(self):
        """Test that abbreviation field has an index."""
        indexes = [index.fields for index in Department._meta.indexes]
        self.assertIn(['abbreviation'], indexes)


class DepartmentTimestampsTest(TestCase):
    """Test created_at and updated_at timestamps."""
    
    def setUp(self):
        """Create test university and faculty."""
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
    
    def test_created_at_auto_set_on_creation(self):
        """Test that created_at is automatically set."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        self.assertIsNotNone(department.created_at)
    
    def test_updated_at_auto_set_on_creation(self):
        """Test that updated_at is automatically set."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        self.assertIsNotNone(department.updated_at)
    
    def test_updated_at_changes_on_update(self):
        """Test that updated_at changes when model is updated."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        original_updated_at = department.updated_at
        
        # Wait a moment and update
        import time
        time.sleep(0.01)
        
        department.name = "Updated Department"
        department.save()
        
        department.refresh_from_db()
        self.assertGreater(department.updated_at, original_updated_at)
    
    def test_created_at_does_not_change_on_update(self):
        """Test that created_at does not change on update."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        original_created_at = department.created_at
        
        department.name = "Updated Department"
        department.save()
        
        department.refresh_from_db()
        self.assertEqual(department.created_at, original_created_at)