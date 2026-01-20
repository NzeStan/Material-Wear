# order/tests/test_admin.py
"""
Comprehensive tests for Order Admin

Coverage:
- OrderItemInline: fields, readonly, display methods, permissions
- BaseOrderAdmin: list display, filters, search, fieldsets, actions
- NyscKitOrderAdmin: specific fields, list display, filters
- NyscTourOrderAdmin: inheritance
- ChurchOrderAdmin: delivery display, specific fields
- Custom display methods and formatting
- Admin permissions
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from unittest.mock import Mock, patch
from order.admin import (
    OrderItemInline, BaseOrderAdmin, NyscKitOrderAdmin,
    NyscTourOrderAdmin, ChurchOrderAdmin
)
from order.models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem
from products.models import Category, NyscKit

User = get_user_model()


class MockRequest:
    """Mock request object for admin tests"""
    pass


class OrderItemInlineTests(TestCase):
    """Test OrderItemInline admin configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.inline = OrderItemInline(BaseOrder, self.site)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name='Test Cap',
            type='cap',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
    
    def test_inline_model_is_orderitem(self):
        """Test inline uses OrderItem model"""
        self.assertEqual(self.inline.model, OrderItem)
    
    def test_extra_is_zero(self):
        """Test no extra empty forms are shown"""
        self.assertEqual(self.inline.extra, 0)
    
    def test_can_delete_is_false(self):
        """Test items cannot be deleted from inline"""
        self.assertFalse(self.inline.can_delete)
    
    def test_readonly_fields_configuration(self):
        """Test readonly fields are properly set"""
        expected_readonly = ['product_display', 'price', 'quantity', 'item_cost']
        
        for field in expected_readonly:
            self.assertIn(field, self.inline.readonly_fields)
    
    def test_fields_configuration(self):
        """Test fields displayed in inline"""
        # ✅ FIXED: Correct field order matches actual admin implementation
        expected_fields = ['product_display', 'quantity', 'price', 'item_cost']
        self.assertEqual(self.inline.fields, expected_fields)
    
    def test_product_display_with_image(self):
        """Test product_display shows SVG placeholder"""
        product_ct = ContentType.objects.get_for_model(self.product)
        item = OrderItem.objects.create(
            order=self.order,
            content_type=product_ct,
            object_id=self.product.id,
            price=Decimal('5000.00'),
            quantity=1
        )
        
        html = self.inline.product_display(item)
        
        # Should show SVG placeholder
        self.assertIn('svg', html)
        self.assertIn('Test Cap', html)
    
    def test_product_display_with_no_product(self):
        """Test product_display handles missing product"""
        # Create item without proper product link
        item = Mock()
        item.product = None
        
        html = self.inline.product_display(item)
        
        self.assertIn('No Product', html)
    
    def test_item_cost_calculation(self):
        """Test item_cost displays correctly"""
        product_ct = ContentType.objects.get_for_model(self.product)
        item = OrderItem.objects.create(
            order=self.order,
            content_type=product_ct,
            object_id=self.product.id,
            price=Decimal('5000.00'),
            quantity=3
        )
        
        html = self.inline.item_cost(item)
        
        # Should display 15000.00 formatted
        self.assertIn('15,000.00', html)
        self.assertIn('₦', html)
    
    def test_item_cost_formatting(self):
        """Test item_cost formats with color and styling"""
        product_ct = ContentType.objects.get_for_model(self.product)
        item = OrderItem.objects.create(
            order=self.order,
            content_type=product_ct,
            object_id=self.product.id,
            price=Decimal('1234.56'),
            quantity=2
        )
        
        html = self.inline.item_cost(item)
        
        self.assertIn('color: #064E3B', html)
        self.assertIn('font-weight: bold', html)
        self.assertIn('2,469.12', html)  # 1234.56 * 2


