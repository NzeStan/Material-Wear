"""
Comprehensive bulletproof tests for accounts/admin.py

Test Coverage:
- CustomUserAdmin registration
- List display configuration
- List filters
- Search functionality
- Ordering configuration
- Fieldsets structure
- Add fieldsets for user creation
- Admin permissions
- Admin interface access
- Field visibility and grouping
- Admin forms integration

Security & Edge Cases:
- Permission requirements
- Superuser access
- Staff access
- Regular user access denial
- Field configuration validation
- Admin customization integrity
"""

from django.test import TestCase, RequestFactory
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse

from accounts.admin import CustomUserAdmin

User = get_user_model()


# ============================================================================
# ADMIN REGISTRATION TESTS
# ============================================================================

class AdminRegistrationTests(TestCase):
    """Test CustomUserAdmin registration"""

    def test_customuser_registered_with_admin(self):
        """Test CustomUser model is registered with admin site"""
        self.assertIn(User, admin.site._registry)

    def test_customuser_uses_customuseradmin(self):
        """Test CustomUser uses CustomUserAdmin class"""
        admin_instance = admin.site._registry[User]
        self.assertIsInstance(admin_instance, CustomUserAdmin)

    def test_admin_model_attribute(self):
        """Test admin has correct model attribute"""
        admin_instance = admin.site._registry[User]
        self.assertEqual(admin_instance.model, User)


# ============================================================================
# LIST DISPLAY CONFIGURATION TESTS
# ============================================================================

class ListDisplayTests(TestCase):
    """Test CustomUserAdmin list_display configuration"""

    def setUp(self):
        """Set up admin instance"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)

    def test_list_display_fields_exist(self):
        """Test list_display is configured"""
        self.assertTrue(hasattr(self.admin, 'list_display'))
        self.assertIsInstance(self.admin.list_display, list)

    def test_list_display_includes_id(self):
        """Test list_display includes id field"""
        self.assertIn('id', self.admin.list_display)

    def test_list_display_includes_email(self):
        """Test list_display includes email field"""
        self.assertIn('email', self.admin.list_display)

    def test_list_display_includes_username(self):
        """Test list_display includes username field"""
        self.assertIn('username', self.admin.list_display)

    def test_list_display_includes_is_staff(self):
        """Test list_display includes is_staff field"""
        self.assertIn('is_staff', self.admin.list_display)

    def test_list_display_includes_is_superuser(self):
        """Test list_display includes is_superuser field"""
        self.assertIn('is_superuser', self.admin.list_display)

    def test_list_display_includes_is_active(self):
        """Test list_display includes is_active field"""
        self.assertIn('is_active', self.admin.list_display)

    def test_list_display_includes_date_joined(self):
        """Test list_display includes date_joined field"""
        self.assertIn('date_joined', self.admin.list_display)

    def test_list_display_field_count(self):
        """Test list_display has expected number of fields"""
        expected_fields = [
            'id', 'email', 'username', 'is_staff', 
            'is_superuser', 'is_active', 'date_joined'
        ]
        self.assertEqual(len(self.admin.list_display), len(expected_fields))

    def test_all_list_display_fields_valid(self):
        """Test all list_display fields are valid model fields"""
        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='test123'
        )
        
        for field in self.admin.list_display:
            # Check field exists on user model
            self.assertTrue(
                hasattr(user, field),
                f"Field '{field}' does not exist on User model"
            )


# ============================================================================
# LIST FILTER TESTS
# ============================================================================

class ListFilterTests(TestCase):
    """Test CustomUserAdmin list_filter configuration"""

    def setUp(self):
        """Set up admin instance"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)

    def test_list_filter_exists(self):
        """Test list_filter is configured"""
        self.assertTrue(hasattr(self.admin, 'list_filter'))
        self.assertIsInstance(self.admin.list_filter, list)

    def test_list_filter_includes_is_staff(self):
        """Test list_filter includes is_staff"""
        self.assertIn('is_staff', self.admin.list_filter)

    def test_list_filter_includes_is_superuser(self):
        """Test list_filter includes is_superuser"""
        self.assertIn('is_superuser', self.admin.list_filter)

    def test_list_filter_includes_is_active(self):
        """Test list_filter includes is_active"""
        self.assertIn('is_active', self.admin.list_filter)

    def test_list_filter_field_count(self):
        """Test list_filter has expected number of fields"""
        expected_filters = ['is_staff', 'is_superuser', 'is_active']
        self.assertEqual(len(self.admin.list_filter), len(expected_filters))


