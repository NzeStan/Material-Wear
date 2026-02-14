# academic_directory/tests/views/test_university.py
"""
Comprehensive test suite for UniversityViewSet.

Test Coverage:
- List universities (admin only)
- Retrieve university (admin only)
- Create university (admin only)
- Update university (admin only)
- Delete university (admin only)
- Choices endpoint (public)
- Permissions (authenticated admin vs unauthenticated)
- Serializer selection (list vs detail)
- Filtering by is_active
- Ordering
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from academic_directory.models import University

User = get_user_model()


class UniversityViewSetListTest(TestCase):
    """Test listing universities."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="testpass123"
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
        self.url = '/api/v1/academic-directory/universities/'
    
    def test_list_universities_as_admin(self):
        """Test that admin can list universities."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_universities_unauthenticated(self):
        """Test that unauthenticated users cannot list universities."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_universities_as_regular_user(self):
        """Test that regular users cannot list universities."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_uses_list_serializer(self):
        """Test that list action uses UniversityListSerializer."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        # Check for list serializer fields
        first_result = response.data['results'][0]
        self.assertIn('faculties_count', first_result)
        self.assertIn('departments_count', first_result)
        self.assertIn('representatives_count', first_result)
    
    def test_list_only_active_universities(self):
        """Test that only active universities are returned."""
        # Create inactive university
        University.objects.create(
            name="Inactive University",
            abbreviation="INACT",
            state="LAGOS",
            type="FEDERAL",
            is_active=False
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        # Should still be 2 (the 2 active ones)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_list_ordered_by_name(self):
        """Test that universities are ordered by name."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        names = [u['name'] for u in response.data['results']]
        self.assertEqual(names, sorted(names))


class UniversityViewSetRetrieveTest(TestCase):
    """Test retrieving a single university."""
    
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
        self.url = f'/api/v1/academic-directory/universities/{self.university.id}/'
    
    def test_retrieve_university_as_admin(self):
        """Test that admin can retrieve a university."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "University of Benin")
    
    def test_retrieve_uses_detail_serializer(self):
        """Test that retrieve action uses UniversitySerializer."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        # Check for detail serializer fields
        self.assertIn('state_display', response.data)
        self.assertIn('type_display', response.data)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
    
    def test_retrieve_nonexistent_university(self):
        """Test retrieving nonexistent university returns 404."""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/academic-directory/universities/99999999-9999-9999-9999-999999999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class UniversityViewSetCreateTest(TestCase):
    """Test creating universities."""
    
    def setUp(self):
        """Create test data."""
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            is_staff=True
        )
        self.url = '/api/v1/academic-directory/universities/'
    
    def test_create_university_as_admin(self):
        """Test that admin can create a university."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'University of Ibadan',
            'abbreviation': 'UI',
            'state': 'OYO',
            'type': 'FEDERAL'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(University.objects.count(), 1)
        self.assertEqual(response.data['name'], 'University of Ibadan')
    
    def test_create_university_unauthenticated(self):
        """Test that unauthenticated users cannot create universities."""
        data = {
            'name': 'University of Ibadan',
            'abbreviation': 'UI',
            'state': 'OYO',
            'type': 'FEDERAL'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(University.objects.count(), 0)
    
    def test_create_university_with_invalid_data(self):
        """Test creating university with invalid data fails."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': '',  # Invalid: empty name
            'abbreviation': 'UI',
            'state': 'OYO',
            'type': 'FEDERAL'
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)


class UniversityViewSetUpdateTest(TestCase):
    """Test updating universities."""
    
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
        self.url = f'/api/v1/academic-directory/universities/{self.university.id}/'
    
    def test_update_university_as_admin(self):
        """Test that admin can update a university."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Updated University Name',
            'abbreviation': 'UNIBEN',
            'state': 'EDO',
            'type': 'FEDERAL'
        }
        response = self.client.put(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.university.refresh_from_db()
        self.assertEqual(self.university.name, 'Updated University Name')
    
    def test_partial_update_university(self):
        """Test partial update of university."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Partially Updated Name'}
        response = self.client.patch(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.university.refresh_from_db()
        self.assertEqual(self.university.name, 'Partially Updated Name')
        self.assertEqual(self.university.abbreviation, 'UNIBEN')


class UniversityViewSetDeleteTest(TestCase):
    """Test deleting universities."""
    
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
        self.url = f'/api/v1/academic-directory/universities/{self.university.id}/'
    
    def test_delete_university_as_admin(self):
        """Test that admin can delete a university."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(University.objects.count(), 0)


class UniversityChoicesEndpointTest(TestCase):
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
        self.inactive_university = University.objects.create(
            name="Inactive University",
            abbreviation="INACT",
            state="LAGOS",
            type="FEDERAL",
            is_active=False
        )
        self.url = '/api/v1/academic-directory/universities/choices/'
    
    def test_choices_endpoint_is_public(self):
        """Test that choices endpoint is accessible without authentication."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_choices_returns_only_active_universities(self):
        """Test that choices only returns active universities."""
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.data), 2)
        abbreviations = [u['abbreviation'] for u in response.data]
        self.assertIn('UNIBEN', abbreviations)
        self.assertIn('UNILAG', abbreviations)
        self.assertNotIn('INACT', abbreviations)
    
    def test_choices_returns_minimal_data(self):
        """Test that choices returns minimal data for dropdowns."""
        response = self.client.get(self.url)
        
        first_result = response.data[0]
        expected_fields = {'id', 'name', 'abbreviation', 'state', 'type'}
        self.assertEqual(set(first_result.keys()), expected_fields)
    
    def test_choices_ordered_by_name(self):
        """Test that choices are ordered by name."""
        response = self.client.get(self.url)
        
        names = [u['name'] for u in response.data]
        self.assertEqual(names, sorted(names))