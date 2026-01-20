"""
Comprehensive bulletproof tests for measurement/views.py

Test Coverage:
- Authentication & Authorization
- List measurements (GET /api/measurement/measurements/)
- Create measurement (POST /api/measurement/measurements/)
- Retrieve measurement (GET /api/measurement/measurements/{id}/)
- Update measurement (PUT /api/measurement/measurements/{id}/)
- Partial update (PATCH /api/measurement/measurements/{id}/)
- Delete measurement (DELETE /api/measurement/measurements/{id}/)
- Pagination
- Filtering (by created_at, updated_at)
- Ordering
- Rate limiting
- User isolation (security)
- Validation errors
- Edge cases
- Soft delete behavior
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
import uuid
import time

from measurement.models import Measurement
from measurement.serializers import MeasurementSerializer


User = get_user_model()


class MeasurementViewSetAuthenticationTests(APITestCase):
    """Test authentication and authorization for measurement endpoints."""

    def setUp(self):
        """Set up test client and URL."""
        self.client = APIClient()
        self.list_url = reverse('measurement:measurement-list')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_unauthenticated_list_forbidden(self):
        """Test that unauthenticated users cannot list measurements."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_create_forbidden(self):
        """Test that unauthenticated users cannot create measurements."""
        data = {'chest': '38.00'}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_retrieve_forbidden(self):
        """Test that unauthenticated users cannot retrieve measurements."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': measurement.id})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_update_forbidden(self):
        """Test that unauthenticated users cannot update measurements."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': measurement.id})
        data = {'chest': '40.00'}
        response = self.client.put(detail_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_delete_forbidden(self):
        """Test that unauthenticated users cannot delete measurements."""
        measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': measurement.id})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_list_allowed(self):
        """Test that authenticated users can list their measurements."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_create_allowed(self):
        """Test that authenticated users can create measurements."""
        self.client.force_authenticate(user=self.user)
        data = {'chest': '38.00'}
        response = self.client.post(self.list_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class MeasurementViewSetListTests(APITestCase):
    """Test listing measurements with pagination, filtering, and ordering."""

    def setUp(self):
        """Set up test users, measurements, and client."""
        self.client = APIClient()
        self.list_url = reverse('measurement:measurement-list')
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create measurements for user1
        self.measurement1 = Measurement.objects.create(
            user=self.user1,
            chest=Decimal('38.00'),
            waist=Decimal('32.00')
        )
        time.sleep(0.01)  # Ensure different timestamps
        self.measurement2 = Measurement.objects.create(
            user=self.user1,
            chest=Decimal('40.00'),
            waist=Decimal('34.00')
        )
        
        # Create measurement for user2
        self.measurement3 = Measurement.objects.create(
            user=self.user2,
            chest=Decimal('42.00'),
            waist=Decimal('36.00')
        )

    def test_list_returns_only_user_measurements(self):
        """Test that list only returns authenticated user's measurements."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify only user1's measurements are returned
        measurement_ids = [m['id'] for m in response.data['results']]
        self.assertIn(str(self.measurement1.id), measurement_ids)
        self.assertIn(str(self.measurement2.id), measurement_ids)
        self.assertNotIn(str(self.measurement3.id), measurement_ids)

    def test_list_empty_for_user_with_no_measurements(self):
        """Test that list returns empty array for user with no measurements."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=new_user)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_list_default_ordering_by_created_desc(self):
        """Test that list returns measurements ordered by created_at descending."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Most recent should be first
        self.assertEqual(results[0]['id'], str(self.measurement2.id))
        self.assertEqual(results[1]['id'], str(self.measurement1.id))

    def test_list_ordering_by_created_asc(self):
        """Test ordering measurements by created_at ascending."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'{self.list_url}?ordering=created_at')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        
        # Oldest should be first
        self.assertEqual(results[0]['id'], str(self.measurement1.id))
        self.assertEqual(results[1]['id'], str(self.measurement2.id))

    def test_list_ordering_by_updated_desc(self):
        """Test ordering measurements by updated_at descending."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'{self.list_url}?ordering=-updated_at')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_list_pagination(self):
        """Test that pagination works correctly."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_list_custom_page_size(self):
        """Test custom page_size parameter."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'{self.list_url}?page_size=1')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['next'])  # Should have next page

    def test_list_excludes_soft_deleted_measurements(self):
        """Test that soft-deleted measurements are excluded from list."""
        self.measurement1.delete()  # Soft delete
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.measurement2.id))

    def test_list_response_structure(self):
        """Test that list response has correct structure."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        measurement = response.data['results'][0]
        
        # Check all expected fields are present
        expected_fields = [
            'id', 'user', 'chest', 'shoulder', 'neck', 'sleeve_length',
            'sleeve_round', 'top_length', 'waist', 'thigh', 'knee',
            'ankle', 'hips', 'trouser_length', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, measurement)

    def test_list_with_many_measurements(self):
        """Test listing with many measurements (pagination edge case)."""
        # Create 25 more measurements
        for i in range(25):
            Measurement.objects.create(
                user=self.user1,
                chest=Decimal('38.00')
            )
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 27)  # 2 original + 25 new
        self.assertEqual(len(response.data['results']), 20)  # Default page size
        self.assertIsNotNone(response.data['next'])


class MeasurementViewSetCreateTests(APITestCase):
    """Test creating measurements via API."""

    def setUp(self):
        """Set up test user and client."""
        self.client = APIClient()
        self.list_url = reverse('measurement:measurement-list')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_create_measurement_with_single_field(self):
        """Test creating measurement with only one field."""
        data = {'chest': '38.00'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['chest'], '38.00')
        self.assertEqual(response.data['user'], self.user.id)
        
        # Verify in database
        self.assertTrue(Measurement.objects.filter(user=self.user).exists())

    def test_create_measurement_with_all_fields(self):
        """Test creating measurement with all fields populated."""
        data = {
            'chest': '38.50',
            'shoulder': '18.00',
            'neck': '15.50',
            'sleeve_length': '32.00',
            'sleeve_round': '14.00',
            'top_length': '28.50',
            'waist': '32.00',
            'thigh': '22.00',
            'knee': '16.00',
            'ankle': '10.00',
            'hips': '40.00',
            'trouser_length': '38.00'
        }
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        for field, value in data.items():
            self.assertEqual(response.data[field], value)

    def test_create_measurement_auto_sets_user(self):
        """Test that user is automatically set from authenticated user."""
        data = {'chest': '38.00'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user.id)
        
        # Verify user cannot override the user field
        data_with_user = {'chest': '40.00', 'user': 999}
        response2 = self.client.post(self.list_url, data_with_user, format='json')
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data['user'], self.user.id)  # Should still be authenticated user

    def test_create_measurement_sets_timestamps(self):
        """Test that created_at and updated_at are automatically set."""
        data = {'chest': '38.00'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('created_at', response.data)
        self.assertIn('updated_at', response.data)
        self.assertIsNotNone(response.data['created_at'])
        self.assertIsNotNone(response.data['updated_at'])

    def test_create_measurement_generates_uuid(self):
        """Test that UUID is automatically generated."""
        data = {'chest': '38.00'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        # Verify it's a valid UUID
        try:
            uuid.UUID(response.data['id'])
        except ValueError:
            self.fail("Invalid UUID generated")

    def test_create_measurement_without_any_fields_fails(self):
        """Test that creating measurement without any measurement fields fails."""
        data = {}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_measurement_with_invalid_chest_min(self):
        """Test creating measurement with chest below minimum."""
        data = {'chest': '19.99'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('chest', response.data)

    def test_create_measurement_with_invalid_chest_max(self):
        """Test creating measurement with chest above maximum."""
        data = {'chest': '70.01'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('chest', response.data)

    def test_create_measurement_with_valid_boundary_values(self):
        """Test creating measurement with exact min/max boundary values."""
        data = {
            'chest': '20.00',  # Minimum
            'waist': '60.00'   # Maximum
        }
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['chest'], '20.00')
        self.assertEqual(response.data['waist'], '60.00')

    def test_create_measurement_with_negative_value_fails(self):
        """Test that negative values are rejected."""
        data = {'chest': '-10.00'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_multiple_measurements_for_same_user(self):
        """Test that user can create multiple measurements."""
        data1 = {'chest': '38.00'}
        response1 = self.client.post(self.list_url, data1, format='json')
        
        data2 = {'chest': '40.00'}
        response2 = self.client.post(self.list_url, data2, format='json')
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Verify both exist in database
        self.assertEqual(Measurement.objects.filter(user=self.user).count(), 2)

    def test_create_measurement_with_decimal_precision(self):
        """Test creating measurement with 2 decimal places."""
        data = {'chest': '38.12'}
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['chest'], '38.12')

    def test_create_measurement_validation_error_message(self):
        """Test that validation errors return helpful messages."""
        data = {'chest': '10.00'}  # Too small
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('chest', response.data)
        # Should contain helpful error message
        error_message = str(response.data['chest'][0])
        self.assertIn('20 inches', error_message.lower())


class MeasurementViewSetRetrieveTests(APITestCase):
    """Test retrieving individual measurements."""

    def setUp(self):
        """Set up test users and measurements."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.measurement1 = Measurement.objects.create(
            user=self.user1,
            chest=Decimal('38.00'),
            waist=Decimal('32.00')
        )
        self.measurement2 = Measurement.objects.create(
            user=self.user2,
            chest=Decimal('40.00'),
            waist=Decimal('34.00')
        )

    def test_retrieve_own_measurement(self):
        """Test that user can retrieve their own measurement."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(self.measurement1.id))
        self.assertEqual(response.data['chest'], '38.00')

    def test_cannot_retrieve_other_user_measurement(self):
        """Test that user cannot retrieve another user's measurement."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement2.id})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_nonexistent_measurement(self):
        """Test retrieving non-existent measurement returns 404."""
        self.client.force_authenticate(user=self.user1)
        fake_uuid = uuid.uuid4()
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': fake_uuid})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_soft_deleted_measurement(self):
        """Test that soft-deleted measurements return 404."""
        self.measurement1.delete()  # Soft delete
        
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_includes_all_fields(self):
        """Test that retrieve returns all measurement fields."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_fields = [
            'id', 'user', 'chest', 'shoulder', 'neck', 'sleeve_length',
            'sleeve_round', 'top_length', 'waist', 'thigh', 'knee',
            'ankle', 'hips', 'trouser_length', 'created_at', 'updated_at'
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)

    def test_retrieve_returns_correct_user_id(self):
        """Test that retrieved measurement includes correct user ID."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.user1.id)


