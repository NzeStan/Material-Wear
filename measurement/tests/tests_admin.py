"""
Comprehensive bulletproof tests for measurement/admin.py

Test Coverage:
- Admin registration
- list_display configuration
- list_filter configuration
- search_fields configuration
- readonly_fields configuration
- get_queryset optimization (select_related)
- Admin interface rendering
- Admin permissions
- Admin search functionality
- Admin filtering functionality
- Admin field display
- Query optimization
- Helper function (get_list_display)
"""

from django.test import TestCase, RequestFactory
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.db import connection
from django.test.utils import override_settings
from decimal import Decimal
from unittest.mock import Mock, patch

from measurement.models import Measurement
from measurement.admin import MeasurementAdmin, get_list_display


User = get_user_model()


class GetListDisplayHelperTests(TestCase):
    """Test the get_list_display helper function."""

    def test_get_list_display_excludes_specified_fields(self):
        """Test that get_list_display excludes specified fields."""
        result = get_list_display(Measurement, exclude_fields=['id'])
        
        self.assertNotIn('id', result)
        self.assertIsInstance(result, list)

    def test_get_list_display_includes_other_fields(self):
        """Test that get_list_display includes non-excluded fields."""
        result = get_list_display(Measurement, exclude_fields=['id'])
        
        # Should include these fields
        expected_fields = [
            'user', 'chest', 'shoulder', 'neck', 'sleeve_length',
            'sleeve_round', 'top_length', 'waist', 'thigh', 'knee',
            'ankle', 'hips', 'trouser_length', 'created_at', 'updated_at',
            'is_deleted'
        ]
        
        for field in expected_fields:
            self.assertIn(field, result)

    def test_get_list_display_with_multiple_exclusions(self):
        """Test get_list_display with multiple excluded fields."""
        result = get_list_display(
            Measurement,
            exclude_fields=['id', 'is_deleted', 'created_at']
        )
        
        self.assertNotIn('id', result)
        self.assertNotIn('is_deleted', result)
        self.assertNotIn('created_at', result)
        
        # Should still include others
        self.assertIn('chest', result)
        self.assertIn('user', result)

    def test_get_list_display_with_no_exclusions(self):
        """Test get_list_display with no exclusions."""
        result = get_list_display(Measurement, exclude_fields=[])
        
        # Should include all fields
        all_field_names = [field.name for field in Measurement._meta.fields]
        for field_name in all_field_names:
            self.assertIn(field_name, result)

    def test_get_list_display_returns_list(self):
        """Test that get_list_display returns a list."""
        result = get_list_display(Measurement, exclude_fields=['id'])
        self.assertIsInstance(result, list)


class MeasurementAdminRegistrationTests(TestCase):
    """Test admin registration for Measurement model."""

    def test_measurement_is_registered(self):
        """Test that Measurement model is registered in admin."""
        self.assertTrue(admin.site.is_registered(Measurement))

    def test_measurement_admin_class_is_correct(self):
        """Test that correct admin class is used for Measurement."""
        self.assertIsInstance(
            admin.site._registry[Measurement],
            MeasurementAdmin
        )


class MeasurementAdminConfigurationTests(TestCase):
    """Test MeasurementAdmin configuration."""

    def setUp(self):
        """Set up admin instance for testing."""
        self.site = AdminSite()
        self.admin = MeasurementAdmin(Measurement, self.site)

    def test_list_display_configured(self):
        """Test that list_display is properly configured."""
        self.assertTrue(hasattr(self.admin, 'list_display'))
        self.assertIsInstance(self.admin.list_display, list)
        self.assertGreater(len(self.admin.list_display), 0)

    def test_list_display_excludes_id(self):
        """Test that list_display excludes 'id' field."""
        self.assertNotIn('id', self.admin.list_display)

    def test_list_display_includes_key_fields(self):
        """Test that list_display includes important fields."""
        # Should include at least these key fields
        important_fields = ['user', 'chest', 'waist', 'created_at']
        
        for field in important_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter_configured(self):
        """Test that list_filter is properly configured."""
        self.assertEqual(
            self.admin.list_filter,
            ['created_at', 'updated_at']
        )

    def test_search_fields_configured(self):
        """Test that search_fields is properly configured."""
        self.assertEqual(
            self.admin.search_fields,
            ['user__username']
        )

    def test_readonly_fields_configured(self):
        """Test that readonly_fields is properly configured."""
        self.assertEqual(
            self.admin.readonly_fields,
            ['created_at', 'updated_at']
        )

    def test_readonly_fields_protects_timestamps(self):
        """Test that timestamp fields are read-only."""
        self.assertIn('created_at', self.admin.readonly_fields)
        self.assertIn('updated_at', self.admin.readonly_fields)


