# academic_directory/tests/models/test_university.py
"""
Comprehensive test suite for University model.

Test Coverage:
- Model creation and basic functionality
- Field validation and constraints
- Unique constraints (name, abbreviation)
- Abbreviation uppercase enforcement
- Clean method validation
- Save hooks
- Properties (faculties_count, departments_count, representatives_count)
- String representation
- Edge cases and boundary conditions
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from academic_directory.models import University, Faculty, Department, Representative
import uuid


class UniversityCreationTest(TestCase):
    """Test basic university creation and model functionality."""
    
    def test_create_university_with_valid_data(self):
        """Test creating a university with all valid data."""
        university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
        
        self.assertIsNotNone(university.id)
        self.assertIsInstance(university.id, uuid.UUID)
        self.assertEqual(university.name, "University of Benin")
        self.assertEqual(university.abbreviation, "UNIBEN")
        self.assertEqual(university.state, "EDO")
        self.assertEqual(university.type, "FEDERAL")
        self.assertTrue(university.is_active)
        self.assertIsNotNone(university.created_at)
        self.assertIsNotNone(university.updated_at)
    
    def test_create_state_university(self):
        """Test creating a state university."""
        university = University.objects.create(
            name="Lagos State University",
            abbreviation="LASU",
            state="LAGOS",
            type="STATE"
        )
        
        self.assertEqual(university.type, "STATE")
        self.assertEqual(university.state, "LAGOS")
    
    def test_create_private_university(self):
        """Test creating a private university."""
        university = University.objects.create(
            name="Babcock University",
            abbreviation="BABCOCK",
            state="OGUN",
            type="PRIVATE"
        )
        
        self.assertEqual(university.type, "PRIVATE")
    
    def test_default_is_active_true(self):
        """Test that is_active defaults to True."""
        university = University.objects.create(
            name="Test University",
            abbreviation="TU",
            state="LAGOS",
            type="FEDERAL"
        )
        
        self.assertTrue(university.is_active)
    
    def test_create_inactive_university(self):
        """Test creating an inactive university."""
        university = University.objects.create(
            name="Inactive University",
            abbreviation="IU",
            state="LAGOS",
            type="FEDERAL",
            is_active=False
        )
        
        self.assertFalse(university.is_active)


class UniversityFieldValidationTest(TestCase):
    """Test field-level validation."""
    
    def test_abbreviation_must_be_uppercase(self):
        """Test that lowercase abbreviation is converted to uppercase."""
        university = University.objects.create(
            name="Test University",
            abbreviation="test",  # lowercase
            state="LAGOS",
            type="FEDERAL"
        )
        
        # Should be automatically converted to uppercase
        university.refresh_from_db()
        self.assertEqual(university.abbreviation, "TEST")
    
    def test_abbreviation_mixed_case_converted_to_uppercase(self):
        """Test that mixed case abbreviation is converted to uppercase."""
        university = University.objects.create(
            name="Test University",
            abbreviation="TeSt",  # mixed case
            state="LAGOS",
            type="FEDERAL"
        )
        
        university.refresh_from_db()
        self.assertEqual(university.abbreviation, "TEST")
    
    def test_abbreviation_with_numbers_fails_validation(self):
        """Test that abbreviation with numbers fails regex validation."""
        university = University(
            name="Test University",
            abbreviation="TEST123",
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_abbreviation_with_spaces_fails_validation(self):
        """Test that abbreviation with spaces fails validation."""
        university = University(
            name="Test University",
            abbreviation="TE ST",
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_abbreviation_with_special_characters_fails_validation(self):
        """Test that abbreviation with special characters fails validation."""
        university = University(
            name="Test University",
            abbreviation="TEST-1",
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.full_clean()
        
        self.assertIn('abbreviation', context.exception.message_dict)
    
    def test_empty_name_fails_validation(self):
        """Test that empty name fails validation."""
        university = University(
            name="",
            abbreviation="TEST",
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.full_clean()
        
        self.assertIn('name', context.exception.message_dict)
    
    def test_whitespace_only_name_fails_validation(self):
        """Test that whitespace-only name fails validation."""
        university = University(
            name="   ",
            abbreviation="TEST",
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.save()
        
        self.assertIn('name', str(context.exception))
    
    def test_valid_nigerian_states(self):
        """Test all valid Nigerian states."""
        valid_states = [
            'ABIA', 'ADAMAWA', 'AKWA_IBOM', 'ANAMBRA', 'BAUCHI',
            'BAYELSA', 'BENUE', 'BORNO', 'CROSS_RIVER', 'DELTA',
            'EBONYI', 'EDO', 'EKITI', 'ENUGU', 'FCT', 'GOMBE',
            'IMO', 'JIGAWA', 'KADUNA', 'KANO', 'KATSINA', 'KEBBI',
            'KOGI', 'KWARA', 'LAGOS', 'NASARAWA', 'NIGER', 'OGUN',
            'ONDO', 'OSUN', 'OYO', 'PLATEAU', 'RIVERS', 'SOKOTO',
            'TARABA', 'YOBE', 'ZAMFARA'
        ]
        
        for state in valid_states:
            university = University.objects.create(
                name=f"Test University {state}",
                abbreviation=f"TU{state[:3]}",
                state=state,
                type="FEDERAL"
            )
            self.assertEqual(university.state, state)
    
    def test_invalid_state_fails_validation(self):
        """Test that invalid state fails validation."""
        university = University(
            name="Test University",
            abbreviation="TEST",
            state="INVALID_STATE",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.full_clean()
        
        self.assertIn('state', context.exception.message_dict)
    
    def test_valid_university_types(self):
        """Test all valid university types."""
        for uni_type in ['FEDERAL', 'STATE', 'PRIVATE']:
            university = University.objects.create(
                name=f"Test {uni_type} University",
                abbreviation=f"T{uni_type[:3]}",
                state="LAGOS",
                type=uni_type
            )
            self.assertEqual(university.type, uni_type)
    
    def test_invalid_university_type_fails_validation(self):
        """Test that invalid university type fails validation."""
        university = University(
            name="Test University",
            abbreviation="TEST",
            state="LAGOS",
            type="INVALID_TYPE"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.full_clean()
        
        self.assertIn('type', context.exception.message_dict)


class UniversityUniqueConstraintsTest(TestCase):
    """Test unique constraints on name and abbreviation."""
    
    def setUp(self):
        """Create a test university for duplicate tests."""
        self.university = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
    
    def test_duplicate_name_fails(self):
        """Test that duplicate name raises IntegrityError."""
        with self.assertRaises(IntegrityError):
            University.objects.create(
                name="University of Lagos",  # duplicate
                abbreviation="UNILAG2",
                state="LAGOS",
                type="FEDERAL"
            )
    
    def test_duplicate_abbreviation_fails(self):
        """Test that duplicate abbreviation raises IntegrityError."""
        with self.assertRaises(IntegrityError):
            University.objects.create(
                name="Another University",
                abbreviation="UNILAG",  # duplicate
                state="LAGOS",
                type="STATE"
            )
    
    def test_case_sensitive_name_uniqueness(self):
        """Test that name uniqueness is case-sensitive in database."""
        # This might succeed or fail depending on database collation
        # but we test the behavior
        try:
            university = University.objects.create(
                name="university of lagos",  # different case
                abbreviation="UL",
                state="LAGOS",
                type="STATE"
            )
            # If it succeeds, names are case-sensitive
            self.assertIsNotNone(university.id)
        except IntegrityError:
            # If it fails, database is case-insensitive
            pass
    
    def test_same_university_different_states_allowed(self):
        """Test that same name/abbreviation but different everything else is not allowed."""
        # Universities must have unique names and abbreviations regardless of state
        with self.assertRaises(IntegrityError):
            University.objects.create(
                name="University of Lagos",
                abbreviation="UL",
                state="RIVERS",  # different state
                type="STATE"
            )


class UniversityCleanMethodTest(TestCase):
    """Test the clean() method validation."""
    
    def test_clean_converts_abbreviation_to_uppercase(self):
        """Test that clean() converts abbreviation to uppercase."""
        university = University(
            name="Test University",
            abbreviation="test",
            state="LAGOS",
            type="FEDERAL"
        )
        
        university.clean()
        self.assertEqual(university.abbreviation, "TEST")
    
    def test_clean_validates_empty_name(self):
        """Test that clean() catches empty name."""
        university = University(
            name="",
            abbreviation="TEST",
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.clean()
        
        self.assertIn('name', str(context.exception))
    
    def test_clean_validates_whitespace_name(self):
        """Test that clean() catches whitespace-only name."""
        university = University(
            name="   ",
            abbreviation="TEST",
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError) as context:
            university.clean()
        
        self.assertIn('name', str(context.exception))
    
    def test_clean_called_on_save(self):
        """Test that save() calls clean()."""
        university = University(
            name="Test University",
            abbreviation="test",  # lowercase
            state="LAGOS",
            type="FEDERAL"
        )
        
        university.save()
        self.assertEqual(university.abbreviation, "TEST")


class UniversityPropertiesTest(TestCase):
    """Test computed properties."""
    
    def setUp(self):
        """Set up test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_faculties_count_zero_initially(self):
        """Test that faculties_count is 0 for new university."""
        self.assertEqual(self.university.faculties_count, 0)
    
    def test_faculties_count_with_active_faculties(self):
        """Test faculties_count with active faculties."""
        Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG",
            is_active=True
        )
        Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI",
            is_active=True
        )
        
        self.assertEqual(self.university.faculties_count, 2)
    
    def test_faculties_count_excludes_inactive_faculties(self):
        """Test that faculties_count excludes inactive faculties."""
        Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG",
            is_active=True
        )
        Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI",
            is_active=False  # inactive
        )
        
        self.assertEqual(self.university.faculties_count, 1)
    
    def test_departments_count_zero_initially(self):
        """Test that departments_count is 0 for new university."""
        self.assertEqual(self.university.departments_count, 0)
    
    def test_departments_count_with_departments(self):
        """Test departments_count with active departments."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        Department.objects.create(
            faculty=faculty,
            name="Computer Science",
            abbreviation="CSC",
            is_active=True
        )
        Department.objects.create(
            faculty=faculty,
            name="Electrical Engineering",
            abbreviation="EEE",
            is_active=True
        )
        
        self.assertEqual(self.university.departments_count, 2)
    
    def test_departments_count_excludes_inactive_departments(self):
        """Test that departments_count excludes inactive departments."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        Department.objects.create(
            faculty=faculty,
            name="Computer Science",
            abbreviation="CSC",
            is_active=True
        )
        Department.objects.create(
            faculty=faculty,
            name="Electrical Engineering",
            abbreviation="EEE",
            is_active=False  # inactive
        )
        
        self.assertEqual(self.university.departments_count, 1)
    
    def test_departments_count_across_multiple_faculties(self):
        """Test departments_count across multiple faculties."""
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
        
        Department.objects.create(
            faculty=faculty1,
            name="Computer Science",
            abbreviation="CSC"
        )
        Department.objects.create(
            faculty=faculty2,
            name="Mathematics",
            abbreviation="MTH"
        )
        
        self.assertEqual(self.university.departments_count, 2)
    
    def test_representatives_count_zero_initially(self):
        """Test that representatives_count is 0 for new university."""
        self.assertEqual(self.university.representatives_count, 0)
    
    def test_representatives_count_with_representatives(self):
        """Test representatives_count with active representatives."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        department = Department.objects.create(
            faculty=faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=department,
            faculty=faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            is_active=True
        )
        Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=department,
            faculty=faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024,
            is_active=True
        )
        
        self.assertEqual(self.university.representatives_count, 2)
    
    def test_representatives_count_excludes_inactive_representatives(self):
        """Test that representatives_count excludes inactive representatives."""
        faculty = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        department = Department.objects.create(
            faculty=faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=department,
            faculty=faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            is_active=True
        )
        Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08098765432",
            department=department,
            faculty=faculty,
            university=self.university,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024,
            is_active=False  # inactive
        )
        
        self.assertEqual(self.university.representatives_count, 1)


class UniversityStringRepresentationTest(TestCase):
    """Test string representation."""
    
    def test_str_format(self):
        """Test __str__ returns correct format."""
        university = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        
        self.assertEqual(str(university), "UNILAG - University of Lagos")
    
    def test_str_with_different_data(self):
        """Test __str__ with different university data."""
        university = University.objects.create(
            name="Obafemi Awolowo University",
            abbreviation="OAU",
            state="OSUN",
            type="FEDERAL"
        )
        
        self.assertEqual(str(university), "OAU - Obafemi Awolowo University")


class UniversityMetaOptionsTest(TestCase):
    """Test model Meta options."""
    
    def test_ordering_by_name(self):
        """Test that universities are ordered by name."""
        University.objects.create(
            name="Zeta University",
            abbreviation="ZU",
            state="LAGOS",
            type="FEDERAL"
        )
        University.objects.create(
            name="Alpha University",
            abbreviation="AU",
            state="LAGOS",
            type="FEDERAL"
        )
        University.objects.create(
            name="Beta University",
            abbreviation="BU",
            state="LAGOS",
            type="FEDERAL"
        )
        
        universities = list(University.objects.all())
        self.assertEqual(universities[0].name, "Alpha University")
        self.assertEqual(universities[1].name, "Beta University")
        self.assertEqual(universities[2].name, "Zeta University")
    
    def test_verbose_name(self):
        """Test verbose_name is set correctly."""
        self.assertEqual(
            University._meta.verbose_name,
            "University"
        )
    
    def test_verbose_name_plural(self):
        """Test verbose_name_plural is set correctly."""
        self.assertEqual(
            University._meta.verbose_name_plural,
            "Universities"
        )


class UniversityEdgeCasesTest(TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_very_long_name(self):
        """Test university with very long name."""
        long_name = "A" * 255  # Max length
        university = University.objects.create(
            name=long_name,
            abbreviation="LONG",
            state="LAGOS",
            type="FEDERAL"
        )
        
        self.assertEqual(university.name, long_name)
        self.assertEqual(len(university.name), 255)
    
    def test_name_exceeding_max_length_fails(self):
        """Test that name exceeding 255 characters fails."""
        long_name = "A" * 256  # Over max length
        university = University(
            name=long_name,
            abbreviation="LONG",
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError):
            university.full_clean()
    
    def test_abbreviation_max_length(self):
        """Test abbreviation at max length."""
        abbr = "A" * 20  # Max length
        university = University.objects.create(
            name="Test University",
            abbreviation=abbr,
            state="LAGOS",
            type="FEDERAL"
        )
        
        self.assertEqual(len(university.abbreviation), 20)
    
    def test_abbreviation_exceeding_max_length_fails(self):
        """Test that abbreviation exceeding 20 characters fails."""
        abbr = "A" * 21  # Over max length
        university = University(
            name="Test University",
            abbreviation=abbr,
            state="LAGOS",
            type="FEDERAL"
        )
        
        with self.assertRaises(ValidationError):
            university.full_clean()
    
    def test_unicode_characters_in_name(self):
        """Test university name with unicode characters."""
        university = University.objects.create(
            name="Université de Lagos",  # with accent
            abbreviation="UDL",
            state="LAGOS",
            type="FEDERAL"
        )
        
        self.assertEqual(university.name, "Université de Lagos")
    
    def test_special_characters_in_name(self):
        """Test university name with special characters."""
        university = University.objects.create(
            name="University of Lagos (Main Campus)",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        
        self.assertIn("(Main Campus)", university.name)
    
    def test_update_university_name(self):
        """Test updating university name."""
        university = University.objects.create(
            name="Old Name",
            abbreviation="ON",
            state="LAGOS",
            type="FEDERAL"
        )
        
        university.name = "New Name"
        university.save()
        
        university.refresh_from_db()
        self.assertEqual(university.name, "New Name")
    
    def test_update_university_abbreviation(self):
        """Test updating university abbreviation."""
        university = University.objects.create(
            name="Test University",
            abbreviation="OLD",
            state="LAGOS",
            type="FEDERAL"
        )
        
        university.abbreviation = "new"
        university.save()
        
        university.refresh_from_db()
        self.assertEqual(university.abbreviation, "NEW")  # should be uppercase
    
    def test_toggle_is_active_status(self):
        """Test toggling is_active status."""
        university = University.objects.create(
            name="Test University",
            abbreviation="TU",
            state="LAGOS",
            type="FEDERAL",
            is_active=True
        )
        
        university.is_active = False
        university.save()
        
        university.refresh_from_db()
        self.assertFalse(university.is_active)
        
        university.is_active = True
        university.save()
        
        university.refresh_from_db()
        self.assertTrue(university.is_active)


class UniversityIndexingTest(TestCase):
    """Test database indexes."""
    
    def test_abbreviation_index_exists(self):
        """Test that abbreviation field has an index."""
        indexes = [index.fields for index in University._meta.indexes]
        self.assertIn(['abbreviation'], indexes)
    
    def test_state_index_exists(self):
        """Test that state field has an index."""
        indexes = [index.fields for index in University._meta.indexes]
        self.assertIn(['state'], indexes)
    
    def test_type_index_exists(self):
        """Test that type field has an index."""
        indexes = [index.fields for index in University._meta.indexes]
        self.assertIn(['type'], indexes)


class UniversityTimestampsTest(TestCase):
    """Test created_at and updated_at timestamps."""
    
    def test_created_at_auto_set_on_creation(self):
        """Test that created_at is automatically set."""
        university = University.objects.create(
            name="Test University",
            abbreviation="TU",
            state="LAGOS",
            type="FEDERAL"
        )
        
        self.assertIsNotNone(university.created_at)
    
    def test_updated_at_auto_set_on_creation(self):
        """Test that updated_at is automatically set."""
        university = University.objects.create(
            name="Test University",
            abbreviation="TU",
            state="LAGOS",
            type="FEDERAL"
        )
        
        self.assertIsNotNone(university.updated_at)
    
    def test_updated_at_changes_on_update(self):
        """Test that updated_at changes when model is updated."""
        university = University.objects.create(
            name="Test University",
            abbreviation="TU",
            state="LAGOS",
            type="FEDERAL"
        )
        
        original_updated_at = university.updated_at
        
        # Wait a moment and update
        import time
        time.sleep(0.01)
        
        university.name = "Updated University"
        university.save()
        
        university.refresh_from_db()
        self.assertGreater(university.updated_at, original_updated_at)
    
    def test_created_at_does_not_change_on_update(self):
        """Test that created_at does not change on update."""
        university = University.objects.create(
            name="Test University",
            abbreviation="TU",
            state="LAGOS",
            type="FEDERAL"
        )
        
        original_created_at = university.created_at
        
        university.name = "Updated University"
        university.save()
        
        university.refresh_from_db()
        self.assertEqual(university.created_at, original_created_at)