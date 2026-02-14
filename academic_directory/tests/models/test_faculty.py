# academic_directory/tests/models/test_faculty.py
"""
Comprehensive test suite for Faculty model.

Test Coverage:
- Model creation and basic functionality
- Field validation and constraints
- Unique constraints (university + name)
- Abbreviation uppercase enforcement  
- Clean method validation
- Save hooks
- Foreign key relationship with University
- Cascade delete behavior
- Properties (departments_count, representatives_count, full_name)
- String representation
- Edge cases and boundary conditions
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from academic_directory.models import University, Faculty, Department, Representative
import uuid


class FacultyCreationTest(TestCase):
    """Test basic faculty creation and model functionality."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_create_faculty_with_valid_data(self):
        """Test creating a faculty with all valid data."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        self.assertIsNotNone(faculty.id)
        self.assertIsInstance(faculty.id, uuid.UUID)
        self.assertEqual(faculty.university, self.university)
        self.assertEqual(faculty.name, "Faculty of Engineering")
        self.assertEqual(faculty.abbreviation, "ENG")
        self.assertTrue(faculty.is_active)
        self.assertIsNotNone(faculty.created_at)
        self.assertIsNotNone(faculty.updated_at)
    
    def test_create_multiple_faculties(self):
        """Test creating multiple faculties for same university."""
        faculty1 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        self.assertEqual(Faculty.objects.count(), 2)
        self.assertEqual(faculty1.university, self.university)
        self.assertEqual(faculty2.university, self.university)
    
    def test_default_is_active_true(self):
        """Test that is_active defaults to True."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        self.assertTrue(faculty.is_active)
    
    def test_create_inactive_faculty(self):
        """Test creating an inactive faculty."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Inactive Faculty",
            abbreviation="IF",
            is_active=False
        )
        
        self.assertFalse(faculty.is_active)


class FacultyFieldValidationTest(TestCase):
    """Test field-level validation."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_abbreviation_must_be_uppercase(self):
        """Test that lowercase abbreviation is converted to uppercase."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="eng"  # lowercase
        )
        
        faculty.refresh_from_db()
        self.assertEqual(faculty.abbreviation, "ENG")
    
    def test_abbreviation_mixed_case_converted_to_uppercase(self):
        """Test that mixed case abbreviation is converted to uppercase."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="ScI"  # mixed case
        )
        
        faculty.refresh_from_db()
        self.assertEqual(faculty.abbreviation, "SCI")
    
    def test_abbreviation_with_numbers_fails_validation(self):
        """Test that abbreviation with numbers fails regex validation."""
        faculty = Faculty(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG123"
        )
        
        with self.assertRaises(ValidationError) as context:
            faculty.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_abbreviation_with_spaces_fails_validation(self):
        """Test that abbreviation with spaces fails validation."""
        faculty = Faculty(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="EN G"
        )
        
        with self.assertRaises(ValidationError) as context:
            faculty.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_abbreviation_with_special_characters_fails_validation(self):
        """Test that abbreviation with special characters fails validation."""
        faculty = Faculty(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG-1"
        )
        
        with self.assertRaises(ValidationError) as context:
            faculty.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_empty_name_fails_validation(self):
        """Test that empty name fails validation."""
        faculty = Faculty(
            university=self.university,
            name="",
            abbreviation="ENG"
        )
        
        with self.assertRaises(ValidationError) as context:
            faculty.full_clean()
        
        self.assertIn('name', context.exception.message_dict)
    
    def test_whitespace_only_name_fails_validation(self):
        """Test that whitespace-only name fails validation."""
        faculty = Faculty(
            university=self.university,
            name="   ",
            abbreviation="ENG"
        )
        
        with self.assertRaises(ValidationError) as context:
            faculty.save()
        
        self.assertIn('name', str(context.exception))
    
    def test_null_university_fails_validation(self):
        """Test that null university fails validation."""
        faculty = Faculty(
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        with self.assertRaises(ValidationError) as context:
            faculty.full_clean()
        
        self.assertIn('university', context.exception.message_dict)


class FacultyUniqueConstraintsTest(TestCase):
    """Test unique constraints."""
    
    def setUp(self):
        """Create test universities and faculty."""
        self.university1 = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        self.university2 = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        self.faculty = Faculty.objects.create(
            university=self.university1,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
    
    def test_duplicate_faculty_name_same_university_fails(self):
        """Test that duplicate faculty name in same university fails."""
        with self.assertRaises(IntegrityError):
            Faculty.objects.create(
                university=self.university1,
                name="Faculty of Engineering",  # duplicate
                abbreviation="ENGR"
            )
    
    def test_same_faculty_name_different_universities_allowed(self):
        """Test that same faculty name in different universities is allowed."""
        faculty2 = Faculty.objects.create(
            university=self.university2,
            name="Faculty of Engineering",  # same name
            abbreviation="ENG"
        )
        
        self.assertIsNotNone(faculty2.id)
        self.assertEqual(Faculty.objects.count(), 2)
    
    def test_different_abbreviations_same_university_allowed(self):
        """Test that different abbreviations for same university are allowed."""
        faculty2 = Faculty.objects.create(
            university=self.university1,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        self.assertEqual(Faculty.objects.filter(university=self.university1).count(), 2)
    
    def test_case_sensitive_name_uniqueness(self):
        """Test name uniqueness case sensitivity."""
        try:
            faculty2 = Faculty.objects.create(
                university=self.university1,
                name="faculty of engineering",  # different case
                abbreviation="FE"
            )
            # If it succeeds, names are case-sensitive
            self.assertIsNotNone(faculty2.id)
        except IntegrityError:
            # If it fails, database is case-insensitive
            pass


class FacultyCleanMethodTest(TestCase):
    """Test the clean() method validation."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_clean_converts_abbreviation_to_uppercase(self):
        """Test that clean() converts abbreviation to uppercase."""
        faculty = Faculty(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="eng"
        )
        
        faculty.clean()
        self.assertEqual(faculty.abbreviation, "ENG")
    
    def test_clean_validates_empty_name(self):
        """Test that clean() catches empty name."""
        faculty = Faculty(
            university=self.university,
            name="",
            abbreviation="ENG"
        )
        
        with self.assertRaises(ValidationError) as context:
            faculty.clean()
        
        self.assertIn('name', str(context.exception))
    
    def test_clean_validates_whitespace_name(self):
        """Test that clean() catches whitespace-only name."""
        faculty = Faculty(
            university=self.university,
            name="   ",
            abbreviation="ENG"
        )
        
        with self.assertRaises(ValidationError) as context:
            faculty.clean()
        
        self.assertIn('name', str(context.exception))
    
    def test_clean_called_on_save(self):
        """Test that save() calls clean()."""
        faculty = Faculty(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="eng"  # lowercase
        )
        
        faculty.save()
        self.assertEqual(faculty.abbreviation, "ENG")


class FacultyForeignKeyRelationshipTest(TestCase):
    """Test foreign key relationships."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_faculty_linked_to_university(self):
        """Test that faculty is properly linked to university."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        self.assertEqual(faculty.university.id, self.university.id)
        self.assertEqual(faculty.university.name, "University of Benin")
    
    def test_university_faculties_reverse_relation(self):
        """Test reverse relation from university to faculties."""
        faculty1 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        faculties = self.university.faculties.all()
        self.assertEqual(faculties.count(), 2)
        self.assertIn(faculty1, faculties)
        self.assertIn(faculty2, faculties)
    
    def test_delete_university_cascades_to_faculties(self):
        """Test that deleting university cascades to faculties."""
        Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        self.assertEqual(Faculty.objects.count(), 2)
        
        self.university.delete()
        
        # All faculties should be deleted
        self.assertEqual(Faculty.objects.count(), 0)
    
    def test_faculty_survives_other_university_deletion(self):
        """Test that faculty survives when other university is deleted."""
        university2 = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        
        faculty1 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        faculty2 = Faculty.objects.create(
            university=university2,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        university2.delete()
        
        # Only faculty1 should remain
        self.assertEqual(Faculty.objects.count(), 1)
        self.assertTrue(Faculty.objects.filter(id=faculty1.id).exists())
        self.assertFalse(Faculty.objects.filter(id=faculty2.id).exists())


class FacultyPropertiesTest(TestCase):
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
    
    def test_departments_count_zero_initially(self):
        """Test that departments_count is 0 for new faculty."""
        self.assertEqual(self.faculty.departments_count, 0)
    
    def test_departments_count_with_active_departments(self):
        """Test departments_count with active departments."""
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC",
            is_active=True
        )
        Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE",
            is_active=True
        )
        
        self.assertEqual(self.faculty.departments_count, 2)
    
    def test_departments_count_excludes_inactive_departments(self):
        """Test that departments_count excludes inactive departments."""
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC",
            is_active=True
        )
        Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE",
            is_active=False  # inactive
        )
        
        self.assertEqual(self.faculty.departments_count, 1)
    
    def test_representatives_count_zero_initially(self):
        """Test that representatives_count is 0 for new faculty."""
        self.assertEqual(self.faculty.representatives_count, 0)
    
    def test_representatives_count_with_representatives(self):
        """Test representatives_count with active representatives."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            is_active=True
        )
        Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=department,
            faculty=self.faculty,
            university=self.university,
            role="FACULTY_PRESIDENT",
            tenure_start_year=2024,
            is_active=True
        )
        
        self.assertEqual(self.faculty.representatives_count, 2)
    
    def test_representatives_count_excludes_inactive_representatives(self):
        """Test that representatives_count excludes inactive representatives."""
        department = Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            is_active=True
        )
        Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=department,
            faculty=self.faculty,
            university=self.university,
            role="FACULTY_PRESIDENT",
            tenure_start_year=2024,
            is_active=False  # inactive
        )
        
        self.assertEqual(self.faculty.representatives_count, 1)
    
    def test_full_name_property(self):
        """Test full_name property returns correct format."""
        expected = f"{self.university.abbreviation} - {self.faculty.name}"
        self.assertEqual(self.faculty.full_name, expected)
        self.assertEqual(self.faculty.full_name, "UNIBEN - Faculty of Engineering")