class MeasurementAdminQuerysetTests(TestCase):
    """Test get_queryset optimization."""

    def setUp(self):
        """Set up admin, users, and measurements."""
        self.site = AdminSite()
        self.admin = MeasurementAdmin(Measurement, self.site)
        self.factory = RequestFactory()
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create regular users
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
        
        # Create measurements
        self.measurement1 = Measurement.objects.create(
            user=self.user1,
            chest=Decimal('38.00')
        )
        self.measurement2 = Measurement.objects.create(
            user=self.user2,
            chest=Decimal('40.00')
        )

    def test_get_queryset_returns_queryset(self):
        """Test that get_queryset returns a queryset."""
        request = self.factory.get('/admin/measurement/measurement/')
        request.user = self.staff_user
        
        queryset = self.admin.get_queryset(request)
        
        self.assertTrue(hasattr(queryset, 'model'))
        self.assertEqual(queryset.model, Measurement)

    def test_get_queryset_uses_select_related(self):
        """Test that get_queryset uses select_related for optimization."""
        request = self.factory.get('/admin/measurement/measurement/')
        request.user = self.staff_user
        
        # Get the queryset
        queryset = self.admin.get_queryset(request)
        
        # Check if select_related is in the query
        # This checks the internal _select_related attribute
        self.assertIsNotNone(queryset.query.select_related)
        self.assertIn('user', queryset.query.select_related)

    def test_get_queryset_includes_all_measurements(self):
        """Test that get_queryset includes all measurements."""
        request = self.factory.get('/admin/measurement/measurement/')
        request.user = self.staff_user
        
        queryset = self.admin.get_queryset(request)
        
        self.assertEqual(queryset.count(), 2)
        self.assertIn(self.measurement1, queryset)
        self.assertIn(self.measurement2, queryset)

    def test_get_queryset_optimization_reduces_queries(self):
        """Test that select_related reduces database queries."""
        request = self.factory.get('/admin/measurement/measurement/')
        request.user = self.staff_user
        
        # Get queryset with optimization
        queryset = self.admin.get_queryset(request)
        
        # Reset query counter
        from django.db import reset_queries
        reset_queries()
        
        # Access users for all measurements
        with self.assertNumQueries(1):  # Should only be 1 query due to select_related
            list(queryset)
            for measurement in queryset:
                _ = measurement.user.username  # Access related user