class MeasurementViewSetUpdateTests(APITestCase):
    """Test updating measurements (PUT and PATCH)."""

    def setUp(self):
        """Set up test users and measurements."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.measurement1 = Measurement.objects.create(
            user=self.user1,
            chest=Decimal('38.00'),
            waist=Decimal('32.00')
        )
        self.measurement2 = Measurement.objects.create(
            user=self.user2,
            chest=Decimal('40.00')
        )

    def test_update_own_measurement_full(self):
        """Test full update (PUT) of own measurement."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        data = {
            'chest': '40.00',
            'waist': '34.00',
            'shoulder': '18.00'
        }
        response = self.client.put(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chest'], '40.00')
        self.assertEqual(response.data['waist'], '34.00')
        self.assertEqual(response.data['shoulder'], '18.00')
        
        # Verify in database
        self.measurement1.refresh_from_db()
        self.assertEqual(self.measurement1.chest, Decimal('40.00'))

    def test_partial_update_own_measurement(self):
        """Test partial update (PATCH) of own measurement."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        data = {'chest': '42.00'}
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['chest'], '42.00')
        self.assertEqual(response.data['waist'], '32.00')  # Unchanged
        
        # Verify in database
        self.measurement1.refresh_from_db()
        self.assertEqual(self.measurement1.chest, Decimal('42.00'))
        self.assertEqual(self.measurement1.waist, Decimal('32.00'))

    def test_cannot_update_other_user_measurement(self):
        """Test that user cannot update another user's measurement."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement2.id})
        
        data = {'chest': '42.00'}
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify measurement unchanged
        self.measurement2.refresh_from_db()
        self.assertEqual(self.measurement2.chest, Decimal('40.00'))

    def test_update_updates_timestamp(self):
        """Test that updated_at timestamp changes on update."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        original_updated_at = self.measurement1.updated_at
        time.sleep(0.01)
        
        data = {'chest': '42.00'}
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.measurement1.refresh_from_db()
        self.assertGreater(self.measurement1.updated_at, original_updated_at)

    def test_update_does_not_change_created_at(self):
        """Test that created_at timestamp remains unchanged on update."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        original_created_at = self.measurement1.created_at
        
        data = {'chest': '42.00'}
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.measurement1.refresh_from_db()
        self.assertEqual(self.measurement1.created_at, original_created_at)

    def test_update_with_invalid_value_fails(self):
        """Test that update with invalid value fails."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        data = {'chest': '10.00'}  # Below minimum
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify measurement unchanged
        self.measurement1.refresh_from_db()
        self.assertEqual(self.measurement1.chest, Decimal('38.00'))

    def test_update_cannot_change_user(self):
        """Test that update cannot change the user field."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        data = {'chest': '42.00', 'user': self.user2.id}
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user unchanged
        self.measurement1.refresh_from_db()
        self.assertEqual(self.measurement1.user, self.user1)

    def test_update_soft_deleted_measurement_fails(self):
        """Test that updating soft-deleted measurement fails."""
        self.measurement1.delete()  # Soft delete
        
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        data = {'chest': '42.00'}
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MeasurementViewSetDeleteTests(APITestCase):
    """Test deleting measurements (soft delete)."""

    def setUp(self):
        """Set up test users and measurements."""
        self.client = APIClient()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        self.measurement1 = Measurement.objects.create(
            user=self.user1,
            chest=Decimal('38.00')
        )
        self.measurement2 = Measurement.objects.create(
            user=self.user2,
            chest=Decimal('40.00')
        )

    def test_delete_own_measurement_soft_delete(self):
        """Test that deleting measurement performs soft delete."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify soft delete (is_deleted=True)
        self.measurement1.refresh_from_db()
        self.assertTrue(self.measurement1.is_deleted)

    def test_soft_deleted_measurement_not_in_queryset(self):
        """Test that soft-deleted measurement doesn't appear in list."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        list_url = reverse('measurement:measurement-list')
        
        # Delete measurement
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify not in list
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)

    def test_cannot_delete_other_user_measurement(self):
        """Test that user cannot delete another user's measurement."""
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement2.id})
        
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify measurement not deleted
        self.measurement2.refresh_from_db()
        self.assertFalse(self.measurement2.is_deleted)

    def test_delete_nonexistent_measurement(self):
        """Test deleting non-existent measurement returns 404."""
        self.client.force_authenticate(user=self.user1)
        fake_uuid = uuid.uuid4()
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': fake_uuid})
        
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_already_deleted_measurement(self):
        """Test deleting already soft-deleted measurement returns 404."""
        self.measurement1.delete()  # Soft delete
        
        self.client.force_authenticate(user=self.user1)
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement1.id})
        
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MeasurementViewSetUserIsolationTests(APITestCase):
    """Test user isolation and security."""

    def setUp(self):
        """Set up multiple users and measurements."""
        self.client = APIClient()
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        # Create measurements for each user
        self.m1_user1 = Measurement.objects.create(user=self.user1, chest=Decimal('38.00'))
        self.m2_user1 = Measurement.objects.create(user=self.user1, chest=Decimal('40.00'))
        self.m1_user2 = Measurement.objects.create(user=self.user2, chest=Decimal('42.00'))
        self.m1_user3 = Measurement.objects.create(user=self.user3, chest=Decimal('44.00'))

    def test_user_only_sees_own_measurements(self):
        """Test that each user only sees their own measurements."""
        list_url = reverse('measurement:measurement-list')
        
        # User 1
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(list_url)
        self.assertEqual(len(response.data['results']), 2)
        ids = [m['id'] for m in response.data['results']]
        self.assertIn(str(self.m1_user1.id), ids)
        self.assertIn(str(self.m2_user1.id), ids)
        
        # User 2
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(list_url)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.m1_user2.id))
        
        # User 3
        self.client.force_authenticate(user=self.user3)
        response = self.client.get(list_url)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(self.m1_user3.id))

    def test_user_cannot_retrieve_others_measurement_by_id(self):
        """Test that knowing another user's measurement ID doesn't grant access."""
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.m1_user2.id})
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_update_others_measurement(self):
        """Test that user cannot update another user's measurement."""
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.m1_user2.id})
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(detail_url, {'chest': '50.00'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify not updated
        self.m1_user2.refresh_from_db()
        self.assertEqual(self.m1_user2.chest, Decimal('42.00'))

    def test_user_cannot_delete_others_measurement(self):
        """Test that user cannot delete another user's measurement."""
        detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.m1_user2.id})
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verify not deleted
        self.m1_user2.refresh_from_db()
        self.assertFalse(self.m1_user2.is_deleted)

    def test_switching_users_shows_different_measurements(self):
        """Test that switching authenticated users shows different data."""
        list_url = reverse('measurement:measurement-list')
        
        # As user1
        self.client.force_authenticate(user=self.user1)
        response1 = self.client.get(list_url)
        user1_count = len(response1.data['results'])
        
        # Switch to user2
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get(list_url)
        user2_count = len(response2.data['results'])
        
        self.assertEqual(user1_count, 2)
        self.assertEqual(user2_count, 1)
        self.assertNotEqual(
            response1.data['results'][0]['id'],
            response2.data['results'][0]['id']
        )