class FacultyStringRepresentationTest(TestCase):
    """Test string representation."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_str_format(self):
        """Test __str__ returns correct format."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        self.assertEqual(str(faculty), "UNIBEN - Faculty of Engineering")
    
    def test_str_with_different_data(self):
        """Test __str__ with different faculty data."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        self.assertEqual(str(faculty), "UNIBEN - Faculty of Science")


class FacultyMetaOptionsTest(TestCase):
    """Test model Meta options."""
    
    def setUp(self):
        """Create test universities."""
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
    
    def test_ordering_by_university_then_name(self):
        """Test that faculties are ordered by university name, then faculty name."""
        Faculty.objects.create(
            university=self.university2,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        Faculty.objects.create(
            university=self.university1,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        Faculty.objects.create(
            university=self.university1,
            name="Faculty of Arts",
            abbreviation="ARTS"
        )
        
        faculties = list(Faculty.objects.all())
        # Should be ordered by university name (Alpha before Beta)
        # Then by faculty name within same university
        self.assertEqual(faculties[0].university.name, "Alpha University")
        self.assertEqual(faculties[0].name, "Faculty of Arts")
        self.assertEqual(faculties[1].university.name, "Alpha University")
        self.assertEqual(faculties[1].name, "Faculty of Science")
        self.assertEqual(faculties[2].university.name, "Beta University")
    
    def test_verbose_name(self):
        """Test verbose_name is set correctly."""
        self.assertEqual(Faculty._meta.verbose_name, "Faculty")
    
    def test_verbose_name_plural(self):
        """Test verbose_name_plural is set correctly."""
        self.assertEqual(Faculty._meta.verbose_name_plural, "Faculties")
    
    def test_unique_together_constraint(self):
        """Test unique_together constraint on university and name."""
        faculty = Faculty.objects.create(
            university=self.university1,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        # Should raise IntegrityError for duplicate university + name
        with self.assertRaises(IntegrityError):
            Faculty.objects.create(
                university=self.university1,
                name="Faculty of Engineering",
                abbreviation="ENGR"
            )


class FacultyEdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_very_long_name(self):
        """Test faculty with very long name."""
        long_name = "A" * 255  # Max length
        faculty = Faculty.objects.create(
            university=self.university,
            name=long_name,
            abbreviation="LONG"
        )
        
        self.assertEqual(faculty.name, long_name)
        self.assertEqual(len(faculty.name), 255)
    
    def test_name_exceeding_max_length_fails(self):
        """Test that name exceeding 255 characters fails."""
        long_name = "A" * 256  # Over max length
        faculty = Faculty(
            university=self.university,
            name=long_name,
            abbreviation="LONG"
        )
        
        with self.assertRaises(ValidationError):
            faculty.full_clean()
    
    def test_abbreviation_max_length(self):
        """Test abbreviation at max length."""
        abbr = "A" * 20  # Max length
        faculty = Faculty.objects.create(
            university=self.university,
            name="Test Faculty",
            abbreviation=abbr
        )
        
        self.assertEqual(len(faculty.abbreviation), 20)
    
    def test_abbreviation_exceeding_max_length_fails(self):
        """Test that abbreviation exceeding 20 characters fails."""
        abbr = "A" * 21  # Over max length
        faculty = Faculty(
            university=self.university,
            name="Test Faculty",
            abbreviation=abbr
        )
        
        with self.assertRaises(ValidationError):
            faculty.full_clean()
    
    def test_unicode_characters_in_name(self):
        """Test faculty name with unicode characters."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculté d'Ingénierie",  # with accents
            abbreviation="FI"
        )
        
        self.assertEqual(faculty.name, "Faculté d'Ingénierie")
    
    def test_special_characters_in_name(self):
        """Test faculty name with special characters."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering & Technology",
            abbreviation="ENGTECH"
        )
        
        self.assertIn("&", faculty.name)
    
    def test_update_faculty_name(self):
        """Test updating faculty name."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Old Name",
            abbreviation="ON"
        )
        
        faculty.name = "New Name"
        faculty.save()
        
        faculty.refresh_from_db()
        self.assertEqual(faculty.name, "New Name")
    
    def test_update_faculty_abbreviation(self):
        """Test updating faculty abbreviation."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Test Faculty",
            abbreviation="OLD"
        )
        
        faculty.abbreviation = "new"
        faculty.save()
        
        faculty.refresh_from_db()
        self.assertEqual(faculty.abbreviation, "NEW")  # should be uppercase
    
    def test_change_faculty_university(self):
        """Test changing faculty's university."""
        university2 = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        faculty.university = university2
        faculty.save()
        
        faculty.refresh_from_db()
        self.assertEqual(faculty.university.id, university2.id)
    
    def test_toggle_is_active_status(self):
        """Test toggling is_active status."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Test Faculty",
            abbreviation="TF",
            is_active=True
        )
        
        faculty.is_active = False
        faculty.save()
        
        faculty.refresh_from_db()
        self.assertFalse(faculty.is_active)
        
        faculty.is_active = True
        faculty.save()
        
        faculty.refresh_from_db()
        self.assertTrue(faculty.is_active)


class FacultyIndexingTest(TestCase):
    """Test database indexes."""
    
    def test_university_name_composite_index_exists(self):
        """Test that composite index on university and name exists."""
        indexes = [index.fields for index in Faculty._meta.indexes]
        self.assertIn(['university', 'name'], indexes)
    
    def test_abbreviation_index_exists(self):
        """Test that abbreviation field has an index."""
        indexes = [index.fields for index in Faculty._meta.indexes]
        self.assertIn(['abbreviation'], indexes)


class FacultyTimestampsTest(TestCase):
    """Test created_at and updated_at timestamps."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_created_at_auto_set_on_creation(self):
        """Test that created_at is automatically set."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        self.assertIsNotNone(faculty.created_at)
    
    def test_updated_at_auto_set_on_creation(self):
        """Test that updated_at is automatically set."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        self.assertIsNotNone(faculty.updated_at)
    
    def test_updated_at_changes_on_update(self):
        """Test that updated_at changes when model is updated."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        original_updated_at = faculty.updated_at
        
        # Wait a moment and update
        import time
        time.sleep(0.01)
        
        faculty.name = "Updated Faculty"
        faculty.save()
        
        faculty.refresh_from_db()
        self.assertGreater(faculty.updated_at, original_updated_at)
    
    def test_created_at_does_not_change_on_update(self):
        """Test that created_at does not change on update."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        
        original_created_at = faculty.created_at
        
        faculty.name = "Updated Faculty"
        faculty.save()
        
        faculty.refresh_from_db()
        self.assertEqual(faculty.created_at, original_created_at)