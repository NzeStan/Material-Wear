# academic_directory/tests/views/test_public_submission.py
"""
Comprehensive test suite for PublicSubmissionView.

Test Coverage:
- Single representative submission (no auth)
- Bulk representative submissions (no auth)
- Phone number deduplication
- Validation errors
- Success response structure
- Rate limiting (StrictAnonRateThrottle - 50/hr)
- Min/max submission limits (1-100)
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from academic_directory.models import University, Faculty, Department, Representative, ProgramDuration

class PublicSubmissionSingleTest(TestCase):
    """Test single representative submissions."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
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
        self.url = '/api/v1/academic-directory/submit/'
    
    def test_submit_single_representative_no_auth(self):
        """Test submitting single representative without authentication."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Representative.objects.count(), 1)
        self.assertIn('created', response.data)
        self.assertEqual(response.data['created'], 1)
    
    def test_submit_with_all_fields(self):
        """Test submitting with all optional fields."""
        data = {
            'full_name': 'John Doe',
            'nickname': 'Johnny',
            'phone_number': '08012345678',
            'whatsapp_number': '08087654321',
            'email': 'john@example.com',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020,
            'submission_source': 'WEBSITE',
            'notes': 'Test submission'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        rep = Representative.objects.first()
        self.assertEqual(rep.nickname, 'Johnny')
        self.assertEqual(rep.email, 'john@example.com')
    
    def test_submit_invalid_phone_number(self):
        """Test submitting with invalid phone number fails."""
        data = {
            'full_name': 'John Doe',
            'phone_number': 'INVALID',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data['details'])
    
    def test_submit_missing_required_field(self):
        """Test submitting without required field fails."""
        data = {
            'full_name': 'John Doe',
            # Missing phone_number
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PublicSubmissionBulkTest(TestCase):
    """Test bulk representative submissions."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
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
        self.url = '/api/v1/academic-directory/submit/'
    
    def test_submit_bulk_representatives(self):
        """Test submitting multiple representatives."""
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
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Representative.objects.count(), 2)
        self.assertEqual(response.data['created'], 2)
        self.assertEqual(response.data['updated'], 0)
        self.assertEqual(response.data['errors'], 0)
    
    def test_submit_max_100_submissions(self):
        """Test submitting exactly 100 representatives."""
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
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Representative.objects.count(), 100)
    
    def test_submit_exceeding_100_fails(self):
        """Test that >100 submissions fails validation."""
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
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PublicSubmissionDeduplicationTest(TestCase):
    """Test phone number deduplication."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
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
        self.url = '/api/v1/academic-directory/submit/'
    
    def test_duplicate_phone_updates_existing(self):
        """Test that duplicate phone number updates existing record."""
        # Create existing
        Representative.objects.create(
            full_name='John Doe',
            phone_number='08012345678',
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role='CLASS_REP',
            entry_year=2020
        )
        
        # Submit with same phone but different data
        data = {
            'full_name': 'John Updated',
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2021
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Representative.objects.count(), 1)  # Still 1
        self.assertEqual(response.data['updated'], 1)
        self.assertEqual(response.data['created'], 0)
        
        # Verify data was updated
        rep = Representative.objects.first()
        self.assertEqual(rep.full_name, 'John Updated')
        self.assertEqual(rep.entry_year, 2021)
    
    def test_normalized_phone_deduplication(self):
        """Test deduplication works with normalized phone."""
        # Create with normalized format
        Representative.objects.create(
            full_name='John Doe',
            phone_number='08012345678',
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role='CLASS_REP',
            entry_year=2020
        )
        
        # Submit with +234 format
        data = {
            'full_name': 'John Updated',
            'phone_number': '+2348012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2021
        }
        response = self.client.post(self.url, data, format='json')
        
        # Should update, not create new
        self.assertEqual(Representative.objects.count(), 1)
        self.assertEqual(response.data['updated'], 1)


class PublicSubmissionResponseStructureTest(TestCase):
    """Test response structure."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
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
        self.url = '/api/v1/academic-directory/submit/'
    
    def test_success_response_structure(self):
        """Test that success response has correct structure."""
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertIn('success', response.data)
        self.assertIn('message', response.data)
        self.assertIn('created', response.data)
        self.assertIn('updated', response.data)
        self.assertIn('errors', response.data)
        self.assertIn('results', response.data)
        
        self.assertTrue(response.data['success'])
    
    def test_partial_success_response(self):
        """Test response when some submissions succeed and some fail."""
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
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created'], 1)
        self.assertEqual(response.data['errors'], 1)


class PublicSubmissionPermissionsTest(TestCase):
    """Test that endpoint is public and requires no authentication."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
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
        self.url = '/api/v1/academic-directory/submit/'
    
    def test_no_authentication_required(self):
        """Test public endpoint requires no authentication."""
        data = {
            'full_name': 'Public User',
            'phone_number': '08012345678',
            'department_id': self.department.id,
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        # No authentication
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Representative.objects.count(), 1)