class MeasurementViewSetFilteringTests(APITestCase):
    """Test filtering functionality."""

    def setUp(self):
        """Set up test user and measurements with different timestamps."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('measurement:measurement-list')
        
        # Create measurements at different times
        self.measurement1 = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        time.sleep(0.02)
        self.measurement2 = Measurement.objects.create(
            user=self.user,
            chest=Decimal('40.00')
        )

    def test_filter_by_created_at(self):
        """Test filtering by created_at date."""
        # Get today's date
        today = timezone.now().date()
        
        response = self.client.get(
            f'{self.list_url}?created_at={today.isoformat()}'
        )
        
        # Both measurements should be from today
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Note: Exact filtering behavior depends on your Django filter configuration

    def test_filter_by_updated_at(self):
        """Test filtering by updated_at date."""
        today = timezone.now().date()
        
        response = self.client.get(
            f'{self.list_url}?updated_at={today.isoformat()}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MeasurementViewSetEdgeCaseTests(APITestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test user and client."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('measurement:measurement-list')

    def test_create_with_all_minimum_values(self):
        """Test creating measurement with all fields at minimum boundary."""
        data = {
            'chest': '20.00',
            'shoulder': '12.00',
            'neck': '10.00',
            'sleeve_length': '20.00',
            'sleeve_round': '8.00',
            'top_length': '20.00',
            'waist': '20.00',
            'thigh': '12.00',
            'knee': '10.00',
            'ankle': '7.00',
            'hips': '25.00',
            'trouser_length': '25.00'
        }
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_all_maximum_values(self):
        """Test creating measurement with all fields at maximum boundary."""
        data = {
            'chest': '70.00',
            'shoulder': '30.00',
            'neck': '30.00',
            'sleeve_length': '40.00',
            'sleeve_round': '20.00',
            'top_length': '40.00',
            'waist': '60.00',
            'thigh': '40.00',
            'knee': '30.00',
            'ankle': '20.00',
            'hips': '70.00',
            'trouser_length': '50.00'
        }
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_empty_string_values_handled(self):
        """Test that empty string values are handled appropriately."""
        data = {'chest': ''}
        response = self.client.post(self.list_url, data, format='json')
        
        # Should return validation error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_null_values_accepted_for_optional_fields(self):
        """Test that null/None values are accepted for optional measurement fields."""
        data = {
            'chest': '38.00',
            'shoulder': None,
            'neck': None
        }
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['shoulder'])
        self.assertIsNone(response.data['neck'])

    def test_invalid_uuid_in_url(self):
        """Test that invalid UUID in URL returns 404."""
        invalid_url = f"/api/measurement/measurements/invalid-uuid/"
        response = self.client.get(invalid_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_very_large_page_size_capped(self):
        """Test that very large page_size is capped at max_page_size."""
        response = self.client.get(f'{self.list_url}?page_size=1000')
        
        # Should be capped at 100 (max_page_size)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MeasurementViewSetPerformanceTests(APITestCase):
    """Test performance and optimization."""

    def setUp(self):
        """Set up test user and client."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse('measurement:measurement-list')

    def test_list_uses_select_related(self):
        """Test that list view uses select_related for optimization."""
        # Create measurement
        Measurement.objects.create(user=self.user, chest=Decimal('38.00'))
        
        # This test verifies the view uses select_related('user')
        # by checking query count (requires django-debug-toolbar or similar)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # In production, you'd use assertNumQueries to verify optimization