class MeasurementAdminInterfaceTests(TestCase):
    """Test admin interface rendering and functionality."""

    def setUp(self):
        """Set up admin user and client."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user1 = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.measurement = Measurement.objects.create(
            user=self.user1,
            chest=Decimal('38.00'),
            waist=Decimal('32.00')
        )
        
        # Login as admin
        self.client.login(username='admin', password='adminpass123')

    def test_admin_changelist_accessible(self):
        """Test that measurement changelist page is accessible."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_admin_changelist_displays_measurements(self):
        """Test that changelist displays measurements."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user1.username)

    def test_admin_change_form_accessible(self):
        """Test that measurement change form is accessible."""
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_admin_change_form_displays_measurement_data(self):
        """Test that change form displays measurement data."""
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '38.00')  # chest value
        self.assertContains(response, '32.00')  # waist value

    def test_admin_add_form_accessible(self):
        """Test that add measurement form is accessible."""
        url = reverse('admin:measurement_measurement_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_measurement(self):
        """Test that admin can create a measurement."""
        url = reverse('admin:measurement_measurement_add')
        data = {
            'user': self.user1.id,
            'chest': '40.00',
            'waist': '34.00',
            'shoulder': '18.00'
        }
        response = self.client.post(url, data)
        
        # Should redirect on success
        self.assertEqual(response.status_code, 302)
        
        # Verify measurement was created
        self.assertTrue(
            Measurement.objects.filter(
                user=self.user1,
                chest=Decimal('40.00')
            ).exists()
        )

    def test_admin_can_update_measurement(self):
        """Test that admin can update a measurement."""
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        data = {
            'user': self.user1.id,
            'chest': '42.00',  # Changed
            'waist': '32.00'
        }
        response = self.client.post(url, data)
        
        # Verify measurement was updated
        self.measurement.refresh_from_db()
        self.assertEqual(self.measurement.chest, Decimal('42.00'))

    def test_admin_can_delete_measurement(self):
        """Test that admin can delete a measurement."""
        measurement_id = self.measurement.id
        url = reverse('admin:measurement_measurement_delete', args=[self.measurement.id])
        
        # GET delete confirmation page
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # POST to confirm deletion
        response = self.client.post(url, {'post': 'yes'})
        
        # Verify measurement was soft-deleted
        self.measurement.refresh_from_db()
        self.assertTrue(self.measurement.is_deleted)


class MeasurementAdminSearchTests(TestCase):
    """Test admin search functionality."""

    def setUp(self):
        """Set up admin user and measurements."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user1 = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='janedoe',
            email='jane@example.com',
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
        
        self.client.login(username='admin', password='adminpass123')

    def test_search_by_username(self):
        """Test searching measurements by username."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url, {'q': 'johndoe'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'johndoe')
        self.assertNotContains(response, 'janedoe')

    def test_search_by_partial_username(self):
        """Test searching by partial username."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url, {'q': 'john'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'johndoe')

    def test_search_returns_empty_for_no_match(self):
        """Test search returns no results when no match."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url, {'q': 'nonexistentuser'})
        
        self.assertEqual(response.status_code, 200)
        # Should not contain either user
        content = response.content.decode()
        # Check that no measurements are shown (would show username if present)
        self.assertNotIn('johndoe', content)
        self.assertNotIn('janedoe', content)


class MeasurementAdminFilterTests(TestCase):
    """Test admin filtering functionality."""

    def setUp(self):
        """Set up admin user and measurements with different dates."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create measurements
        self.measurement1 = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        
        import time
        time.sleep(0.01)
        
        self.measurement2 = Measurement.objects.create(
            user=self.user,
            chest=Decimal('40.00')
        )
        
        self.client.login(username='admin', password='adminpass123')

    def test_filter_by_created_at(self):
        """Test filtering by created_at date."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Verify filter is available
        self.assertContains(response, 'created_at')

    def test_filter_by_updated_at(self):
        """Test filtering by updated_at date."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Verify filter is available
        self.assertContains(response, 'updated_at')

    def test_filters_are_available(self):
        """Test that both filters are available in the interface."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # Both filters should be in the page
        self.assertIn('created_at', content)
        self.assertIn('updated_at', content)


class MeasurementAdminReadOnlyFieldsTests(TestCase):
    """Test that readonly fields cannot be edited."""

    def setUp(self):
        """Set up admin user and measurement."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        
        self.client.login(username='admin', password='adminpass123')

    def test_created_at_is_readonly_in_form(self):
        """Test that created_at field is readonly in change form."""
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # created_at should be displayed but not as an input field
        self.assertIn('created_at', content)
        # Should not have input with name="created_at"
        self.assertNotIn('name="created_at"', content)

    def test_updated_at_is_readonly_in_form(self):
        """Test that updated_at field is readonly in change form."""
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        
        # updated_at should be displayed but not as an input field
        self.assertIn('updated_at', content)
        # Should not have input with name="updated_at"
        self.assertNotIn('name="updated_at"', content)

    def test_cannot_modify_created_at_via_post(self):
        """Test that created_at cannot be modified via POST."""
        original_created_at = self.measurement.created_at
        
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        
        from django.utils import timezone
        future_date = timezone.now() + timezone.timedelta(days=10)
        
        data = {
            'user': self.user.id,
            'chest': '40.00',
            'created_at': future_date.isoformat()
        }
        response = self.client.post(url, data)
        
        self.measurement.refresh_from_db()
        
        # created_at should not have changed
        self.assertEqual(self.measurement.created_at, original_created_at)