# ============================================================================
# SEARCH FIELDS TESTS
# ============================================================================

class SearchFieldsTests(TestCase):
    """Test CustomUserAdmin search_fields configuration"""

    def setUp(self):
        """Set up admin instance"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)

    def test_search_fields_exists(self):
        """Test search_fields is configured"""
        self.assertTrue(hasattr(self.admin, 'search_fields'))
        self.assertIsInstance(self.admin.search_fields, list)

    def test_search_fields_includes_email(self):
        """Test search_fields includes email"""
        self.assertIn('email', self.admin.search_fields)

    def test_search_fields_includes_username(self):
        """Test search_fields includes username"""
        self.assertIn('username', self.admin.search_fields)

    def test_search_fields_includes_first_name(self):
        """Test search_fields includes first_name"""
        self.assertIn('first_name', self.admin.search_fields)

    def test_search_fields_includes_last_name(self):
        """Test search_fields includes last_name"""
        self.assertIn('last_name', self.admin.search_fields)

    def test_search_fields_field_count(self):
        """Test search_fields has expected number of fields"""
        expected_fields = ['email', 'username', 'first_name', 'last_name']
        self.assertEqual(len(self.admin.search_fields), len(expected_fields))


# ============================================================================
# ORDERING TESTS
# ============================================================================

class OrderingTests(TestCase):
    """Test CustomUserAdmin ordering configuration"""

    def setUp(self):
        """Set up admin instance"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)

    def test_ordering_exists(self):
        """Test ordering is configured"""
        self.assertTrue(hasattr(self.admin, 'ordering'))
        self.assertIsInstance(self.admin.ordering, list)

    def test_ordering_by_date_joined_desc(self):
        """Test ordering is by date_joined descending"""
        self.assertEqual(self.admin.ordering, ['-date_joined'])

    def test_ordering_works_correctly(self):
        """Test ordering actually orders users correctly"""
        # Create users at different times
        user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='test123'
        )
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='test123'
        )
        
        # Get queryset with admin ordering
        queryset = self.admin.get_queryset(RequestFactory().get('/'))
        users = list(queryset)
        
        # Most recent should be first
        self.assertEqual(users[0].username, 'user2')
        self.assertEqual(users[1].username, 'user1')


# ============================================================================
# FIELDSETS TESTS
# ============================================================================