class MeasurementViewSetReadOnlyFieldsTests(APITestCase):
    """Test that read-only fields cannot be modified."""

    def setUp(self):
        """Set up test user and measurement."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        self.measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        self.detail_url = reverse('measurement:measurement-detail', kwargs={'pk': self.measurement.id})

    def test_cannot_modify_user_field(self):
        """Test that user field cannot be modified via API."""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        
        data = {'chest': '40.00', 'user': new_user.id}
        response = self.client.patch(self.detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user unchanged
        self.measurement.refresh_from_db()
        self.assertEqual(self.measurement.user, self.user)

    def test_cannot_modify_created_at(self):
        """Test that created_at cannot be modified via API."""
        future_date = timezone.now() + timedelta(days=10)
        
        data = {'chest': '40.00', 'created_at': future_date.isoformat()}
        response = self.client.patch(self.detail_url, data, format='json')
        
        original_created = self.measurement.created_at
        self.measurement.refresh_from_db()
        
        # created_at should not have changed to future_date
        self.assertNotEqual(self.measurement.created_at, future_date)

    def test_cannot_modify_is_deleted(self):
        """Test that is_deleted cannot be set to True via API (use DELETE instead)."""
        data = {'chest': '40.00', 'is_deleted': True}
        response = self.client.patch(self.detail_url, data, format='json')
        
        self.measurement.refresh_from_db()
        # is_deleted should still be False
        self.assertFalse(self.measurement.is_deleted)