class BaseOrderAdminTests(TestCase):
    """Test BaseOrderAdmin configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = BaseOrderAdmin(BaseOrder, self.site)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_staff=True,
            is_superuser=True
        )
    
    def test_list_display_configuration(self):
        """Test list_display contains expected fields"""
        expected = [
            'serial_number', 'full_name_display', 'email',
            'phone_number', 'order_total', 'paid_status',
            'generation_status', 'created'
        ]
        self.assertEqual(self.admin.list_display, expected)
    
    def test_list_filter_configuration(self):
        """Test list_filter contains expected fields"""
        expected = ['paid', 'items_generated', 'created']
        self.assertEqual(self.admin.list_filter, expected)
    
    def test_search_fields_configuration(self):
        """Test search_fields contains expected fields"""
        expected = ['serial_number', 'email', 'first_name', 'last_name', 'phone_number']
        self.assertEqual(self.admin.search_fields, expected)
    
    def test_readonly_fields_configuration(self):
        """Test readonly_fields contains expected fields"""
        expected = [
            'serial_number', 'user', 'created', 'updated',
            'order_total', 'items_count', 'generated_at', 'generated_by'
        ]
        self.assertEqual(self.admin.readonly_fields, expected)
    
    def test_date_hierarchy_is_created(self):
        """Test date_hierarchy is set to created"""
        self.assertEqual(self.admin.date_hierarchy, 'created')
    
    def test_inlines_contains_orderitem_inline(self):
        """Test OrderItemInline is included"""
        self.assertEqual(len(self.admin.inlines), 1)
        self.assertEqual(self.admin.inlines[0], OrderItemInline)
    
    def test_actions_contains_reset_generation_status(self):
        """Test reset_generation_status action is available"""
        self.assertIn('reset_generation_status', self.admin.actions)
    
    def test_fieldsets_structure(self):
        """Test fieldsets has correct structure"""
        self.assertIsNotNone(self.admin.fieldsets)
        self.assertIsInstance(self.admin.fieldsets, tuple)
        self.assertGreater(len(self.admin.fieldsets), 0)
    
    def test_full_name_display_method(self):
        """Test full_name_display shows formatted name"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            middle_name='David',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        display = self.admin.full_name_display(order)
        
        self.assertIn('John David Doe', display)
    
    def test_order_total_formatting(self):
        """Test order_total displays formatted currency"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('50000.00')
        )
        
        display = self.admin.order_total(order)
        
        self.assertIn('₦', display)
        self.assertIn('50,000.00', display)
    
    def test_paid_status_true(self):
        """Test paid_status displays correctly for paid orders"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            paid=True
        )
        
        display = self.admin.paid_status(order)
        
        # ✅ FIXED: Check for uppercase 'PAID'
        self.assertIn('PAID', display)
        # ✅ FIXED: Check for correct color (light green background)
        self.assertIn('#D1FAE5', display)
    
    def test_paid_status_false(self):
        """Test paid_status displays correctly for unpaid orders"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            paid=False
        )
        
        display = self.admin.paid_status(order)
        
        # ✅ FIXED: Check for uppercase 'UNPAID'
        self.assertIn('UNPAID', display)
        # ✅ FIXED: Check for correct color (light red background)
        self.assertIn('#FEE2E2', display)
    
    def test_generation_status_generated(self):
        """Test generation_status for generated orders"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            items_generated=True,
            generated_at=timezone.now(),
            generated_by=self.admin_user
        )
        
        display = self.admin.generation_status(order)
        
        # ✅ FIXED: Check for uppercase 'GENERATED'
        self.assertIn('GENERATED', display)
        # ✅ FIXED: Check for correct color (light blue background)
        self.assertIn('#DBEAFE', display)
    
    def test_generation_status_not_generated(self):
        """Test generation_status for non-generated orders"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            items_generated=False
        )
        
        display = self.admin.generation_status(order)
        
        # ✅ FIXED: Check for uppercase 'PENDING'
        self.assertIn('PENDING', display)
        # ✅ FIXED: Check for correct color (yellow background)
        self.assertIn('#FEF3C7', display)
    
    def test_items_count_with_items(self):
        """Test items_count displays count of OrderItem objects (not sum of quantities)"""
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        product = NyscKit.objects.create(
            name='Test Cap',
            type='cap',
            category=category,
            price=Decimal('5000.00'),
            available=True
        )
        
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00')
        )
        
        product_ct = ContentType.objects.get_for_model(product)
        OrderItem.objects.create(
            order=order,
            content_type=product_ct,
            object_id=product.id,
            price=Decimal('5000.00'),
            quantity=3
        )
        
        count = self.admin.items_count(order)
        
        # ✅ FIXED: items_count() returns obj.items.count() which counts OrderItem objects
        # We created 1 OrderItem with quantity=3, so count is 1, not 3
        self.assertIn('1 items', count)
    
    def test_items_count_without_items(self):
        """Test items_count returns 0 for orders without items"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('0.00')
        )
        
        count = self.admin.items_count(order)
        
        # ✅ FIXED: items_count returns HTML string, not integer
        self.assertIn('0 items', count)
    
    def test_reset_generation_status_action(self):
        """Test reset_generation_status action resets orders"""
        order1 = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            items_generated=True,
            generated_at=timezone.now(),
            generated_by=self.admin_user
        )
        
        order2 = BaseOrder.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone_number='08087654321',
            total_cost=Decimal('15000.00'),
            items_generated=True,
            generated_at=timezone.now(),
            generated_by=self.admin_user
        )
        
        # Create mock request
        request = MockRequest()
        queryset = BaseOrder.objects.filter(id__in=[order1.id, order2.id])
        
        # Execute action
        with patch.object(self.admin, 'message_user'):
            self.admin.reset_generation_status(request, queryset)
        
        # Verify orders were reset
        order1.refresh_from_db()
        order2.refresh_from_db()
        
        self.assertFalse(order1.items_generated)
        self.assertIsNone(order1.generated_at)
        self.assertIsNone(order1.generated_by)
        
        self.assertFalse(order2.items_generated)
        self.assertIsNone(order2.generated_at)
        self.assertIsNone(order2.generated_by)