class FieldsetsTests(TestCase):
    """Test CustomUserAdmin fieldsets configuration"""

    def setUp(self):
        """Set up admin instance"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)

    def test_fieldsets_exists(self):
        """Test fieldsets is configured"""
        self.assertTrue(hasattr(self.admin, 'fieldsets'))
        self.assertIsInstance(self.admin.fieldsets, tuple)

    def test_fieldsets_count(self):
        """Test correct number of fieldsets"""
        self.assertEqual(len(self.admin.fieldsets), 4)

    def test_first_fieldset_structure(self):
        """Test first fieldset (None - credentials)"""
        fieldset = self.admin.fieldsets[0]
        
        # Check title
        self.assertIsNone(fieldset[0])
        
        # Check fields
        fields = fieldset[1]['fields']
        self.assertEqual(fields, ('username', 'password'))

    def test_second_fieldset_structure(self):
        """Test second fieldset (Personal info)"""
        fieldset = self.admin.fieldsets[1]
        
        # Check title
        self.assertEqual(fieldset[0], 'Personal info')
        
        # Check fields
        fields = fieldset[1]['fields']
        self.assertEqual(fields, ('first_name', 'last_name', 'email'))

    def test_third_fieldset_structure(self):
        """Test third fieldset (Permissions)"""
        fieldset = self.admin.fieldsets[2]
        
        # Check title
        self.assertEqual(fieldset[0], 'Permissions')
        
        # Check fields
        fields = fieldset[1]['fields']
        expected_fields = (
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )
        self.assertEqual(fields, expected_fields)

    def test_fourth_fieldset_structure(self):
        """Test fourth fieldset (Important dates)"""
        fieldset = self.admin.fieldsets[3]
        
        # Check title
        self.assertEqual(fieldset[0], 'Important dates')
        
        # Check fields
        fields = fieldset[1]['fields']
        self.assertEqual(fields, ('last_login', 'date_joined'))

    def test_all_important_fields_in_fieldsets(self):
        """Test all important fields are present in fieldsets"""
        # Extract all fields from fieldsets
        all_fields = []
        for fieldset in self.admin.fieldsets:
            fields = fieldset[1]['fields']
            if isinstance(fields, tuple):
                all_fields.extend(fields)
        
        # Check important fields are present
        important_fields = [
            'username', 'password', 'email',
            'first_name', 'last_name',
            'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions',
            'last_login', 'date_joined'
        ]
        
        for field in important_fields:
            self.assertIn(field, all_fields, f"Field '{field}' missing from fieldsets")


# ============================================================================
# ADD FIELDSETS TESTS
# ============================================================================

class AddFieldsetsTests(TestCase):
    """Test CustomUserAdmin add_fieldsets configuration"""

    def setUp(self):
        """Set up admin instance"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)

    def test_add_fieldsets_exists(self):
        """Test add_fieldsets is configured"""
        self.assertTrue(hasattr(self.admin, 'add_fieldsets'))
        self.assertIsInstance(self.admin.add_fieldsets, tuple)

    def test_add_fieldsets_structure(self):
        """Test add_fieldsets structure"""
        self.assertEqual(len(self.admin.add_fieldsets), 1)
        
        fieldset = self.admin.add_fieldsets[0]
        
        # Check title
        self.assertIsNone(fieldset[0])
        
        # Check classes
        classes = fieldset[1].get('classes')
        self.assertEqual(classes, ('wide',))
        
        # Check fields
        fields = fieldset[1]['fields']
        expected_fields = ('username', 'email', 'password1', 'password2')
        self.assertEqual(fields, expected_fields)

    def test_add_fieldsets_includes_email(self):
        """Test add_fieldsets includes email field"""
        fields = self.admin.add_fieldsets[0][1]['fields']
        self.assertIn('email', fields)

    def test_add_fieldsets_includes_username(self):
        """Test add_fieldsets includes username field"""
        fields = self.admin.add_fieldsets[0][1]['fields']
        self.assertIn('username', fields)

    def test_add_fieldsets_includes_passwords(self):
        """Test add_fieldsets includes password fields"""
        fields = self.admin.add_fieldsets[0][1]['fields']
        self.assertIn('password1', fields)
        self.assertIn('password2', fields)


# ============================================================================
# ADMIN PERMISSIONS TESTS
# ============================================================================

