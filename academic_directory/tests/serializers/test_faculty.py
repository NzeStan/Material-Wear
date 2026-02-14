# academic_directory/tests/serializers/test_faculty.py
"""
Comprehensive test suite for Faculty serializers.

Test Coverage:
- FacultyListSerializer (lightweight listing)
- FacultySerializer (full details with nested university)
- Serialization (model to JSON)
- Deserialization (JSON to model)
- Nested university detail
- Field validation
- Required fields
- Read-only fields (created_at, updated_at, counts, full_name)
- Computed fields (departments_count, representatives_count, full_name)
- Foreign key validation (university must exist)
- Edge cases
"""

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from academic_directory.models import University, Faculty, Department, Representative
from academic_directory.serializers import FacultySerializer, FacultyListSerializer


class FacultyListSerializerTest(TestCase):
    """Test FacultyListSerializer."""
    
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
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = FacultyListSerializer(self.faculty)
        data = serializer.data
        
        expected_fields = {
            'id', 'name', 'abbreviation', 'university', 
            'university_name', 'university_abbreviation',
            'departments_count', 'representatives_count', 'is_active'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = FacultyListSerializer(self.faculty)
        data = serializer.data
        
        self.assertEqual(data['name'], "Faculty of Engineering")
        self.assertEqual(data['abbreviation'], "ENG")
        self.assertEqual(data['university'], str(self.university.id))
        self.assertTrue(data['is_active'])
    
    def test_serialization_university_display_fields(self):
        """Test serialization of university display fields."""
        serializer = FacultyListSerializer(self.faculty)
        data = serializer.data
        
        self.assertEqual(data['university_name'], "University of Benin")
        self.assertEqual(data['university_abbreviation'], "UNIBEN")
    
    def test_serialization_count_properties(self):
        """Test serialization of count properties."""
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
            entry_year=2020
        )
        
        serializer = FacultyListSerializer(self.faculty)
        data = serializer.data
        
        self.assertEqual(data['departments_count'], 1)
        self.assertEqual(data['representatives_count'], 1)
    
    def test_serialization_zero_counts_initially(self):
        """Test that counts are 0 for new faculty."""
        serializer = FacultyListSerializer(self.faculty)
        data = serializer.data
        
        self.assertEqual(data['departments_count'], 0)
        self.assertEqual(data['representatives_count'], 0)
    
    def test_serialize_multiple_faculties(self):
        """Test serializing multiple faculties."""
        faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        serializer = FacultyListSerializer([self.faculty, faculty2], many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['abbreviation'], "ENG")
        self.assertEqual(data[1]['abbreviation'], "SCI")