class NyscKitOrderAdminTests(TestCase):
    """Test NyscKitOrderAdmin specific configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = NyscKitOrderAdmin(NyscKitOrder, self.site)
    
    def test_list_display_includes_kit_fields(self):
        """Test list_display includes state and local_government"""
        self.assertIn('state', self.admin.list_display)
        self.assertIn('local_government', self.admin.list_display)
    
    def test_list_filter_includes_state(self):
        """Test list_filter includes state"""
        self.assertIn('state', self.admin.list_filter)


class NyscTourOrderAdminTests(TestCase):
    """Test NyscTourOrderAdmin configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = NyscTourOrderAdmin(NyscTourOrder, self.site)
    
    def test_inherits_from_base_order_admin(self):
        """Test NyscTourOrderAdmin has base configuration"""
        self.assertIsInstance(self.admin, BaseOrderAdmin)


class ChurchOrderAdminTests(TestCase):
    """Test ChurchOrderAdmin specific configuration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = ChurchOrderAdmin(ChurchOrder, self.site)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_list_display_includes_delivery_fields(self):
        """Test list_display includes delivery fields"""
        self.assertIn('pickup_on_camp', self.admin.list_display)
        self.assertIn('delivery_location', self.admin.list_display)
    
    def test_list_filter_includes_delivery_fields(self):
        """Test list_filter includes delivery fields"""
        self.assertIn('pickup_on_camp', self.admin.list_filter)
        self.assertIn('delivery_state', self.admin.list_filter)
    
    def test_delivery_location_pickup_on_camp(self):
        """Test delivery_location displays 'Pickup on Camp' correctly"""
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            pickup_on_camp=True,
            delivery_state='Lagos',
            delivery_lga='Ikeja'
        )
        
        display = self.admin.delivery_location(order)
        
        self.assertIn('Pickup on Camp', display)
    
    def test_delivery_location_delivery_address(self):
        """Test delivery_location displays state and LGA"""
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            pickup_on_camp=False,
            delivery_state='Abuja',
            delivery_lga='Gwagwalada'
        )
        
        display = self.admin.delivery_location(order)
        
        self.assertIn('Abuja', display)
        self.assertIn('Gwagwalada', display)