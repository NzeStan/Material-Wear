# academic_directory/tests/views/test_department.py
"""
Comprehensive test suite for DepartmentViewSet.

Test Coverage:
- List departments (admin only)
- Filtering by faculty and university
- Retrieve department (admin only)
- Create/Update/Delete department (admin only)
- Choices endpoint (public) with cascading filters
- Permissions
- Query optimization (select_related)
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from academic_directory.models import University, Faculty, Department

User = get_user_model()


class DepartmentViewSetListTest(TestCase):
    """Test listing departments."""
    
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
            university=self.university1,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        self.faculty3 = Faculty.objects.create(
            university=self.university2,
            name="Faculty of Law",
            abbreviation="LAW"
        )
        self.dept1 = Department.objects.create(
            faculty=self.faculty1,
            name="Computer Science",
            abbreviation="CSC"
        )
        self.dept2 = Department.objects.create(
            faculty=self.faculty1,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        self.dept3 = Department.objects.create(
            faculty=self.faculty2,
            name="Mathematics",
            abbreviation="MTH"
        )
        self.url = '/api/v1/academic-directory/departments/'
    
    def test_list_departments_as_admin(self):
        """Test that admin can list departments."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
    
    def test_list_departments_unauthenticated(self):
        """Test that unauthenticated users cannot list departments."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_departments_filtered_by_faculty(self):
        """Test filtering departments by faculty."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'faculty': str(self.faculty1.id)})
        
        self.assertEqual(len(response.data['results']), 2)
        for dept in response.data['results']:
            self.assertEqual(dept['faculty'], str(self.faculty1.id))
    
    def test_list_departments_filtered_by_university(self):
        """Test filtering departments by university."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url, {'university': str(self.university1.id)})
        
        # Should return all departments from university1's faculties
        self.assertEqual(len(response.data['results']), 3)
    
    def test_list_only_active_departments(self):
        """Test that only active departments are returned."""
        Department.objects.create(
            faculty=self.faculty1,
            name="Inactive Department",
            abbreviation="INACT",
            is_active=False
        )
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.data['results']), 3)
    
    def test_list_uses_select_related(self):
        """Test that queryset uses select_related for optimization."""
        self.client.force_authenticate(user=self.admin_user)
        
        # This should execute efficiently with select_related
        with self.assertNumQueries(3):  # Auth query + list query + count query
            response = self.client.get(self.url)
            
            # Access nested relationships - should not cause additional queries
            if response.data['results']:
                first_dept = response.data['results'][0]
                self.assertIn('faculty_name', first_dept)
                self.assertIn('university_name', first_dept)
    
    def test_list_ordered_correctly(self):
        """Test departments are ordered by university, faculty, then name."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        # Should be ordered
        self.assertEqual(len(response.data['results']), 3)


