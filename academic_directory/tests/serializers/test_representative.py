# academic_directory/tests/serializers/test_representative.py
"""
Comprehensive test suite for Representative serializers.

Test Coverage:
- RepresentativeListSerializer (lightweight listing)
- RepresentativeDetailSerializer (full details with computed fields)
- RepresentativeSerializer (main create/update serializer with validation)
- RepresentativeVerificationSerializer (bulk verification)
- Phone number normalization
- Role-specific field validation
- Computed fields (current_level, is_final_year, has_graduated, display_name)
- Submission source validation
- Edge cases
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from academic_directory.models import (
    University, Faculty, Department, Representative, ProgramDuration
)
from academic_directory.serializers import (
    RepresentativeListSerializer,
    RepresentativeDetailSerializer,
    RepresentativeSerializer,
    RepresentativeVerificationSerializer
)

User = get_user_model()


class RepresentativeListSerializerTest(TestCase):
    """Test RepresentativeListSerializer."""
    
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
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        self.rep = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = RepresentativeListSerializer(self.rep)
        data = serializer.data
        
        expected_fields = {
            'id', 'display_name', 'full_name', 'phone_number',
            'role', 'role_display', 'department_name', 'faculty_name',
            'university_name', 'current_level_display', 'verification_status',
            'verification_status_display', 'is_active', 'created_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_basic_fields(self):
        """Test serialization of basic fields."""
        serializer = RepresentativeListSerializer(self.rep)
        data = serializer.data
        
        self.assertEqual(data['full_name'], "John Doe")
        self.assertEqual(data['phone_number'], "08012345678")
        self.assertEqual(data['role'], "CLASS_REP")
        self.assertTrue(data['is_active'])
    
    def test_serialization_display_fields(self):
        """Test serialization of display fields."""
        serializer = RepresentativeListSerializer(self.rep)
        data = serializer.data
        
        self.assertEqual(data['role_display'], "Class Representative")
        self.assertEqual(data['verification_status_display'], "Unverified")
        self.assertEqual(data['department_name'], "Computer Science")
        self.assertEqual(data['faculty_name'], "Faculty of Engineering")
        self.assertEqual(data['university_name'], "University of Benin")
    
    def test_serialization_display_name_without_nickname(self):
        """Test display_name uses full_name when no nickname."""
        serializer = RepresentativeListSerializer(self.rep)
        data = serializer.data
        
        self.assertEqual(data['display_name'], "John Doe")
    
    def test_serialization_display_name_with_nickname(self):
        """Test display_name uses nickname when available."""
        self.rep.nickname = "Johnny"
        self.rep.save()
        
        serializer = RepresentativeListSerializer(self.rep)
        data = serializer.data
        
        self.assertEqual(data['display_name'], "Johnny")
    
    def test_serialization_current_level_display(self):
        """Test current_level_display field."""
        serializer = RepresentativeListSerializer(self.rep)
        data = serializer.data
        
        # 2020 entry year + 4 year program, depends on current year
        self.assertIn('L', data['current_level_display'])


class RepresentativeDetailSerializerTest(TestCase):
    """Test RepresentativeDetailSerializer."""
    
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
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123"
        )
        self.rep = Representative.objects.create(
            full_name="John Doe",
            nickname="Johnny",
            phone_number="08012345678",
            whatsapp_number="08087654321",
            email="john@example.com",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020,
            submission_source="WEBSITE",
            notes="Test representative"
        )
    
    def test_serialization_contains_all_fields(self):
        """Test that serialization includes all expected fields."""
        serializer = RepresentativeDetailSerializer(self.rep)
        data = serializer.data
        
        expected_fields = {
            'id', 'full_name', 'nickname', 'display_name',
            'phone_number', 'whatsapp_number', 'email',
            'department', 'department_detail', 'faculty_name', 'university_name',
            'role', 'role_display', 'entry_year', 'tenure_start_year',
            'current_level', 'current_level_display', 'is_final_year',
            'expected_graduation_year', 'has_graduated',
            'submission_source', 'submission_source_display', 'submission_source_other',
            'verification_status', 'verification_status_display',
            'verified_by', 'verified_by_username', 'verified_at',
            'notes', 'is_active', 'created_at', 'updated_at'
        }
        self.assertEqual(set(data.keys()), expected_fields)
    
    def test_serialization_nested_department_detail(self):
        """Test nested department detail."""
        serializer = RepresentativeDetailSerializer(self.rep)
        data = serializer.data
        
        self.assertIn('department_detail', data)
        self.assertIsInstance(data['department_detail'], dict)
        self.assertEqual(data['department_detail']['name'], "Computer Science")
    
    def test_serialization_computed_fields(self):
        """Test all computed fields are present."""
        serializer = RepresentativeDetailSerializer(self.rep)
        data = serializer.data
        
        self.assertIn('current_level', data)
        self.assertIn('current_level_display', data)
        self.assertIn('is_final_year', data)
        self.assertIn('expected_graduation_year', data)
        self.assertIn('has_graduated', data)
        self.assertIn('display_name', data)
    
    def test_serialization_verification_fields_when_verified(self):
        """Test verification fields when representative is verified."""
        self.rep.verify(self.user)
        
        serializer = RepresentativeDetailSerializer(self.rep)
        data = serializer.data
        
        self.assertEqual(data['verification_status'], 'VERIFIED')
        self.assertEqual(data['verified_by_username'], self.user.username)
        self.assertIsNotNone(data['verified_at'])


class RepresentativeSerializerDeserializationTest(TestCase):
    """Test RepresentativeSerializer deserialization and validation."""
    
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
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
    
    def test_deserialization_class_rep_with_valid_data(self):
        """Test creating CLASS_REP with all required fields."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department': str(self.department.id),
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rep = serializer.save()
        
        self.assertEqual(rep.full_name, 'John Doe')
        self.assertEqual(rep.phone_number, '08012345678')
        self.assertEqual(rep.role, 'CLASS_REP')
        self.assertEqual(rep.entry_year, 2020)
    
    def test_deserialization_dept_president_with_tenure(self):
        """Test creating DEPT_PRESIDENT with tenure_start_year."""
        data = {
            'full_name': 'Jane Smith',
            'phone_number': '08087654321',
            'department': str(self.department.id),
            'role': 'DEPT_PRESIDENT',
            'tenure_start_year': 2024
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rep = serializer.save()
        
        self.assertEqual(rep.role, 'DEPT_PRESIDENT')
        self.assertEqual(rep.tenure_start_year, 2024)
    
    def test_deserialization_faculty_president_with_tenure(self):
        """Test creating FACULTY_PRESIDENT with tenure_start_year."""
        data = {
            'full_name': 'Bob Johnson',
            'phone_number': '08098765432',
            'department': str(self.department.id),
            'role': 'FACULTY_PRESIDENT',
            'tenure_start_year': 2024
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rep = serializer.save()
        
        self.assertEqual(rep.role, 'FACULTY_PRESIDENT')
        self.assertEqual(rep.tenure_start_year, 2024)
    
    def test_class_rep_requires_entry_year(self):
        """Test that CLASS_REP requires entry_year."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department': str(self.department.id),
            'role': 'CLASS_REP'
            # Missing entry_year
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('entry_year', serializer.errors)
    
    def test_dept_president_requires_tenure_start_year(self):
        """Test that DEPT_PRESIDENT requires tenure_start_year."""
        data = {
            'full_name': 'Jane Smith',
            'phone_number': '08087654321',
            'department': str(self.department.id),
            'role': 'DEPT_PRESIDENT'
            # Missing tenure_start_year
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tenure_start_year', serializer.errors)
    
    def test_faculty_president_requires_tenure_start_year(self):
        """Test that FACULTY_PRESIDENT requires tenure_start_year."""
        data = {
            'full_name': 'Bob Johnson',
            'phone_number': '08098765432',
            'department': str(self.department.id),
            'role': 'FACULTY_PRESIDENT'
            # Missing tenure_start_year
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tenure_start_year', serializer.errors)


class PhoneNumberNormalizationTest(TestCase):
    """Test phone number normalization in RepresentativeSerializer."""
    
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
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
    
    def test_normalize_phone_with_country_code(self):
        """Test phone number with +234 country code is normalized."""
        data = {
            'full_name': 'Test User',
            'phone_number': '+2348012345678',
            'department': str(self.department.id),
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rep = serializer.save()
        
        self.assertEqual(rep.phone_number, '08012345678')
    
    def test_normalize_phone_with_spaces(self):
        """Test phone number with spaces is normalized."""
        data = {
            'full_name': 'Test User',
            'phone_number': '0801 234 5678',
            'department': str(self.department.id),
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rep = serializer.save()
        
        self.assertEqual(rep.phone_number, '08012345678')
    
    def test_normalize_phone_with_dashes(self):
        """Test phone number with dashes is normalized."""
        data = {
            'full_name': 'Test User',
            'phone_number': '0801-234-5678',
            'department': str(self.department.id),
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        rep = serializer.save()
        
        self.assertEqual(rep.phone_number, '08012345678')
    
    def test_invalid_phone_number_fails(self):
        """Test that invalid phone number fails validation."""
        data = {
            'full_name': 'Test User',
            'phone_number': '1234567890',  # Invalid Nigerian number
            'department': str(self.department.id),
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)


class RepresentativeVerificationSerializerTest(TestCase):
    """Test RepresentativeVerificationSerializer."""
    
    def test_verification_serializer_with_verify_action(self):
        """Test verification serializer with verify action."""
        data = {
            'representative_ids': [1, 2, 3],
            'action': 'verify'
        }
        
        serializer = RepresentativeVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['action'], 'verify')
    
    def test_verification_serializer_with_dispute_action(self):
        """Test verification serializer with dispute action."""
        data = {
            'representative_ids': [1, 2, 3],
            'action': 'dispute'
        }
        
        serializer = RepresentativeVerificationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['action'], 'dispute')
    
    def test_invalid_action_fails(self):
        """Test that invalid action fails validation."""
        data = {
            'representative_ids': [1, 2, 3],
            'action': 'invalid_action'
        }
        
        serializer = RepresentativeVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('action', serializer.errors)
    
    def test_empty_ids_list_fails(self):
        """Test that empty representative_ids list fails."""
        data = {
            'representative_ids': [],
            'action': 'verify'
        }
        
        serializer = RepresentativeVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('representative_ids', serializer.errors)
    
    def test_missing_ids_fails(self):
        """Test that missing representative_ids fails."""
        data = {
            'action': 'verify'
        }
        
        serializer = RepresentativeVerificationSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('representative_ids', serializer.errors)


class RepresentativeSerializerEdgeCasesTest(TestCase):
    """Test edge cases for RepresentativeSerializer."""
    
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
        ProgramDuration.objects.create(
            department=self.department,
            duration_years=4,
            program_type='BSC'
        )
    
    def test_very_long_full_name(self):
        """Test representative with maximum length name."""
        long_name = "A" * 255
        data = {
            'full_name': long_name,
            'phone_number': '08012345678',
            'department': str(self.department.id),
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        rep = serializer.save()
        
        self.assertEqual(len(rep.full_name), 255)
    
    def test_unicode_characters_in_name(self):
        """Test name with unicode characters."""
        data = {
            'full_name': 'François Müller',
            'phone_number': '08012345678',
            'department': str(self.department.id),
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = RepresentativeSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        rep = serializer.save()
        
        self.assertEqual(rep.full_name, 'François Müller')
    
    def test_all_submission_sources_valid(self):
        """Test all valid submission source values."""
        sources = ['WEBSITE', 'WHATSAPP', 'EMAIL', 'PHONE', 'SMS', 'MANUAL', 'IMPORT', 'OTHER']
        
        for source in sources:
            data = {
                'full_name': f'User {source}',
                'phone_number': f'0801234567{sources.index(source)}',
                'department': str(self.department.id),
                'role': 'CLASS_REP',
                'entry_year': 2020,
                'submission_source': source
            }
            
            serializer = RepresentativeSerializer(data=data)
            self.assertTrue(serializer.is_valid(), f"Failed for source: {source}")