class FacultySerializerSerializationTest(TestCase):
    """Test FacultySerializer serialization (model to JSON)."""
    
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
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = FacultySerializer(self.faculty)
        data = serializer.data
        
        expected_fields = {
            'id', 'name', 'abbreviation', 'full_name', 'university',
            'university_detail', 'departments_count', 'representatives_count',
            'is_active', 'created_at', 'updated_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = FacultySerializer(self.faculty)
        data = serializer.data
        
        self.assertEqual(data['name'], "Faculty of Engineering")
        self.assertEqual(data['abbreviation'], "ENG")
        self.assertEqual(data['university'], str(self.university.id))
        self.assertTrue(data['is_active'])
    
    def test_serialization_nested_university_detail(self):
        """Test serialization of nested university detail."""
        serializer = FacultySerializer(self.faculty)
        data = serializer.data
        
        self.assertIn('university_detail', data)
        self.assertIsInstance(data['university_detail'], dict)
        self.assertEqual(data['university_detail']['name'], "University of Benin")
        self.assertEqual(data['university_detail']['abbreviation'], "UNIBEN")
        self.assertEqual(data['university_detail']['state'], "EDO")
        self.assertEqual(data['university_detail']['type'], "FEDERAL")
    
    def test_serialization_full_name_property(self):
        """Test serialization of full_name property."""
        serializer = FacultySerializer(self.faculty)
        data = serializer.data
        
        expected_full_name = f"{self.university.abbreviation} - {self.faculty.name}"
        self.assertEqual(data['full_name'], expected_full_name)
        self.assertEqual(data['full_name'], "UNIBEN - Faculty of Engineering")
    
    def test_serialization_timestamps(self):
        """Test serialization of timestamp fields."""
        serializer = FacultySerializer(self.faculty)
        data = serializer.data
        
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIsNotNone(data['created_at'])
        self.assertIsNotNone(data['updated_at'])
    
    def test_serialization_counts_with_data(self):
        """Test count fields with actual data."""
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
        
        serializer = FacultySerializer(self.faculty)
        data = serializer.data
        
        self.assertEqual(data['departments_count'], 2)


class FacultySerializerDeserializationTest(TestCase):
    """Test FacultySerializer deserialization (JSON to model)."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_deserialization_with_valid_data(self):
        """Test deserialization with all valid data."""
        data = {
            'name': 'Faculty of Science',
            'abbreviation': 'SCI',
            'university': str(self.university.id),
            'is_active': True
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertEqual(faculty.name, 'Faculty of Science')
        self.assertEqual(faculty.abbreviation, 'SCI')
        self.assertEqual(faculty.university, self.university)
        self.assertTrue(faculty.is_active)
    
    def test_deserialization_minimal_required_fields(self):
        """Test deserialization with only required fields."""
        data = {
            'name': 'Test Faculty',
            'abbreviation': 'TEST',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertIsNotNone(faculty.id)
        self.assertTrue(faculty.is_active)  # Default value
    
    def test_deserialization_lowercase_abbreviation_converted(self):
        """Test that lowercase abbreviation is converted to uppercase."""
        data = {
            'name': 'Test Faculty',
            'abbreviation': 'test',  # lowercase
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertEqual(faculty.abbreviation, 'TEST')
    
    def test_deserialization_missing_name_fails(self):
        """Test that missing name fails validation."""
        data = {
            'abbreviation': 'TEST',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_deserialization_missing_abbreviation_fails(self):
        """Test that missing abbreviation fails validation."""
        data = {
            'name': 'Test Faculty',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('abbreviation', serializer.errors)
    
    def test_deserialization_missing_university_fails(self):
        """Test that missing university fails validation."""
        data = {
            'name': 'Test Faculty',
            'abbreviation': 'TEST'
        }
        
        serializer = FacultySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('university', serializer.errors)
    
    def test_deserialization_invalid_university_id_fails(self):
        """Test that invalid university ID fails validation."""
        data = {
            'name': 'Test Faculty',
            'abbreviation': 'TEST',
            'university': '99999999-9999-9999-9999-999999999999'
        }
        
        serializer = FacultySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('university', serializer.errors)
    
    def test_deserialization_empty_name_fails(self):
        """Test that empty name fails validation."""
        data = {
            'name': '',
            'abbreviation': 'TEST',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_deserialization_whitespace_name_fails(self):
        """Test that whitespace-only name fails validation."""
        data = {
            'name': '   ',
            'abbreviation': 'TEST',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)


class FacultySerializerUpdateTest(TestCase):
    """Test updating faculties via serializer."""
    
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
    
    def test_update_name(self):
        """Test updating faculty name."""
        data = {
            'name': 'Updated Faculty Name',
            'abbreviation': self.faculty.abbreviation,
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(self.faculty, data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertEqual(faculty.name, 'Updated Faculty Name')
    
    def test_update_abbreviation(self):
        """Test updating abbreviation."""
        data = {
            'name': self.faculty.name,
            'abbreviation': 'NEW',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(self.faculty, data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertEqual(faculty.abbreviation, 'NEW')
    
    def test_update_university(self):
        """Test changing faculty's university."""
        university2 = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        
        data = {
            'name': self.faculty.name,
            'abbreviation': self.faculty.abbreviation,
            'university': str(university2.id)
        }
        
        serializer = FacultySerializer(self.faculty, data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertEqual(faculty.university, university2)
    
    def test_update_is_active(self):
        """Test updating is_active status."""
        data = {
            'name': self.faculty.name,
            'abbreviation': self.faculty.abbreviation,
            'university': str(self.university.id),
            'is_active': False
        }
        
        serializer = FacultySerializer(self.faculty, data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertFalse(faculty.is_active)
    
    def test_partial_update(self):
        """Test partial update."""
        data = {'name': 'Partially Updated Name'}
        
        serializer = FacultySerializer(self.faculty, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertEqual(faculty.name, 'Partially Updated Name')
        self.assertEqual(faculty.abbreviation, 'ENG')  # Unchanged


class FacultySerializerReadOnlyFieldsTest(TestCase):
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
    
    def test_created_at_is_read_only(self):
        """Test that created_at cannot be set via serializer."""
        from datetime import datetime, timedelta
        
        fake_date = datetime.now() - timedelta(days=365)
        data = {
            'name': 'Test Faculty',
            'abbreviation': 'TEST',
            'university': str(self.university.id),
            'created_at': fake_date.isoformat()
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        # created_at should be auto-generated
        self.assertNotEqual(faculty.created_at.date(), fake_date.date())
    
    def test_updated_at_is_read_only(self):
        """Test that updated_at cannot be set via serializer."""
        from datetime import datetime, timedelta
        
        fake_date = datetime.now() - timedelta(days=365)
        data = {
            'name': self.faculty.name,
            'abbreviation': self.faculty.abbreviation,
            'university': str(self.university.id),
            'updated_at': fake_date.isoformat()
        }
        
        serializer = FacultySerializer(self.faculty, data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        # updated_at should be auto-generated
        self.assertNotEqual(faculty.updated_at.date(), fake_date.date())
    
    def test_count_fields_cannot_be_set(self):
        """Test that count fields are computed and cannot be set."""
        data = {
            'name': 'Test Faculty',
            'abbreviation': 'TEST',
            'university': str(self.university.id),
            'departments_count': 999,
            'representatives_count': 999
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        # Counts should be 0 (computed from actual data)
        self.assertEqual(faculty.departments_count, 0)
        self.assertEqual(faculty.representatives_count, 0)
    
    def test_full_name_is_read_only(self):
        """Test that full_name is computed and cannot be set."""
        data = {
            'name': 'Test Faculty',
            'abbreviation': 'TEST',
            'university': str(self.university.id),
            'full_name': 'FAKE - Full Name'
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        # full_name should be computed
        expected = f"{self.university.abbreviation} - {faculty.name}"
        self.assertEqual(faculty.full_name, expected)
        self.assertNotEqual(faculty.full_name, 'FAKE - Full Name')


class FacultySerializerEdgeCasesTest(TestCase):
    """Test edge cases."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_very_long_name(self):
        """Test faculty with maximum length name."""
        long_name = "A" * 255
        data = {
            'name': long_name,
            'abbreviation': 'LONG',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertEqual(len(faculty.name), 255)
    
    def test_name_exceeding_max_length_fails(self):
        """Test that name exceeding max length fails."""
        long_name = "A" * 256
        data = {
            'name': long_name,
            'abbreviation': 'LONG',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_unicode_characters_in_name(self):
        """Test faculty name with unicode characters."""
        data = {
            'name': 'Faculté d\'Ingénierie',
            'abbreviation': 'FI',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertEqual(faculty.name, 'Faculté d\'Ingénierie')
    
    def test_special_characters_in_name(self):
        """Test faculty name with special characters."""
        data = {
            'name': 'Faculty of Engineering & Technology',
            'abbreviation': 'ENGTECH',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        faculty = serializer.save()
        
        self.assertIn('&', faculty.name)
    
    def test_abbreviation_with_numbers_fails(self):
        """Test that abbreviation with numbers fails validation."""
        data = {
            'name': 'Test Faculty',
            'abbreviation': 'TEST123',
            'university': str(self.university.id)
        }
        
        serializer = FacultySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('abbreviation', serializer.errors)