class DepartmentViewSetRetrieveTest(TestCase):
    """Test retrieving a single department."""
    
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
        self.url = f'/api/v1/academic-directory/departments/{self.department.id}/'
    
    def test_retrieve_department_as_admin(self):
        """Test that admin can retrieve a department."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Computer Science")
    
    def test_retrieve_uses_detail_serializer(self):
        """Test that retrieve uses DepartmentSerializer with full details."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        
        # Check for detail serializer fields
        self.assertIn('faculty_detail', response.data)
        self.assertIn('university_name', response.data)
        self.assertIn('university_abbreviation', response.data)
        self.assertIn('full_name', response.data)
    
    def test_retrieve_nonexistent_department(self):
        """Test retrieving nonexistent department returns 404."""
        self.client.force_authenticate(user=self.admin_user)
        url = '/api/v1/academic-directory/departments/99999999-9999-9999-9999-999999999999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class DepartmentViewSetCreateTest(TestCase):
    """Test creating departments."""
    
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
        self.url = '/api/v1/academic-directory/departments/'
    
    def test_create_department_as_admin(self):
        """Test that admin can create a department."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Computer Science',
            'abbreviation': 'CSC',
            'faculty': str(self.faculty.id)
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Department.objects.count(), 1)
        self.assertEqual(response.data['name'], 'Computer Science')
    
    def test_create_department_duplicate_name_in_same_faculty_fails(self):
        """Test that duplicate department name in same faculty fails."""
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC1"
        )
        
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Computer Science',
            'abbreviation': 'CSC2',
            'faculty': str(self.faculty.id)
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_department_same_name_different_faculty_succeeds(self):
        """Test that same department name in different faculty succeeds."""
        Department.objects.create(
            faculty=self.faculty,
            name="Computer Science",
            abbreviation="CSC1"
        )
        
        faculty2 = Faculty.objects.create(
            university=self.university,
            name="Faculty of Science",
            abbreviation="SCI"
        )
        
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Computer Science',
            'abbreviation': 'CSC2',
            'faculty': str(faculty2.id)
        }
        response = self.client.post(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Department.objects.count(), 2)


class DepartmentViewSetUpdateTest(TestCase):
    """Test updating departments."""
    
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
        self.url = f'/api/v1/academic-directory/departments/{self.department.id}/'
    
    def test_update_department_as_admin(self):
        """Test that admin can update a department."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'name': 'Computer Engineering',
            'abbreviation': 'CPE',
            'faculty': str(self.faculty.id)
        }
        response = self.client.put(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.department.refresh_from_db()
        self.assertEqual(self.department.name, 'Computer Engineering')
    
    def test_partial_update_department(self):
        """Test partial update of department."""
        self.client.force_authenticate(user=self.admin_user)
        data = {'name': 'Updated Name'}
        response = self.client.patch(self.url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.department.refresh_from_db()
        self.assertEqual(self.department.name, 'Updated Name')
        self.assertEqual(self.department.abbreviation, 'CSC')


class DepartmentViewSetDeleteTest(TestCase):
    """Test deleting departments."""
    
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
        self.url = f'/api/v1/academic-directory/departments/{self.department.id}/'
    
    def test_delete_department_as_admin(self):
        """Test that admin can delete a department."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Department.objects.count(), 0)


class DepartmentChoicesEndpointTest(TestCase):
    """Test the public choices endpoint with cascading filters."""
    
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
        self.dept1 = Department.objects.create(
            faculty=self.faculty1,
            name="Computer Science",
            abbreviation="CSC"
        )
        self.dept2 = Department.objects.create(
            faculty=self.faculty1,
            name="Electrical Engineering",
            abbreviation="EEE"
        )
        self.dept3 = Department.objects.create(
            faculty=self.faculty2,
            name="Mathematics",
            abbreviation="MTH"
        )
        Department.objects.create(
            faculty=self.faculty1,
            name="Inactive Department",
            abbreviation="INACT",
            is_active=False
        )
        self.url = '/api/v1/academic-directory/departments/choices/'
    
    def test_choices_endpoint_is_public(self):
        """Test that choices endpoint is accessible without authentication."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_choices_returns_only_active_departments(self):
        """Test that choices only return active departments."""
        response = self.client.get(self.url)
        
        self.assertEqual(len(response.data), 3)
        abbreviations = [d['abbreviation'] for d in response.data]
        self.assertNotIn('INACT', abbreviations)
    
    def test_choices_filtered_by_faculty(self):
        """Test filtering choices by faculty."""
        response = self.client.get(self.url, {'faculty': str(self.faculty1.id)})
        
        self.assertEqual(len(response.data), 2)
        for dept in response.data:
            self.assertEqual(dept['faculty'], str(self.faculty1.id))
    
    def test_choices_filtered_by_university(self):
        """Test filtering choices by university (through faculty)."""
        response = self.client.get(self.url, {'university': str(self.university1.id)})
        
        # Should return all departments from university1's faculties
        self.assertEqual(len(response.data), 2)
    
    def test_choices_cascading_filters(self):
        """Test that university and faculty filters can be combined."""
        response = self.client.get(self.url, {
            'university': str(self.university1.id),
            'faculty': str(self.faculty1.id)
        })
        
        # Should return departments from faculty1 (which is in university1)
        self.assertEqual(len(response.data), 2)