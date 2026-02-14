# academic_directory/tests/views/test_faculty.py
"""
Comprehensive test suite for FacultyViewSet.

Test Coverage:
- List faculties (admin only)
- Retrieve faculty (admin only)
- Create/Update/Delete faculty (admin only)
- Choices endpoint (public) with university filtering
- Permissions
- Query filtering by university
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from academic_directory.models import University, Faculty

User = get_user_model()


class FacultyViewSetListTest(TestCase):
    """Test listing faculties."""
    
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
        self.faculty1 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG"
        )
        self.faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        self.url = '/api/v1/academic-directory/faculties/'
    
    def test_list_faculties_as_admin(self):
        """Test that admin can list faculties."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_faculties_unauthenticated(self):
        """Test that unauthenticated users cannot list faculties."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_faculties_filtered_by_university(self):
        """Test filtering faculties by university."""
        university2 = University.objects.create(
            name="University of Lagos",
            abbreviation="UNILAG",
            state="LAGOS",
            type="FEDERAL"
        )
        Faculty.objects.create(
            university=university2,
            name="Faculty of Law",
            abbreviation="LAW"
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'university': str(self.university.id)})
        
        self.assertEqual(len(response.data['results']), 2)
        for faculty in response.data['results']:
            self.assertEqual(faculty['university'], str(self.university.id))
    
    def test_list_only_active_faculties(self):
        """Test that only active faculties are returned."""
        Faculty.objects.create(
            university=self.university,
            name="Inactive Faculty",
            abbreviation="INACT",
            is_active=False
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.data['results']), 2)


class FacultyViewSetCreateTest(TestCase):
    """Test creating faculties."""
    
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
        self.url = '/api/v1/academic-directory/faculties/'
    
    def test_create_faculty_as_admin(self):
        """Test that admin can create a faculty."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Faculty of Engineering',
            'abbreviation': 'ENG',
            'university': str(self.university.id)
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Faculty.objects.count(), 1)
    
    def test_create_faculty_duplicate_name_in_same_university_fails(self):
        """Test that duplicate faculty name in same university fails."""
        Faculty.objects.create(
            university=self.university,
            name="Faculty of Engineering",
            abbreviation="ENG1"
        )
        
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Faculty of Engineering',
            'abbreviation': 'ENG2',
            'university': str(self.university.id)
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FacultyChoicesEndpointTest(TestCase):
    """Test the public choices endpoint."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
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
        self.url = '/api/v1/academic-directory/faculties/choices/'
    
    def test_choices_endpoint_is_public(self):
        """Test that choices endpoint is accessible without authentication."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_choices_filtered_by_university(self):
        """Test filtering choices by university."""
        response = self.client.get(self.url, {'university': str(self.university1.id)})
        
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['abbreviation'], 'ENG')
    
    def test_choices_returns_university_info(self):
        """Test that choices include university information."""
        response = self.client.get(self.url)
        
        first_result = response.data[0]
        self.assertIn('university_id', first_result)
        self.assertIn('university_abbreviation', first_result)
    
    def test_choices_only_active_faculties(self):
        """Test that choices only include active faculties."""
        Faculty.objects.create(
            university=self.university1,
            name="Inactive Faculty",
            abbreviation="INACT",
            is_active=False
        )
        
        response = self.client.get(self.url)
        
        abbreviations = [f['abbreviation'] for f in response.data]
        self.assertNotIn('INACT', abbreviations)