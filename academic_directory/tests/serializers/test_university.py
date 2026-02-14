# academic_directory/tests/serializers/test_university.py
"""
Comprehensive test suite for University serializers.

Test Coverage:
- UniversityListSerializer (lightweight listing)
- UniversitySerializer (full details)
- Serialization (model to JSON)
- Deserialization (JSON to model)
- Field validation
- Required fields
- Read-only fields (created_at, updated_at, counts)
- Computed fields (state_display, type_display, faculties_count, departments_count, representatives_count)
- Choice field validation (state, type)
- Edge cases
"""

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from academic_directory.models import University, Faculty, Department, Representative
from academic_directory.serializers import UniversitySerializer, UniversityListSerializer


class UniversityListSerializerTest(TestCase):
    """Test UniversityListSerializer."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = UniversityListSerializer(self.university)
        data = serializer.data
        
        expected_fields = {
            'id', 'name', 'abbreviation', 'state', 'type',
            'is_active', 'faculties_count', 'departments_count',
            'representatives_count'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = UniversityListSerializer(self.university)
        data = serializer.data
        
        self.assertEqual(data['name'], "University of Benin")
        self.assertEqual(data['abbreviation'], "UNIBEN")
        self.assertEqual(data['state'], "EDO")
        self.assertEqual(data['type'], "FEDERAL")
        self.assertTrue(data['is_active'])
    
    def test_serialization_count_properties(self):
        """Test serialization of count properties."""
        # Create related objects
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
            entry_year=2020
        )
        
        serializer = UniversityListSerializer(self.university)
        data = serializer.data
        
        self.assertEqual(data['faculties_count'], 1)
        self.assertEqual(data['departments_count'], 1)
        self.assertEqual(data['representatives_count'], 1)
    
    def test_serialization_zero_counts_initially(self):
        """Test that counts are 0 for new university."""
        serializer = UniversityListSerializer(self.university)
        data = serializer.data
        
        self.assertEqual(data['faculties_count'], 0)
        self.assertEqual(data['departments_count'], 0)
        self.assertEqual(data['representatives_count'], 0)
    
    def test_serialize_multiple_universities(self):
        """Test serializing multiple universities."""
        uni2 = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        
        serializer = UniversityListSerializer([self.university, uni2], many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['abbreviation'], "UNIBEN")
        self.assertEqual(data[1]['abbreviation'], "UNILAG")


class UniversitySerializerSerializationTest(TestCase):
    """Test UniversitySerializer serialization (model to JSON)."""
    
    def setUp(self):
        """Create test data."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = UniversitySerializer(self.university)
        data = serializer.data
        
        expected_fields = {
            'id', 'name', 'abbreviation', 'state', 'state_display',
            'type', 'type_display', 'is_active', 'faculties_count',
            'departments_count', 'representatives_count',
            'created_at', 'updated_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = UniversitySerializer(self.university)
        data = serializer.data
        
        self.assertEqual(data['name'], "University of Benin")
        self.assertEqual(data['abbreviation'], "UNIBEN")
        self.assertEqual(data['state'], "EDO")
        self.assertEqual(data['type'], "FEDERAL")
        self.assertTrue(data['is_active'])
    
    def test_serialization_display_fields(self):
        """Test serialization of display fields."""
        serializer = UniversitySerializer(self.university)
        data = serializer.data
        
        self.assertEqual(data['state_display'], "Edo")
        self.assertEqual(data['type_display'], "Federal University")
    
    def test_serialization_timestamps(self):
        """Test serialization of timestamp fields."""
        serializer = UniversitySerializer(self.university)
        data = serializer.data
        
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIsNotNone(data['created_at'])
        self.assertIsNotNone(data['updated_at'])
    
    def test_serialization_different_states(self):
        """Test serialization with different states."""
        states_to_test = [
            ('LAGOS', 'Lagos'),
            ('RIVERS', 'Rivers'),
            ('FCT', 'Federal Capital Territory'),
        ]
        
        for state_code, state_display in states_to_test:
            uni = University.objects.create(
                name=f"Test University {state_code}",
                abbreviation=f"TU{state_code[:3]}",
                state=state_code,
                type="FEDERAL"
            )
            
            serializer = UniversitySerializer(uni)
            data = serializer.data
            
            self.assertEqual(data['state'], state_code)
            self.assertEqual(data['state_display'], state_display)
    
    def test_serialization_different_types(self):
        """Test serialization with different university types."""
        types_to_test = [
            ('FEDERAL', 'Federal University'),
            ('STATE', 'State University'),
            ('PRIVATE', 'Private University'),
        ]
        
        for type_code, type_display in types_to_test:
            uni = University.objects.create(
                name=f"Test {type_code} University",
                abbreviation=f"T{type_code[:3]}U",
                state="LAGOS",
                type=type_code
            )
            
            serializer = UniversitySerializer(uni)
            data = serializer.data
            
            self.assertEqual(data['type'], type_code)
            self.assertEqual(data['type_display'], type_display)


class UniversitySerializerDeserializationTest(TestCase):
    """Test UniversitySerializer deserialization (JSON to model)."""
    
    def test_deserialization_with_valid_data(self):
        """Test deserialization with all valid data."""
        data = {
            'name': 'University of Lagos',
            'abbreviation': 'UNILAG',
            'state': 'LAGOS',
            'type': 'FEDERAL',
            'is_active': True
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertEqual(university.name, 'University of Lagos')
        self.assertEqual(university.abbreviation, 'UNILAG')
        self.assertEqual(university.state, 'LAGOS')
        self.assertEqual(university.type, 'FEDERAL')
        self.assertTrue(university.is_active)
    
    def test_deserialization_minimal_required_fields(self):
        """Test deserialization with only required fields."""
        data = {
            'name': 'Test University',
            'abbreviation': 'TU',
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertIsNotNone(university.id)
        self.assertTrue(university.is_active)  # Default value
    
    def test_deserialization_lowercase_abbreviation_converted(self):
        """Test that lowercase abbreviation is converted to uppercase."""
        data = {
            'name': 'Test University',
            'abbreviation': 'test',  # lowercase
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertEqual(university.abbreviation, 'TEST')
    
    def test_deserialization_missing_name_fails(self):
        """Test that missing name fails validation."""
        data = {
            'abbreviation': 'TU',
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_deserialization_missing_abbreviation_fails(self):
        """Test that missing abbreviation fails validation."""
        data = {
            'name': 'Test University',
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('abbreviation', serializer.errors)
    
    def test_deserialization_missing_state_fails(self):
        """Test that missing state fails validation."""
        data = {
            'name': 'Test University',
            'abbreviation': 'TU',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('state', serializer.errors)
    
    def test_deserialization_missing_type_fails(self):
        """Test that missing type fails validation."""
        data = {
            'name': 'Test University',
            'abbreviation': 'TU',
            'state': 'LAGOS'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)
    
    def test_deserialization_invalid_state_fails(self):
        """Test that invalid state fails validation."""
        data = {
            'name': 'Test University',
            'abbreviation': 'TU',
            'state': 'INVALID_STATE',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('state', serializer.errors)
    
    def test_deserialization_invalid_type_fails(self):
        """Test that invalid type fails validation."""
        data = {
            'name': 'Test University',
            'abbreviation': 'TU',
            'state': 'LAGOS',
            'type': 'INVALID_TYPE'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('type', serializer.errors)
    
    def test_deserialization_empty_name_fails(self):
        """Test that empty name fails validation."""
        data = {
            'name': '',
            'abbreviation': 'TU',
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_deserialization_blank_fields(self):
        """Test deserialization with blank/null optional fields."""
        data = {
            'name': 'Test University',
            'abbreviation': 'TU',
            'state': 'LAGOS',
            'type': 'FEDERAL',
            'is_active': False
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertFalse(university.is_active)


class UniversitySerializerUpdateTest(TestCase):
    """Test updating universities via serializer."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_update_name(self):
        """Test updating university name."""
        data = {
            'name': 'Updated University Name',
            'abbreviation': self.university.abbreviation,
            'state': self.university.state,
            'type': self.university.type
        }
        
        serializer = UniversitySerializer(self.university, data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertEqual(university.name, 'Updated University Name')
    
    def test_update_abbreviation(self):
        """Test updating abbreviation."""
        data = {
            'name': self.university.name,
            'abbreviation': 'NEW',
            'state': self.university.state,
            'type': self.university.type
        }
        
        serializer = UniversitySerializer(self.university, data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertEqual(university.abbreviation, 'NEW')
    
    def test_update_is_active(self):
        """Test updating is_active status."""
        data = {
            'name': self.university.name,
            'abbreviation': self.university.abbreviation,
            'state': self.university.state,
            'type': self.university.type,
            'is_active': False
        }
        
        serializer = UniversitySerializer(self.university, data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertFalse(university.is_active)
    
    def test_partial_update(self):
        """Test partial update."""
        data = {'name': 'Partially Updated Name'}
        
        serializer = UniversitySerializer(self.university, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertEqual(university.name, 'Partially Updated Name')
        self.assertEqual(university.abbreviation, 'UNIBEN')  # Unchanged


class UniversitySerializerReadOnlyFieldsTest(TestCase):
    """Test read-only fields."""
    
    def setUp(self):
        """Create test university."""
        self.university = University.objects.create(
            name="University of Benin",
            abbreviation="UNIBEN",
            state="EDO",
            type="FEDERAL"
        )
    
    def test_created_at_is_read_only(self):
        """Test that created_at cannot be set via serializer."""
        from datetime import datetime, timedelta
        
        fake_date = datetime.now() - timedelta(days=365)
        data = {
            'name': 'Test University',
            'abbreviation': 'TU',
            'state': 'LAGOS',
            'type': 'FEDERAL',
            'created_at': fake_date.isoformat()
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        # created_at should be auto-generated, not the fake date
        self.assertNotEqual(university.created_at.date(), fake_date.date())
    
    def test_updated_at_is_read_only(self):
        """Test that updated_at cannot be set via serializer."""
        from datetime import datetime, timedelta
        
        fake_date = datetime.now() - timedelta(days=365)
        data = {
            'name': self.university.name,
            'abbreviation': self.university.abbreviation,
            'state': self.university.state,
            'type': self.university.type,
            'updated_at': fake_date.isoformat()
        }
        
        serializer = UniversitySerializer(self.university, data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        # updated_at should be auto-generated
        self.assertNotEqual(university.updated_at.date(), fake_date.date())
    
    def test_count_fields_cannot_be_set(self):
        """Test that count fields are computed and cannot be set."""
        data = {
            'name': 'Test University',
            'abbreviation': 'TU',
            'state': 'LAGOS',
            'type': 'FEDERAL',
            'faculties_count': 999,
            'departments_count': 999,
            'representatives_count': 999
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        # Counts should be 0 (computed from actual data)
        self.assertEqual(university.faculties_count, 0)
        self.assertEqual(university.departments_count, 0)
        self.assertEqual(university.representatives_count, 0)


class UniversitySerializerEdgeCasesTest(TestCase):
    """Test edge cases."""
    
    def test_very_long_name(self):
        """Test university with maximum length name."""
        long_name = "A" * 255
        data = {
            'name': long_name,
            'abbreviation': 'LONG',
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertEqual(len(university.name), 255)
    
    def test_name_exceeding_max_length_fails(self):
        """Test that name exceeding max length fails."""
        long_name = "A" * 256
        data = {
            'name': long_name,
            'abbreviation': 'LONG',
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)
    
    def test_unicode_characters_in_name(self):
        """Test university name with unicode characters."""
        data = {
            'name': 'Université de Lagos',
            'abbreviation': 'UDL',
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertEqual(university.name, 'Université de Lagos')
    
    def test_special_characters_in_name(self):
        """Test university name with special characters."""
        data = {
            'name': 'University of Lagos (Main Campus)',
            'abbreviation': 'UNILAG',
            'state': 'LAGOS',
            'type': 'FEDERAL'
        }
        
        serializer = UniversitySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        university = serializer.save()
        
        self.assertIn('(Main Campus)', university.name)