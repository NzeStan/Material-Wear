# academic_directory/tests/serializers/test_program_duration.py
"""
Comprehensive test suite for ProgramDuration serializer.

Test Coverage:
- ProgramDurationSerializer serialization
- Deserialization with validation
- Duration validation (4-7 years)
- Program type choices validation
- Nested department detail
- One-to-one relationship with Department
- Field validation
- Edge cases
"""

from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError
from academic_directory.models import University, Faculty, Department, ProgramDuration
from academic_directory.serializers import ProgramDurationSerializer


class ProgramDurationSerializerSerializationTest(TestCase):
    """Test ProgramDurationSerializer serialization (model to JSON)."""
    
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
        self.program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = ProgramDurationSerializer(self.program)
        data = serializer.data
        
        expected_fields = {
            'id', 'department', 'department_detail', 'duration_years',
            'program_type', 'program_type_display', 'notes',
            'created_at', 'updated_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = ProgramDurationSerializer(self.program)
        data = serializer.data
        
        self.assertEqual(data['department'], str(self.department.id))
        self.assertEqual(data['duration_years'], 4)
        self.assertEqual(data['program_type'], 'BSC')
    
    def test_serialization_program_type_display(self):
        """Test serialization of program_type_display field."""
        serializer = ProgramDurationSerializer(self.program)
        data = serializer.data
        
        self.assertEqual(data['program_type_display'], 'Bachelor of Science')
    
    def test_serialization_nested_department_detail(self):
        """Test serialization of nested department detail."""
        serializer = ProgramDurationSerializer(self.program)
        data = serializer.data
        
        self.assertIn('department_detail', data)
        self.assertIsInstance(data['department_detail'], dict)
        self.assertEqual(data['department_detail']['name'], "Computer Science")
        self.assertEqual(data['department_detail']['abbreviation'], "CSC")
    
    def test_serialization_timestamps(self):
        """Test serialization of timestamp fields."""
        serializer = ProgramDurationSerializer(self.program)
        data = serializer.data
        
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        self.assertIsNotNone(data['created_at'])
        self.assertIsNotNone(data['updated_at'])
    
    def test_serialization_with_notes(self):
        """Test serialization when notes field has value."""
        self.program.notes = "Some important notes about this program"
        self.program.save()
        
        serializer = ProgramDurationSerializer(self.program)
        data = serializer.data
        
        self.assertEqual(data['notes'], "Some important notes about this program")


class ProgramDurationSerializerDeserializationTest(TestCase):
    """Test ProgramDurationSerializer deserialization (JSON to model)."""
    
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
    
    def test_deserialization_with_valid_data(self):
        """Test deserialization with all valid data."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BSC',
            'notes': 'Standard 4-year program'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertEqual(program.department, self.department)
        self.assertEqual(program.duration_years, 4)
        self.assertEqual(program.program_type, 'BSC')
        self.assertEqual(program.notes, 'Standard 4-year program')
    
    def test_deserialization_minimal_required_fields(self):
        """Test deserialization with only required fields."""
        data = {
            'department': str(self.department.id),
            'duration_years': 5,
            'program_type': 'BENG'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertIsNotNone(program.id)
        self.assertEqual(program.duration_years, 5)
    
    def test_deserialization_duration_4_years(self):
        """Test that duration of 4 years is valid."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BSC'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_deserialization_duration_7_years(self):
        """Test that duration of 7 years is valid."""
        data = {
            'department': str(self.department.id),
            'duration_years': 7,
            'program_type': 'MBBS'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_deserialization_duration_less_than_4_fails(self):
        """Test that duration < 4 fails validation."""
        data = {
            'department': str(self.department.id),
            'duration_years': 3,
            'program_type': 'BSC'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('duration_years', serializer.errors)
    
    def test_deserialization_duration_greater_than_7_fails(self):
        """Test that duration > 7 fails validation."""
        data = {
            'department': str(self.department.id),
            'duration_years': 8,
            'program_type': 'MBBS'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('duration_years', serializer.errors)
    
    def test_deserialization_missing_department_fails(self):
        """Test that missing department fails validation."""
        data = {
            'duration_years': 4,
            'program_type': 'BSC'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('department', serializer.errors)
    
    def test_deserialization_missing_duration_fails(self):
        """Test that missing duration fails validation."""
        data = {
            'department': str(self.department.id),
            'program_type': 'BSC'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('duration_years', serializer.errors)
    
    def test_deserialization_missing_program_type_fails(self):
        """Test that missing program_type fails validation."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('program_type', serializer.errors)
    
    def test_deserialization_invalid_department_id_fails(self):
        """Test that invalid department ID fails validation."""
        data = {
            'department': '99999999-9999-9999-9999-999999999999',
            'duration_years': 4,
            'program_type': 'BSC'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('department', serializer.errors)
    
    def test_deserialization_invalid_program_type_fails(self):
        """Test that invalid program_type fails validation."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'INVALID'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('program_type', serializer.errors)


class ProgramDurationSerializerProgramTypesTest(TestCase):
    """Test all valid program types."""
    
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
    
    def test_program_type_bsc(self):
        """Test BSC program type."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BSC'
        }
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        self.assertEqual(program.program_type, 'BSC')
    
    def test_program_type_beng(self):
        """Test BENG program type."""
        data = {
            'department': str(self.department.id),
            'duration_years': 5,
            'program_type': 'BENG'
        }
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        self.assertEqual(program.program_type, 'BENG')
    
    def test_program_type_btech(self):
        """Test BTECH program type."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BTECH'
        }
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_program_type_ba(self):
        """Test BA program type."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BA'
        }
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_program_type_mbbs(self):
        """Test MBBS program type (medical, 6 years)."""
        data = {
            'department': str(self.department.id),
            'duration_years': 6,
            'program_type': 'MBBS'
        }
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_program_type_llb(self):
        """Test LLB program type."""
        data = {
            'department': str(self.department.id),
            'duration_years': 5,
            'program_type': 'LLB'
        }
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class ProgramDurationSerializerUpdateTest(TestCase):
    """Test updating program duration via serializer."""
    
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
        self.program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
    
    def test_update_duration_years(self):
        """Test updating duration years."""
        data = {
            'department': str(self.department.id),
            'duration_years': 5,
            'program_type': 'BSC'
        }
        
        serializer = ProgramDurationSerializer(self.program, data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertEqual(program.duration_years, 5)
    
    def test_update_program_type(self):
        """Test updating program type."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BTECH'
        }
        
        serializer = ProgramDurationSerializer(self.program, data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertEqual(program.program_type, 'BTECH')
    
    def test_update_notes(self):
        """Test updating notes field."""
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BSC',
            'notes': 'Updated program notes'
        }
        
        serializer = ProgramDurationSerializer(self.program, data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertEqual(program.notes, 'Updated program notes')
    
    def test_partial_update(self):
        """Test partial update."""
        data = {'duration_years': 6}
        
        serializer = ProgramDurationSerializer(self.program, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertEqual(program.duration_years, 6)
        self.assertEqual(program.program_type, 'BSC')


class ProgramDurationSerializerReadOnlyFieldsTest(TestCase):
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
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BSC',
            'created_at': fake_date.isoformat()
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertNotEqual(program.created_at.date(), fake_date.date())
    
    def test_updated_at_is_read_only(self):
        """Test that updated_at cannot be set via serializer."""
        from datetime import datetime, timedelta
        
        fake_date = datetime.now() - timedelta(days=365)
        program = ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        
        data = {
            'department': str(self.department.id),
            'duration_years': 5,
            'program_type': 'BSC',
            'updated_at': fake_date.isoformat()
        }
        
        serializer = ProgramDurationSerializer(program, data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertNotEqual(program.updated_at.date(), fake_date.date())


class ProgramDurationSerializerEdgeCasesTest(TestCase):
    """Test edge cases."""
    
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
    
    def test_very_long_notes(self):
        """Test program with very long notes."""
        long_notes = "A" * 1000
        data = {
            'department': str(self.department.id),
            'duration_years': 4,
            'program_type': 'BSC',
            'notes': long_notes
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        program = serializer.save()
        
        self.assertEqual(len(program.notes), 1000)
    
    def test_duplicate_program_for_department_fails(self):
        """Test that creating duplicate program for same department fails."""
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        
        data = {
            'department': str(self.department.id),
            'duration_years': 5,
            'program_type': 'BENG'
        }
        
        serializer = ProgramDurationSerializer(data=data)
        self.assertFalse(serializer.is_valid())