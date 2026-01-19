# products/tests/tests_admin.py
"""
Comprehensive tests for products admin
Tests admin interfaces, list displays, filters, and custom admin functionality
"""

from django.test import TestCase, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.urls import reverse
from decimal import Decimal
from products.models import Category, NyscKit, NyscTour, Church
from products.admin import (
    CategoryAdmin,
    NyscKitAdmin,
    NyscTourAdmin,
    ChurchAdmin
)

User = get_user_model()


class MockRequest:
    """Mock request object for testing"""
    pass


class CategoryAdminTest(TestCase):
    """Test CategoryAdmin functionality"""

    def setUp(self):
        """Set up test data"""
        self.site = AdminSite()
        self.admin = CategoryAdmin(Category, self.site)
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit',
            description='NYSC Kit products'
        )
        
        # Create products for product count
        NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00')
        )
        NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00')
        )

    def test_category_list_display(self):
        """Test list_display configuration"""
        expected_fields = ['name', 'slug', 'product_type', 'product_count']
        self.assertEqual(list(self.admin.list_display), expected_fields)

    def test_category_list_filter(self):
        """Test list_filter configuration"""
        self.assertIn('product_type', self.admin.list_filter)

    def test_category_prepopulated_fields(self):
        """Test prepopulated_fields configuration"""
        self.assertIn('slug', self.admin.prepopulated_fields)
        self.assertEqual(self.admin.prepopulated_fields['slug'], ('name',))

    def test_category_search_fields(self):
        """Test search_fields configuration"""
        self.assertIn('name', self.admin.search_fields)
        self.assertIn('description', self.admin.search_fields)

    def test_category_product_count_method(self):
        """Test product_count method returns correct count"""
        count_html = self.admin.product_count(self.category)
        
        # Should contain the count (2)
        self.assertIn('2', count_html)
        # Should be formatted with color
        self.assertIn('#064E3B', count_html)

    def test_category_product_count_zero(self):
        """Test product_count with no products"""
        empty_category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        
        count_html = self.admin.product_count(empty_category)
        self.assertIn('0', str(count_html))

    def test_category_product_count_short_description(self):
        """Test product_count has short_description"""
        self.assertEqual(self.admin.product_count.short_description, 'Products')


class NyscKitAdminTest(TestCase):
    """Test NyscKitAdmin functionality"""

    def setUp(self):
        """Set up test data"""
        self.site = AdminSite()
        self.admin = NyscKitAdmin(NyscKit, self.site)
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00'),
            available=True,
            out_of_stock=False
        )

    def test_kit_list_display(self):
        """Test list_display includes correct fields"""
        expected_fields = [
            'thumbnail_preview', 'id', 'name', 'category', 'price',
            'available', 'out_of_stock', 'created'
        ]
        
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_kit_list_editable(self):
        """Test list_editable fields"""
        expected_editable = ['price', 'available', 'out_of_stock']
        self.assertEqual(list(self.admin.list_editable), expected_editable)

    def test_kit_list_filter(self):
        """Test list_filter configuration"""
        filters = ['available', 'out_of_stock', 'created', 'updated', 'category']
        
        for filter_field in filters:
            self.assertIn(filter_field, self.admin.list_filter)

    def test_kit_search_fields(self):
        """Test search_fields configuration"""
        self.assertIn('name', self.admin.search_fields)
        self.assertIn('description', self.admin.search_fields)

    def test_kit_date_hierarchy(self):
        """Test date_hierarchy is set"""
        self.assertEqual(self.admin.date_hierarchy, 'created')

    def test_kit_readonly_fields(self):
        """Test readonly_fields configuration"""
        readonly = ['created', 'updated', 'large_thumbnail_preview']
        
        for field in readonly:
            self.assertIn(field, self.admin.readonly_fields)

    def test_kit_fieldsets_basic_information(self):
        """Test Basic Information fieldset"""
        fieldsets = self.admin.fieldsets
        basic_info = fieldsets[0]
        
        self.assertEqual(basic_info[0], 'Basic Information')
        self.assertIn('name', basic_info[1]['fields'])
        self.assertIn('slug', basic_info[1]['fields'])
        self.assertIn('category', basic_info[1]['fields'])

    def test_kit_fieldsets_product_details(self):
        """Test Product Details fieldset"""
        fieldsets = self.admin.fieldsets
        product_details = fieldsets[1]
        
        self.assertEqual(product_details[0], 'Product Details')
        self.assertIn('price', product_details[1]['fields'])
        self.assertIn('description', product_details[1]['fields'])

    def test_kit_fieldsets_availability(self):
        """Test Availability fieldset"""
        fieldsets = self.admin.fieldsets
        availability = fieldsets[2]
        
        self.assertEqual(availability[0], 'Availability')
        self.assertIn('available', availability[1]['fields'])
        self.assertIn('out_of_stock', availability[1]['fields'])

    def test_kit_fieldsets_images(self):
        """Test Images fieldset"""
        fieldsets = self.admin.fieldsets
        images = fieldsets[3]
        
        self.assertEqual(images[0], 'Images')
        self.assertIn('image', images[1]['fields'])
        self.assertIn('large_thumbnail_preview', images[1]['fields'])

    def test_kit_thumbnail_preview_method_exists(self):
        """Test thumbnail_preview method exists"""
        self.assertTrue(hasattr(self.admin, 'thumbnail_preview'))

    def test_kit_large_thumbnail_preview_method_exists(self):
        """Test large_thumbnail_preview method exists"""
        self.assertTrue(hasattr(self.admin, 'large_thumbnail_preview'))


