# academic_directory/tests/serializers/test_bulk_submission.py
"""
Comprehensive test suite for Bulk Submission serializers.

Test Coverage:
- SingleSubmissionSerializer validation
- BulkSubmissionSerializer (1-100 submissions)
- Min/max limits enforcement
- create() method and results structure
- Phone number normalization in bulk
- Role-specific validation in bulk
- Error handling for individual submissions
"""

from django.test import TestCase
from academic_directory.models import University, Faculty, Department, Representative, ProgramDuration
from academic_directory.serializers import SingleSubmissionSerializer, BulkSubmissionSerializer


class SingleSubmissionSerializerTest(TestCase):
    """Test SingleSubmissionSerializer."""
    
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
    
    def test_serializer_with_all_fields(self):
        """Test SingleSubmissionSerializer with all fields."""
        data = {
            'full_name': 'John Doe',
            'nickname': 'Johnny',
            'phone_number': '08012345678',
            'whatsapp_number': '08098765432',
            'email': 'john@example.com',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020,
            'submission_source': 'WEBSITE',
            'notes': 'Test submission'
        }
        
        serializer = SingleSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
    
    def test_serializer_with_minimal_fields(self):
        """Test SingleSubmissionSerializer with only required fields."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = SingleSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
    
    def test_missing_full_name_fails(self):
        """Test that missing full_name fails validation."""
        data = {
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = SingleSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('full_name', serializer.errors)
    
    def test_missing_phone_number_fails(self):
        """Test that missing phone_number fails validation."""
        data = {
            'full_name': 'John Doe',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = SingleSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)
    
    def test_missing_department_id_fails(self):
        """Test that missing department_id fails validation."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        
        serializer = SingleSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('department_id', serializer.errors)
    
    def test_missing_role_fails(self):
        """Test that missing role fails validation."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'entry_year': 2020
        }
        
        serializer = SingleSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('role', serializer.errors)


class BulkSubmissionSerializerValidationTest(TestCase):
    """Test BulkSubmissionSerializer validation."""
    
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
    
    def test_single_submission(self):
        """Test bulk serializer with single submission."""
        data = {
            'submissions': [{
                'full_name': 'John Doe',
                'phone_number': '08012345678',
                'department_id': self.department.id,
                'role': 'CLASS_REP',
                'entry_year': 2020
            }]
        }
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
    
    def test_multiple_submissions(self):
        """Test bulk serializer with multiple submissions."""
        data = {
            'submissions': [
                {
                    'full_name': 'John Doe',
                    'phone_number': '08012345678',
                    'department_id': self.department.id,
                    'role': 'CLASS_REP',
                    'entry_year': 2020
                },
                {
                    'full_name': 'Jane Smith',
                    'phone_number': '08087654321',
                    'department_id': self.department.id,
                    'role': 'CLASS_REP',
                    'entry_year': 2021
                }
            ]
        }
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
    
    def test_empty_submissions_list_fails(self):
        """Test that empty submissions list fails validation."""
        data = {'submissions': []}
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('submissions', serializer.errors)
    
    def test_missing_submissions_field_fails(self):
        """Test that missing submissions field fails validation."""
        data = {}
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('submissions', serializer.errors)


class BulkSubmissionLimitsTest(TestCase):
    """Test min/max limits for bulk submissions."""
    
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
    
    def test_max_100_submissions_allowed(self):
        """Test that exactly 100 submissions is valid."""
        submissions = [
            {
                'full_name': f'User {i}',
                'phone_number': f'0801234{i:04d}',
                'department_id': self.department.id,
                'role': 'CLASS_REP',
                'entry_year': 2020
            }
            for i in range(100)
        ]
        data = {'submissions': submissions}
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
    
    def test_exceeding_100_submissions_fails(self):
        """Test that > 100 submissions fails validation."""
        submissions = [
            {
                'full_name': f'User {i}',
                'phone_number': f'0801234{i:04d}',
                'department_id': self.department.id,
                'role': 'CLASS_REP',
                'entry_year': 2020
            }
            for i in range(101)
        ]
        data = {'submissions': submissions}
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('submissions', serializer.errors)
    
    def test_min_1_submission_required(self):
        """Test that at least 1 submission is required."""
        data = {'submissions': []}
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertFalse(serializer.is_valid())


class BulkSubmissionCreateMethodTest(TestCase):
    """Test create() method of BulkSubmissionSerializer."""
    
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
    
    def test_create_returns_proper_structure(self):
        """Test that create() returns created/updated/errors dict."""
        data = {
            'submissions': [{
                'full_name': 'John Doe',
                'phone_number': '08012345678',
                'department_id': self.department.id,
                'role': 'CLASS_REP',
                'entry_year': 2020
            }]
        }
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        results = serializer.save()
        
        self.assertIn('created', results)
        self.assertIn('updated', results)
        self.assertIn('errors', results)
        self.assertIsInstance(results['created'], list)
        self.assertIsInstance(results['updated'], list)
        self.assertIsInstance(results['errors'], list)
    
    def test_create_new_representative(self):
        """Test creating new representative via bulk submission."""
        data = {
            'submissions': [{
                'full_name': 'John Doe',
                'phone_number': '08012345678',
                'department_id': self.department.id,
                'role': 'CLASS_REP',
                'entry_year': 2020
            }]
        }
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        results = serializer.save()
        
        self.assertEqual(len(results['created']), 1)
        self.assertEqual(len(results['updated']), 0)
        self.assertEqual(len(results['errors']), 0)
    
    def test_create_multiple_representatives(self):
        """Test creating multiple representatives."""
        data = {
            'submissions': [
                {
                    'full_name': 'John Doe',
                    'phone_number': '08012345678',
                    'department_id': self.department.id,
                    'role': 'CLASS_REP',
                    'entry_year': 2020
                },
                {
                    'full_name': 'Jane Smith',
                    'phone_number': '08087654321',
                    'department_id': self.department.id,
                    'role': 'CLASS_REP',
                    'entry_year': 2021
                }
            ]
        }
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        results = serializer.save()
        
        self.assertEqual(len(results['created']), 2)
        self.assertEqual(Representative.objects.count(), 2)


class BulkSubmissionErrorHandlingTest(TestCase):
    """Test error handling in bulk submissions."""
    
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
    
    def test_partial_success_with_some_errors(self):
        """Test that valid submissions succeed even when some fail."""
        data = {
            'submissions': [
                {
                    'full_name': 'Valid User',
                    'phone_number': '08012345678',
                    'department_id': self.department.id,
                    'role': 'CLASS_REP',
                    'entry_year': 2020
                },
                {
                    'full_name': 'Invalid User',
                    'phone_number': 'INVALID',
                    'department_id': self.department.id,
                    'role': 'CLASS_REP',
                    'entry_year': 2020
                }
            ]
        }
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        results = serializer.save()
        
        # First should succeed, second should error
        self.assertEqual(len(results['created']) + len(results['updated']), 1)
        self.assertEqual(len(results['errors']), 1)
    
    def test_error_includes_phone_number(self):
        """Test that errors include phone_number for identification."""
        data = {
            'submissions': [{
                'full_name': 'Test User',
                'phone_number': 'INVALID',
                'department_id': self.department.id,
                'role': 'CLASS_REP',
                'entry_year': 2020
            }]
        }
        
        serializer = BulkSubmissionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        results = serializer.save()
        
        self.assertEqual(len(results['errors']), 1)
        self.assertIn('phone_number', results['errors'][0])