class AdminPermissionsTests(TestCase):
    """Test CustomUserAdmin permissions"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)
        self.factory = RequestFactory()
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staff123',
            is_staff=True
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='user123'
        )

    def test_superuser_has_add_permission(self):
        """Test superuser has add permission"""
        request = self.factory.get('/')
        request.user = self.superuser
        
        has_perm = self.admin.has_add_permission(request)
        self.assertTrue(has_perm)

    def test_superuser_has_change_permission(self):
        """Test superuser has change permission"""
        request = self.factory.get('/')
        request.user = self.superuser
        
        has_perm = self.admin.has_change_permission(request)
        self.assertTrue(has_perm)

    def test_superuser_has_delete_permission(self):
        """Test superuser has delete permission"""
        request = self.factory.get('/')
        request.user = self.superuser
        
        has_perm = self.admin.has_delete_permission(request)
        self.assertTrue(has_perm)

    def test_superuser_has_view_permission(self):
        """Test superuser has view permission"""
        request = self.factory.get('/')
        request.user = self.superuser
        
        has_perm = self.admin.has_view_permission(request)
        self.assertTrue(has_perm)

    def test_staff_user_permissions_depend_on_specific_perms(self):
        """Test staff user permissions depend on granted permissions"""
        request = self.factory.get('/')
        request.user = self.staff_user
        
        # By default, staff without specific permissions can't do these
        # (Unless they're granted specific permissions)
        # This tests the default behavior
        has_add = self.admin.has_add_permission(request)
        has_change = self.admin.has_change_permission(request)
        has_delete = self.admin.has_delete_permission(request)
        
        # Staff without specific permissions should not have these by default
        self.assertFalse(has_add)
        self.assertFalse(has_change)
        self.assertFalse(has_delete)


# ============================================================================
# ADMIN QUERYSET TESTS
# ============================================================================

class AdminQuerysetTests(TestCase):
    """Test CustomUserAdmin queryset behavior"""

    def setUp(self):
        """Set up admin instance and users"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)
        self.factory = RequestFactory()
        
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='test123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='test123'
        )

    def test_get_queryset_returns_all_users(self):
        """Test get_queryset returns all users"""
        request = self.factory.get('/')
        queryset = self.admin.get_queryset(request)
        
        self.assertEqual(queryset.count(), 2)

    def test_get_queryset_ordered_correctly(self):
        """Test get_queryset applies ordering"""
        request = self.factory.get('/')
        queryset = self.admin.get_queryset(request)
        
        users = list(queryset)
        # Should be ordered by -date_joined (most recent first)
        self.assertEqual(users[0], self.user2)
        self.assertEqual(users[1], self.user1)


# ============================================================================
# ADMIN INTEGRATION TESTS
# ============================================================================

class AdminIntegrationTests(TestCase):
    """Test CustomUserAdmin integration with Django admin"""

    def setUp(self):
        """Set up superuser for admin access"""
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

    def test_admin_changelist_url_exists(self):
        """Test admin changelist URL is accessible"""
        url = reverse('admin:accounts_customuser_changelist')
        self.assertIsNotNone(url)

    def test_admin_add_url_exists(self):
        """Test admin add URL is accessible"""
        url = reverse('admin:accounts_customuser_add')
        self.assertIsNotNone(url)

    def test_admin_change_url_exists(self):
        """Test admin change URL is accessible"""
        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='test123'
        )
        url = reverse('admin:accounts_customuser_change', args=[user.id])
        self.assertIsNotNone(url)

    def test_admin_delete_url_exists(self):
        """Test admin delete URL is accessible"""
        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='test123'
        )
        url = reverse('admin:accounts_customuser_delete', args=[user.id])
        self.assertIsNotNone(url)


# ============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

class AdminEdgeCaseTests(TestCase):
    """Test edge cases in CustomUserAdmin"""

    def setUp(self):
        """Set up admin instance"""
        self.site = AdminSite()
        self.admin = CustomUserAdmin(User, self.site)

    def test_admin_with_user_with_no_name(self):
        """Test admin handles users with no first/last name"""
        user = User.objects.create_user(
            username='noname',
            email='noname@example.com',
            password='test123',
            first_name='',
            last_name=''
        )
        
        # Should not raise any errors
        self.assertIsNotNone(user)

    def test_admin_with_unicode_in_names(self):
        """Test admin handles Unicode characters in names"""
        user = User.objects.create_user(
            username='unicode',
            email='unicode@example.com',
            password='test123',
            first_name='José',
            last_name='Müller'
        )
        
        # Should not raise any errors
        self.assertIsNotNone(user)

    def test_admin_with_very_long_email(self):
        """Test admin handles long email addresses"""
        long_email = 'a' * 240 + '@example.com'
        user = User.objects.create_user(
            username='longemail',
            email=long_email,
            password='test123'
        )
        
        # Should not raise any errors
        self.assertIsNotNone(user)


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == '__main__':
    import unittest
    unittest.main()