class NyscTourAdminTest(TestCase):
    """Test NyscTourAdmin functionality"""

    def setUp(self):
        """Set up test data"""
        self.site = AdminSite()
        self.admin = NyscTourAdmin(NyscTour, self.site)
        
        self.category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        
        self.tour = NyscTour.objects.create(
            name='Lagos',
            category=self.category,
            price=Decimal('15000.00')
        )

    def test_tour_list_display(self):
        """Test list_display includes correct fields"""
        expected_fields = [
            'thumbnail_preview', 'id', 'name', 'category', 'price',
            'available', 'out_of_stock', 'created'
        ]
        
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_tour_list_editable(self):
        """Test list_editable fields"""
        self.assertIn('price', self.admin.list_editable)
        self.assertIn('available', self.admin.list_editable)
        self.assertIn('out_of_stock', self.admin.list_editable)

    def test_tour_search_fields(self):
        """Test search_fields configuration"""
        self.assertIn('name', self.admin.search_fields)
        self.assertIn('description', self.admin.search_fields)


class ChurchAdminTest(TestCase):
    """Test ChurchAdmin functionality"""

    def setUp(self):
        """Set up test data"""
        self.site = AdminSite()
        self.admin = ChurchAdmin(Church, self.site)
        
        self.category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        
        self.church_product = Church.objects.create(
            name='Quality RCCG Shirt',
            church='RCCG',
            category=self.category,
            price=Decimal('3500.00')
        )

    def test_church_list_display(self):
        """Test list_display includes correct fields"""
        expected_fields = [
            'thumbnail_preview', 'id', 'name', 'category', 'price',
            'available', 'out_of_stock', 'created'
        ]
        
        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_church_list_editable(self):
        """Test list_editable fields"""
        self.assertIn('price', self.admin.list_editable)
        self.assertIn('available', self.admin.list_editable)

    def test_church_search_fields(self):
        """Test search_fields configuration"""
        self.assertIn('name', self.admin.search_fields)
        self.assertIn('description', self.admin.search_fields)