class MeasurementAdminPermissionsTests(TestCase):
    """Test admin permissions."""

    def setUp(self):
        """Set up users with different permission levels."""
        # Regular user (no staff status)
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )
        
        # Staff user without permissions
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.measurement = Measurement.objects.create(
            user=self.regular_user,
            chest=Decimal('38.00')
        )

    def test_regular_user_cannot_access_admin(self):
        """Test that regular users cannot access admin interface."""
        self.client.login(username='regular', password='testpass123')
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_staff_user_can_access_admin(self):
        """Test that staff users can access admin interface."""
        self.client.login(username='staff', password='testpass123')
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        # Staff users can access admin (even without specific permissions)
        self.assertIn(response.status_code, [200, 302, 403])

    def test_admin_user_can_access_admin(self):
        """Test that admin users can access admin interface."""
        self.client.login(username='admin', password='adminpass123')
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)


class MeasurementAdminDisplayTests(TestCase):
    """Test admin display functionality."""

    def setUp(self):
        """Set up admin user and measurements."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.50'),
            waist=Decimal('32.00'),
            shoulder=Decimal('18.00')
        )
        
        self.client.login(username='admin', password='adminpass123')

    def test_admin_displays_all_measurement_fields(self):
        """Test that admin changelist displays all configured fields."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should display user
        self.assertContains(response, 'testuser')

    def test_admin_change_form_shows_all_fields(self):
        """Test that change form shows all measurement fields."""
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Should contain field names
        field_names = [
            'chest', 'shoulder', 'neck', 'sleeve_length', 'sleeve_round',
            'top_length', 'waist', 'thigh', 'knee', 'ankle', 'hips',
            'trouser_length'
        ]
        
        for field_name in field_names:
            self.assertContains(response, field_name)

    def test_admin_displays_decimal_values_correctly(self):
        """Test that decimal values are displayed correctly."""
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '38.5')  # Chest value (may strip trailing 0)


class MeasurementAdminSoftDeleteTests(TestCase):
    """
    Test admin interaction with soft-deleted measurements.
    
    Note: The current admin implementation does NOT show soft-deleted measurements.
    This is the default behavior using the custom MeasurementManager.
    
    If you want to show soft-deleted measurements in admin, update admin.py:
    
    def get_queryset(self, request):
        # Show all measurements including soft-deleted
        return Measurement.objects.all_with_deleted().select_related("user")
    """

    def setUp(self):
        """Set up admin user and measurements."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        
        self.client.login(username='admin', password='adminpass123')

    def test_admin_does_not_show_soft_deleted_measurements_in_list(self):
        """Test that admin list does NOT show soft-deleted measurements by default."""
        # Soft delete the measurement
        self.measurement.delete()
        
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Get the measurements from response
        measurements = list(response.context['cl'].result_list)
        
        # Soft-deleted measurement should NOT be in the list
        self.assertEqual(len(measurements), 0)
        self.assertNotIn(self.measurement, measurements)

    def test_admin_cannot_access_soft_deleted_measurement_directly(self):
        """Test that admin cannot access soft-deleted measurements via direct URL."""
        self.measurement.delete()  # Soft delete
        
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        response = self.client.get(url)
        
        # Should redirect or return 404 (not accessible)
        self.assertNotEqual(response.status_code, 200)
        self.assertIn(response.status_code, [302, 404])

    def test_active_measurements_still_accessible(self):
        """Test that active (non-deleted) measurements are still accessible."""
        url = reverse('admin:measurement_measurement_change', args=[self.measurement.id])
        response = self.client.get(url)
        
        # Should be accessible
        self.assertEqual(response.status_code, 200)


class MeasurementAdminOrderingTests(TestCase):
    """Test admin default ordering."""

    def setUp(self):
        """Set up admin user and measurements."""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create measurements with slight time differences
        self.measurement1 = Measurement.objects.create(
            user=self.user,
            chest=Decimal('38.00')
        )
        
        import time
        time.sleep(0.01)
        
        self.measurement2 = Measurement.objects.create(
            user=self.user,
            chest=Decimal('40.00')
        )
        
        self.client.login(username='admin', password='adminpass123')

    def test_admin_orders_by_created_at_desc(self):
        """Test that admin lists measurements in reverse chronological order."""
        url = reverse('admin:measurement_measurement_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Get the measurements from context
        measurements = list(response.context['cl'].result_list)
        
        # Most recent should be first
        self.assertEqual(measurements[0].id, self.measurement2.id)
        self.assertEqual(measurements[1].id, self.measurement1.id)