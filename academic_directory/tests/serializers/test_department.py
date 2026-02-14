# academic_directory/tests/serializers/test_department.py
"""
Comprehensive test suite for Department serializers.

Test Coverage:
- DepartmentListSerializer (lightweight listing)
- DepartmentSerializer (full details with nested faculty)
- Serialization (model to JSON)
- Deserialization (JSON to model)
- Nested faculty detail
- Field validation
- Required fields
- Read-only fields (created_at, updated_at, counts, full_name, program_duration)
- Computed fields (representatives_count, program_duration, full_name)
- Foreign key validation (faculty must exist)
- Edge cases
"""

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from academic_directory.models import University, Faculty, Department, Representative, ProgramDuration
from academic_directory.serializers import DepartmentSerializer, DepartmentListSerializer


class DepartmentListSerializerTest(TestCase):
    """Test DepartmentListSerializer."""
    
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
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = DepartmentListSerializer(self.department)
        data = serializer.data
        
        expected_fields = {
            'id', 'name', 'abbreviation', 'faculty',
            'faculty_name', 'university_name', 'program_duration',
            'representatives_count', 'is_active'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = DepartmentListSerializer(self.department)
        data = serializer.data
        
        self.assertEqual(data['name'], "Computer Science")
        self.assertEqual(data['abbreviation'], "CSC")
        self.assertEqual(data['faculty'], str(self.faculty.id))
        self.assertTrue(data['is_active'])
    
    def test_serialization_display_fields(self):
        """Test serialization of display fields."""
        serializer = DepartmentListSerializer(self.department)
        data = serializer.data
        
        self.assertEqual(data['faculty_name'], "Faculty of Engineering")
        self.assertEqual(data['university_name'], "University of Benin")
    
    def test_serialization_program_duration_null(self):
        """Test serialization when no program duration exists."""
        serializer = DepartmentListSerializer(self.department)
        data = serializer.data
        
        self.assertIsNone(data['program_duration'])
    
    def test_serialization_program_duration_exists(self):
        """Test serialization when program duration exists."""
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        
        serializer = DepartmentListSerializer(self.department)
        data = serializer.data
        
        self.assertEqual(data['program_duration'], 4)
    
    def test_serialization_representatives_count(self):
        """Test serialization of representatives count."""
        Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        
        serializer = DepartmentListSerializer(self.department)
        data = serializer.data
        
        self.assertEqual(data['representatives_count'], 1)
    
    def test_serialization_zero_count_initially(self):
        """Test that count is 0 for new department."""
        serializer = DepartmentListSerializer(self.department)
        data = serializer.data
        
        self.assertEqual(data['representatives_count'], 0)
    
    def test_serialize_multiple_departments(self):
        """Test serializing multiple departments."""
        dept2 = Department.objects.create(
            faculty=self.faculty,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        
        serializer = DepartmentListSerializer([self.department, dept2], many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['abbreviation'], "CSC")
        self.assertEqual(data[1]['abbreviation'], "EEE")


class DepartmentSerializerSerializationTest(TestCase):
    """Test DepartmentSerializer serialization (model to JSON)."""
    
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
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = DepartmentSerializer(self.department)
        data = serializer.data
        
        expected_fields = {
            'id', 'name', 'abbreviation', 'full_name', 'faculty',
            'faculty_detail', 'university_name', 'university_abbreviation',
            'program_duration', 'representatives_count', 'is_active',
            'created_at', 'updated_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = DepartmentSerializer(self.department)
        data = serializer.data
        
        self.assertEqual(data['name'], "Computer Science")
        self.assertEqual(data['abbreviation'], "CSC")
        self.assertEqual(data['faculty'], str(self.faculty.id))
        self.assertTrue(data['is_active'])
    
    def test_serialization_nested_faculty_detail(self):
        """Test serialization of nested faculty detail."""
        serializer = DepartmentSerializer(self.department)
        data = serializer.data
        
        self.assertIn('faculty_detail', data)
        self.assertIsInstance(data['faculty_detail'], dict)
        self.assertEqual(data['faculty_detail']['name'], "Faculty of Engineering")
        self.assertEqual(data['faculty_detail']['abbreviation'], "ENG")
    
    def test_serialization_university_fields(self):
        """Test serialization of university fields through faculty."""
        serializer = DepartmentSerializer(self.department)
        data = serializer.data
        
        self.assertEqual(data['university_name'], "University of Benin")
        self.assertEqual(data['university_abbreviation'], "UNIBEN")
    
    def test_serialization_full_name_property(self):
        """Test serialization of full_name property."""
        serializer = DepartmentSerializer(self.department)
        data = serializer.data
        
        expected_full_name = f"{self.university.abbreviation} {self.faculty.abbreviation} - {self.department.name}"
        self.assertEqual(data['full_name'], expected_full_name)
        self.assertEqual(data['full_name'], "UNIBEN ENG - Computer Science")
    
    def test_serialization_timestamps(self):
        """Test serialization of timestamp fields."""
        serializer = DepartmentSerializer(self.department)
        data = serializer.data
        
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIsNotNone(data['created_at'])
        self.assertIsNotNone(data['updated_at'])
    
    def test_serialization_program_duration_with_value(self):
        """Test program_duration field when it exists."""
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=5,
            program_type='BENG'
        )
        
        serializer = DepartmentSerializer(self.department)
        data = serializer.data
        
        self.assertEqual(data['program_duration'], 5)


class DepartmentSerializerDeserializationTest(TestCase):
    """Test DepartmentSerializer deserialization (JSON to model)."""
    
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
    
    def test_deserialization_with_valid_data(self):
        """Test deserialization with all valid data."""
        data = {
            'name': 'Electrical Engineering',
            'abbreviation': 'EEE',
            'faculty': str(self.faculty.id),
            'is_active': True
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.name, 'Electrical Engineering')
        self.assertEqual(department.abbreviation, 'EEE')
        self.assertEqual(department.faculty, self.faculty)
        self.assertTrue(department.is_active)
    
    def test_deserialization_minimal_required_fields(self):
        """Test deserialization with only required fields."""
        data = {
            'name': 'Test Department',
            'abbreviation': 'TEST',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertIsNotNone(department.id)
        self.assertTrue(department.is_active)
    
    def test_deserialization_lowercase_abbreviation_converted(self):
        """Test that lowercase abbreviation is converted to uppercase."""
        data = {
            'name': 'Test Department',
            'abbreviation': 'test',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.abbreviation, 'TEST')
    
    def test_deserialization_missing_name_fails(self):
        """Test that missing name fails validation."""
        data = {
            'abbreviation': 'TEST',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_deserialization_missing_abbreviation_fails(self):
        """Test that missing abbreviation fails validation."""
        data = {
            'name': 'Test Department',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('abbreviation', serializer.errors)
    
    def test_deserialization_missing_faculty_fails(self):
        """Test that missing faculty fails validation."""
        data = {
            'name': 'Test Department',
            'abbreviation': 'TEST'
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('faculty', serializer.errors)
    
    def test_deserialization_invalid_faculty_id_fails(self):
        """Test that invalid faculty ID fails validation."""
        data = {
            'name': 'Test Department',
            'abbreviation': 'TEST',
            'faculty': '99999999-9999-9999-9999-999999999999'
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('faculty', serializer.errors)
    
    def test_deserialization_empty_name_fails(self):
        """Test that empty name fails validation."""
        data = {
            'name': '',
            'abbreviation': 'TEST',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_deserialization_whitespace_name_fails(self):
        """Test that whitespace-only name fails validation."""
        data = {
            'name': '   ',
            'abbreviation': 'TEST',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_deserialization_duplicate_name_in_faculty_fails(self):
        """Test that duplicate department name in same faculty fails."""
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC"
        )
        
        data = {
            'name': 'Computer Science',
            'abbreviation': 'CS',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class DepartmentSerializerUpdateTest(TestCase):
    """Test updating departments via serializer."""
    
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
    
    def test_update_name(self):
        """Test updating department name."""
        data = {
            'name': 'Computer Engineering',
            'abbreviation': self.department.abbreviation,
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(self.department, data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.name, 'Computer Engineering')
    
    def test_update_abbreviation(self):
        """Test updating abbreviation."""
        data = {
            'name': self.department.name,
            'abbreviation': 'CPE',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(self.department, data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.abbreviation, 'CPE')
    
    def test_update_faculty(self):
        """Test changing department's faculty."""
        faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        data = {
            'name': self.department.name,
            'abbreviation': self.department.abbreviation,
            'faculty': str(faculty2.id)
        }
        
        serializer = DepartmentSerializer(self.department, data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.faculty, faculty2)
    
    def test_update_is_active(self):
        """Test updating is_active status."""
        data = {
            'name': self.department.name,
            'abbreviation': self.department.abbreviation,
            'faculty': str(self.faculty.id),
            'is_active': False
        }
        
        serializer = DepartmentSerializer(self.department, data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertFalse(department.is_active)
    
    def test_partial_update(self):
        """Test partial update."""
        data = {'name': 'Partially Updated Name'}
        
        serializer = DepartmentSerializer(self.department, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.name, 'Partially Updated Name')
        self.assertEqual(department.abbreviation, 'CSC')


class DepartmentSerializerReadOnlyFieldsTest(TestCase):
    """Test read-only fields."""
    
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
    
    def test_created_at_is_read_only(self):
        """Test that created_at cannot be set via serializer."""
        from datetime import datetime, timedelta
        
        fake_date = datetime.now() - timedelta(days=365)
        data = {
            'name': 'Test Department',
            'abbreviation': 'TEST',
            'faculty': str(self.faculty.id),
            'created_at': fake_date.isoformat()
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertNotEqual(department.created_at.date(), fake_date.date())
    
    def test_updated_at_is_read_only(self):
        """Test that updated_at cannot be set via serializer."""
        from datetime import datetime, timedelta
        
        fake_date = datetime.now() - timedelta(days=365)
        data = {
            'name': self.department.name,
            'abbreviation': self.department.abbreviation,
            'faculty': str(self.faculty.id),
            'updated_at': fake_date.isoformat()
        }
        
        serializer = DepartmentSerializer(self.department, data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertNotEqual(department.updated_at.date(), fake_date.date())
    
    def test_representatives_count_cannot_be_set(self):
        """Test that representatives_count is computed."""
        data = {
            'name': 'Test Department',
            'abbreviation': 'TEST',
            'faculty': str(self.faculty.id),
            'representatives_count': 999
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.representatives_count, 0)
    
    def test_program_duration_cannot_be_set(self):
        """Test that program_duration is computed."""
        data = {
            'name': 'Test Department',
            'abbreviation': 'TEST',
            'faculty': str(self.faculty.id),
            'program_duration': 999
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertIsNone(department.program_duration)
    
    def test_full_name_is_read_only(self):
        """Test that full_name is computed."""
        data = {
            'name': 'Test Department',
            'abbreviation': 'TEST',
            'faculty': str(self.faculty.id),
            'full_name': 'FAKE Full Name'
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        expected = f"{self.university.abbreviation} {self.faculty.abbreviation} - {department.name}"
        self.assertEqual(department.full_name, expected)
        self.assertNotEqual(department.full_name, 'FAKE Full Name')


class DepartmentSerializerEdgeCasesTest(TestCase):
    """Test edge cases."""
    
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
        """Test department with maximum length name."""
        long_name = "A" * 255
        data = {
            'name': long_name,
            'abbreviation': 'LONG',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(len(department.name), 255)
    
    def test_name_exceeding_max_length_fails(self):
        """Test that name exceeding max length fails."""
        long_name = "A" * 256
        data = {
            'name': long_name,
            'abbreviation': 'LONG',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_unicode_characters_in_name(self):
        """Test department name with unicode characters."""
        data = {
            'name': 'Département d\'Informatique',
            'abbreviation': 'INFO',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.name, 'Département d\'Informatique')
    
    def test_special_characters_in_name(self):
        """Test department name with special characters."""
        data = {
            'name': 'Computer Science & Engineering',
            'abbreviation': 'CSE',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertIn('&', department.name)
    
    def test_abbreviation_with_numbers_fails(self):
        """Test that abbreviation with numbers fails validation."""
        data = {
            'name': 'Test Department',
            'abbreviation': 'TEST123',
            'faculty': str(self.faculty.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('abbreviation', serializer.errors)
    
    def test_same_name_in_different_faculties_allowed(self):
        """Test that same department name in different faculties is allowed."""
        faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC1"
        )
        
        data = {
            'name': 'Computer Science',
            'abbreviation': 'CSC2',
            'faculty': str(faculty2.id)
        }
        
        serializer = DepartmentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        department = serializer.save()
        
        self.assertEqual(department.name, 'Computer Science')
        self.assertEqual(department.faculty, faculty2)