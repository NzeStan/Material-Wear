# academic_directory/tests/views/test_representative.py
"""
Comprehensive test suite for RepresentativeViewSet.

Test Coverage:
- List representatives (admin only)
- Filtering (university, faculty, department, role, verification_status, is_active)
- Searching (full_name, nickname, phone_number, email)
- Ordering (created_at, full_name, verification_status)
- Retrieve representative (admin only)
- Create/Update/Delete representative (admin only)
- Bulk verification action
- Bulk dispute action
- Single verify action
- Single dispute action
- Serializer selection (list/detail)
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from academic_directory.models import (
    University, Faculty, Department, Representative, ProgramDuration
)

User = get_user_model()


class RepresentativeViewSetListTest(TestCase):
    """Test listing representatives."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2021
        )
        self.url = '/api/v1/academic-directory/representatives/'
    
    def test_list_representatives_as_admin(self):
        """Test that admin can list representatives."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_representatives_unauthenticated(self):
        """Test that unauthenticated users cannot list representatives."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_uses_list_serializer(self):
        """Test that list uses RepresentativeListSerializer."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        first_result = response.data['results'][0]
        self.assertIn('display_name', first_result)
        self.assertIn('role_display', first_result)
        self.assertIn('current_level_display', first_result)
    
    def test_list_ordered_by_created_at_desc(self):
        """Test default ordering is reverse chronological."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        # rep2 created after rep1, so should be first
        self.assertEqual(response.data['results'][0]['full_name'], "Jane Smith")


class RepresentativeViewSetFilteringTest(TestCase):
    """Test filtering representatives."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.faculty1 = Faculty.objects.create(
            university=self.university1,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.faculty2 = Faculty.objects.create(
            university=self.university2,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        self.dept1 = Department.objects.create(
            faculty=self.faculty1,
            name="Computer Science",
            abbreviation="CSC"
        )
        self.dept2 = Department.objects.create(
            faculty=self.faculty2,
            name="Mathematics",
            abbreviation="MTH"
        )
        ProgramDuration.objects.create(
            department=self.dept1,
            duration_years=4,
            program_type='BSC'
        )
        ProgramDuration.objects.create(
            department=self.dept2,
            duration_years=4,
            program_type='BSC'
        )
        
        self.rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.dept1,
            faculty=self.faculty1,
            university=self.university1,
            role="CLASS_REP",
            entry_year=2020
        )
        self.rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.dept2,
            faculty=self.faculty2,
            university=self.university2,
            role="DEPT_PRESIDENT",
            tenure_start_year=2024
        )
        self.rep3 = Representative.objects.create(
            full_name="Bob Johnson",
            phone_number="08098765432",
            department=self.dept1,
            faculty=self.faculty1,
            university=self.university1,
            role="FACULTY_PRESIDENT",
            tenure_start_year=2024
        )
        self.url = '/api/v1/academic-directory/representatives/'
    
    def test_filter_by_university(self):
        """Test filtering by university."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'university': str(self.university1.id)})
        
        self.assertEqual(len(response.data['results']), 2)
        for rep in response.data['results']:
            self.assertEqual(rep['university_name'], "University of Benin")
    
    def test_filter_by_faculty(self):
        """Test filtering by faculty."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'faculty': str(self.faculty1.id)})
        
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_by_department(self):
        """Test filtering by department."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'department': str(self.dept1.id)})
        
        self.assertEqual(len(response.data['results']), 2)
    
    def test_filter_by_role(self):
        """Test filtering by role."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'role': 'CLASS_REP'})
        
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['role'], 'CLASS_REP')
    
    def test_filter_by_verification_status(self):
        """Test filtering by verification status."""
        self.rep1.verify(self.admin_user)
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'verification_status': 'VERIFIED'})
        
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['verification_status'], 'VERIFIED')
    
    def test_filter_by_is_active(self):
        """Test filtering by is_active status."""
        self.rep1.is_active = False
        self.rep1.save()
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'is_active': 'false'})
        
        self.assertEqual(len(response.data['results']), 1)
        self.assertFalse(response.data['results'][0]['is_active'])


class RepresentativeViewSetSearchTest(TestCase):
    """Test searching representatives."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.rep1 = Representative.objects.create(
            full_name="John Doe",
            nickname="Johnny",
            phone_number="08012345678",
            email="john@example.com",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            email="jane@example.com",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2021
        )
        self.url = '/api/v1/academic-directory/representatives/'
    
    def test_search_by_full_name(self):
        """Test searching by full name."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'search': 'John'})
        
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['full_name'], "John Doe")
    
    def test_search_by_nickname(self):
        """Test searching by nickname."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'search': 'Johnny'})
        
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['full_name'], "John Doe")
    
    def test_search_by_phone_number(self):
        """Test searching by phone number."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'search': '08012345678'})
        
        self.assertEqual(len(response.data['results']), 1)
    
    def test_search_by_email(self):
        """Test searching by email."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'search': 'john@example.com'})
        
        self.assertEqual(len(response.data['results']), 1)