class AdminIntegrationTest(TestCase):
    """Test admin interface integration with actual Django admin"""

    def setUp(self):
        """Set up test data and admin user"""
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00')
        )

    def test_category_admin_access(self):
        """Test accessing category admin page"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_category_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_category_admin_add_page(self):
        """Test accessing category add page"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_category_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_category_admin_change_page(self):
        """Test accessing category change page"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_category_change', args=[self.category.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_nysckit_admin_access(self):
        """Test accessing NYSC Kit admin page"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_nysckit_changelist')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_nysckit_admin_add_page(self):
        """Test accessing NYSC Kit add page"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_nysckit_add')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_nysckit_admin_change_page(self):
        """Test accessing NYSC Kit change page"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_nysckit_change', args=[self.kit.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_nysckit_admin_search(self):
        """Test searching in NYSC Kit admin"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_nysckit_changelist')
        response = self.client.get(url, {'q': 'Kakhi'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kakhi')

    def test_nysckit_admin_filter_by_available(self):
        """Test filtering by available in admin"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_nysckit_changelist')
        response = self.client.get(url, {'available__exact': '1'})
        
        self.assertEqual(response.status_code, 200)

    def test_category_admin_create(self):
        """Test creating category through admin"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_category_add')
        data = {
            'name': 'NYSC TOUR',
            'slug': 'nysc-tour',
            'product_type': 'nysc_tour',
            'description': 'Tour products'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(slug='nysc-tour').exists())

    def test_nysckit_admin_create(self):
        """Test creating NYSC Kit through admin"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_nysckit_add')
        data = {
            'name': 'Quality Nysc Vest',
            'type': 'vest',
            'category': self.category.id,
            'price': '2000.00',
            'slug': 'quality-nysc-vest',
            'available': True,
            'out_of_stock': False,
            'description': 'Test vest'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        self.assertTrue(NyscKit.objects.filter(type='vest').exists())

    def test_nysckit_admin_update(self):
        """Test updating NYSC Kit through admin"""
        self.client.force_login(self.admin_user)
        
        url = reverse('admin:products_nysckit_change', args=[self.kit.id])
        data = {
            'name': 'Quality Nysc Kakhi',
            'type': 'kakhi',
            'category': self.category.id,
            'price': '6000.00',  # Updated price
            'slug': self.kit.slug,
            'available': True,
            'out_of_stock': False,
            'description': 'Updated description'
        }
        
        response = self.client.post(url, data)
        
        self.kit.refresh_from_db()
        self.assertEqual(self.kit.price, Decimal('6000.00'))

    def test_admin_unauthorized_access(self):
        """Test that non-admin users cannot access admin"""
        url = reverse('admin:products_category_changelist')
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_admin_delete_category(self):
        """Test deleting category through admin"""
        self.client.force_login(self.admin_user)
        
        category_to_delete = Category.objects.create(
            name='TO DELETE',
            slug='to-delete',
            product_type='church'
        )
        
        url = reverse('admin:products_category_delete', args=[category_to_delete.id])
        response = self.client.post(url, {'post': 'yes'})
        
        # Should be soft deleted
        category_to_delete.refresh_from_db()
        self.assertIsNotNone(category_to_delete.deleted_at)

    def test_nysckit_admin_bulk_actions(self):
        """Test bulk actions in admin"""
        self.client.force_login(self.admin_user)
        
        # Create multiple kits
        kit2 = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00')
        )
        
        url = reverse('admin:products_nysckit_changelist')
        data = {
            'action': 'delete_selected',
            '_selected_action': [str(self.kit.id), str(kit2.id)],
            'post': 'yes'
        }
        
        response = self.client.post(url, data)
        
        # Items should be soft deleted
        self.kit.refresh_from_db()
        kit2.refresh_from_db()
        self.assertIsNotNone(self.kit.deleted_at)
        self.assertIsNotNone(kit2.deleted_at)


class AdminPermissionsTest(TestCase):
    """Test admin permissions and access control"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create staff user without superuser
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123'
        )
        self.staff_user.is_staff = True
        self.staff_user.save()

    def test_staff_can_access_admin(self):
        """Test that staff users can access admin"""
        self.client.force_login(self.staff_user)
        
        url = reverse('admin:index')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_regular_user_cannot_access_admin(self):
        """Test that regular users cannot access admin"""
        regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='testpass123'
        )
        
        self.client.force_login(regular_user)
        
        url = reverse('admin:products_category_changelist')
        response = self.client.get(url)
        
        # Should redirect or deny access
        self.assertNotEqual(response.status_code, 200)


class AdminEdgeCasesTest(TestCase):
    """Test edge cases in admin functionality"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )

    def test_admin_with_null_category(self):
        """Test admin handles products with null category"""
        kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=None,
            price=Decimal('5000.00')
        )
        
        self.client.force_login(self.admin_user)
        url = reverse('admin:products_nysckit_change', args=[kit.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_admin_with_very_long_description(self):
        """Test admin handles very long descriptions"""
        long_desc = 'A' * 10000
        
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit',
            description=long_desc
        )
        
        self.client.force_login(self.admin_user)
        url = reverse('admin:products_category_change', args=[category.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_admin_with_special_characters(self):
        """Test admin handles special characters"""
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit',
            description="Test with special chars: <>&\"'éñ中文"
        )
        
        self.client.force_login(self.admin_user)
        url = reverse('admin:products_category_change', args=[category.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)

    def test_admin_duplicate_slug_validation(self):
        """Test admin prevents duplicate slugs"""
        Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.client.force_login(self.admin_user)
        url = reverse('admin:products_category_add')
        data = {
            'name': 'NYSC TOUR',
            'slug': 'nysc-kit',  # Duplicate slug
            'product_type': 'nysc_tour'
        }
        
        response = self.client.post(url, data)
        
        # Should show error, not create
        self.assertFormError(response, 'adminform', 'slug', 
                           'Category with this Slug already exists.')