class RepresentativeViewSetOrderingTest(TestCase):
    """Test ordering representatives."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.rep1 = Representative.objects.create(
            full_name="Alice Brown",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.rep2 = Representative.objects.create(
            full_name="Bob Wilson",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2021
        )
        self.url = '/api/v1/academic-directory/representatives/'
    
    def test_ordering_by_full_name_asc(self):
        """Test ordering by full_name ascending."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'ordering': 'full_name'})
        
        names = [r['full_name'] for r in response.data['results']]
        self.assertEqual(names, sorted(names))
    
    def test_ordering_by_full_name_desc(self):
        """Test ordering by full_name descending."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'ordering': '-full_name'})
        
        names = [r['full_name'] for r in response.data['results']]
        self.assertEqual(names, sorted(names, reverse=True))
    
    def test_ordering_by_created_at_desc(self):
        """Test ordering by created_at descending."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'ordering': '-created_at'})
        
        # rep2 created after rep1
        self.assertEqual(response.data['results'][0]['full_name'], "Bob Wilson")


class RepresentativeViewSetBulkActionsTest(TestCase):
    """Test bulk verification and dispute actions."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.rep1 = Representative.objects.create(
            full_name="John Doe",
            phone_number="08012345678",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2020
        )
        self.rep2 = Representative.objects.create(
            full_name="Jane Smith",
            phone_number="08087654321",
            department=self.department,
            faculty=self.faculty,
            university=self.university,
            role="CLASS_REP",
            entry_year=2021
        )
        self.url = '/api/v1/academic-directory/representatives/bulk-verify/'
    
    def test_bulk_verify_action(self):
        """Test bulk verification action."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'representative_ids': [self.rep1.id, self.rep2.id],
            'action': 'verify'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['count'], 2)
        
        # Verify status changed
        self.rep1.refresh_from_db()
        self.rep2.refresh_from_db()
        self.assertEqual(self.rep1.verification_status, 'VERIFIED')
        self.assertEqual(self.rep2.verification_status, 'VERIFIED')
    
    def test_bulk_dispute_action(self):
        """Test bulk dispute action."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'representative_ids': [self.rep1.id, self.rep2.id],
            'action': 'dispute'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify status changed
        self.rep1.refresh_from_db()
        self.rep2.refresh_from_db()
        self.assertEqual(self.rep1.verification_status, 'DISPUTED')
        self.assertEqual(self.rep2.verification_status, 'DISPUTED')
    
    def test_bulk_action_unauthenticated(self):
        """Test bulk actions require authentication."""
        data = {
            'representative_ids': [self.rep1.id],
            'action': 'verify'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_bulk_action_invalid_data(self):
        """Test bulk action with invalid data."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'representative_ids': [],
            'action': 'verify'
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RepresentativeViewSetRetrieveTest(TestCase):
    """Test retrieving a single representative."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.url = f'/api/v1/academic-directory/representatives/{self.rep.id}/'
    
    def test_retrieve_representative_as_admin(self):
        """Test that admin can retrieve a representative."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], "John Doe")
    
    def test_retrieve_uses_detail_serializer(self):
        """Test that retrieve uses RepresentativeDetailSerializer."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        # Check for detail serializer fields
        self.assertIn('department_detail', response.data)
        self.assertIn('current_level', response.data)
        self.assertIn('is_final_year', response.data)
        self.assertIn('expected_graduation_year', response.data)
        self.assertIn('has_graduated', response.data)


class RepresentativeViewSetCreateTest(TestCase):
    """Test creating representatives."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
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
        self.url = '/api/v1/academic-directory/representatives/'
    
    def test_create_representative_as_admin(self):
        """Test that admin can create a representative."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'full_name': 'John Doe',
            'phone_number': '08012345678',
            'department': str(self.department.id),
            'role': 'CLASS_REP',
            'entry_year': 2020
        }
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Representative.objects.count(), 1)