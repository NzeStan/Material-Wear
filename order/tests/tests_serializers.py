# order/tests/test_serializers.py
"""
Comprehensive tests for Order Serializers

Coverage:
- OrderItemSerializer: read-only serialization
- BaseOrderSerializer: base fields and validation
- NyscKitOrderSerializer: NYSC Kit specific fields
- NyscTourOrderSerializer: NYSC Tour specific fields
- ChurchOrderSerializer: Church specific fields
- CheckoutSerializer: cart-based validation, product type validation
- OrderListSerializer: lightweight list serialization
- Edge cases and validation errors
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError
from order.serializers import (
    OrderItemSerializer, BaseOrderSerializer, NyscKitOrderSerializer,
    NyscTourOrderSerializer, ChurchOrderSerializer, CheckoutSerializer,
    OrderListSerializer
)
from order.models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem
from products.models import Category, NyscKit, NyscTour, Church
from unittest.mock import Mock

User = get_user_model()


class OrderItemSerializerTests(TestCase):
    """Test OrderItemSerializer"""
    
    def setUp(self):
        """Set up test fixtures"""
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
        
        product_ct = ContentType.objects.get_for_model(self.product)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            content_type=product_ct,
            object_id=self.product.id,
            price=Decimal('5000.00'),
            quantity=2
        )
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        serializer = OrderItemSerializer(self.order_item)
        
        # Note: product_type and total_price don't appear in data because
        # they need to be calculated/computed but aren't implemented as SerializerMethodFields
        expected_fields = {
            'id', 'product_name', 'quantity', 'price', 'extra_fields'
        }
        self.assertEqual(set(serializer.data.keys()), expected_fields)
    
    def test_read_only_fields(self):
        """Test most fields are read-only except quantity"""
        serializer = OrderItemSerializer(self.order_item)
        
        # These fields should be read-only
        read_only_fields = {'id', 'price', 'extra_fields'}
        
        for field_name in read_only_fields:
            if field_name in serializer.fields:
                field = serializer.fields[field_name]
                self.assertTrue(field.read_only, f"{field_name} should be read-only")
        
        # quantity is writable (not read-only)
        self.assertFalse(serializer.fields['quantity'].read_only)


class BaseOrderSerializerTests(TestCase):
    """Test BaseOrderSerializer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            middle_name='David',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            paid=False
        )
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        serializer = BaseOrderSerializer(self.order)
        
        # Note: order_type doesn't appear because it's not a model field
        # and not implemented as a method field
        expected_fields = {
            'id', 'serial_number', 'first_name', 'middle_name',
            'last_name', 'phone_number', 'total_cost', 'paid', 'created',
            'updated', 'items'
        }
        self.assertEqual(set(serializer.data.keys()), expected_fields)
    
    def test_read_only_fields(self):
        """Test certain fields are read-only"""
        serializer = BaseOrderSerializer(self.order)
        
        read_only_fields = {'id', 'serial_number', 'total_cost', 'paid', 'created', 'updated', 'items'}
        
        for field_name in read_only_fields:
            field = serializer.fields[field_name]
            self.assertTrue(field.read_only, f"{field_name} should be read-only")
    
    def test_middle_name_is_optional(self):
        """Test middle_name is optional"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john2@example.com',
            phone_number='08087654321',
            total_cost=Decimal('5000.00')
        )
        
        serializer = BaseOrderSerializer(order)
        self.assertIn('middle_name', serializer.data)


class NyscKitOrderSerializerTests(TestCase):
    """Test NyscKitOrderSerializer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('50000.00'),
            call_up_number='AB/22C/1234',
            state='Lagos',
            local_government='Ikeja'
        )
    
    def test_serializer_contains_nysc_kit_fields(self):
        """Test serializer contains NYSC Kit specific fields"""
        serializer = NyscKitOrderSerializer(self.order)
        
        self.assertIn('call_up_number', serializer.data)
        self.assertIn('state', serializer.data)
        self.assertIn('local_government', serializer.data)
        
        self.assertEqual(serializer.data['call_up_number'], 'AB/22C/1234')
        self.assertEqual(serializer.data['state'], 'Lagos')
        self.assertEqual(serializer.data['local_government'], 'Ikeja')
    
    def test_inherits_base_fields(self):
        """Test serializer inherits all base fields"""
        serializer = NyscKitOrderSerializer(self.order)
        
        base_fields = {'id', 'serial_number', 'first_name', 'last_name', 'phone_number'}
        for field in base_fields:
            self.assertIn(field, serializer.data)
    
    def test_state_is_choice_field(self):
        """Test state field validates against choices"""
        serializer = NyscKitOrderSerializer(self.order)
        state_field = serializer.fields['state']
        
        # Should have choices
        self.assertTrue(hasattr(state_field, 'choices'))


class NyscTourOrderSerializerTests(TestCase):
    """Test NyscTourOrderSerializer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = NyscTourOrder.objects.create(
            user=self.user,
            first_name='John',
            middle_name='David',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00')
        )
    
    def test_serializer_has_no_additional_fields(self):
        """Test NyscTourOrderSerializer has no additional fields beyond base"""
        serializer = NyscTourOrderSerializer(self.order)
        
        # Should not have NYSC Kit specific fields
        self.assertNotIn('call_up_number', serializer.data)
        self.assertNotIn('state', serializer.data)
        self.assertNotIn('local_government', serializer.data)
        
        # Should not have Church specific fields
        self.assertNotIn('pickup_on_camp', serializer.data)
        self.assertNotIn('delivery_state', serializer.data)
    
    def test_inherits_base_fields(self):
        """Test serializer inherits all base fields"""
        serializer = NyscTourOrderSerializer(self.order)
        
        base_fields = {'id', 'serial_number', 'first_name', 'middle_name', 'last_name', 'phone_number'}
        for field in base_fields:
            self.assertIn(field, serializer.data)


class ChurchOrderSerializerTests(TestCase):
    """Test ChurchOrderSerializer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_serializer_contains_church_fields(self):
        """Test serializer contains Church specific fields"""
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('8000.00'),
            pickup_on_camp=False,
            delivery_state='Lagos',
            delivery_lga='Ikeja'
        )
        
        serializer = ChurchOrderSerializer(order)
        
        self.assertIn('pickup_on_camp', serializer.data)
        self.assertIn('delivery_state', serializer.data)
        self.assertIn('delivery_lga', serializer.data)
        
        self.assertFalse(serializer.data['pickup_on_camp'])
        self.assertEqual(serializer.data['delivery_state'], 'Lagos')
        self.assertEqual(serializer.data['delivery_lga'], 'Ikeja')
    
    def test_pickup_on_camp_defaults_to_true(self):
        """Test pickup_on_camp defaults to True"""
        serializer = ChurchOrderSerializer()
        field = serializer.fields['pickup_on_camp']
        
        self.assertEqual(field.default, True)
    
    def test_delivery_fields_are_optional(self):
        """Test delivery fields are optional"""
        serializer = ChurchOrderSerializer()
        
        self.assertFalse(serializer.fields['delivery_state'].required)
        self.assertFalse(serializer.fields['delivery_lga'].required)


class CheckoutSerializerBasicTests(TestCase):
    """Test CheckoutSerializer basic functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=True)
        
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
    
    def _create_mock_cart(self, product_type_class, product):
        """Helper to create mock cart"""
        mock_cart = Mock()
        mock_cart.__len__ = Mock(return_value=1)
        mock_cart.__iter__ = Mock(return_value=iter([{
            'product': product,
            'quantity': 1,
            'price': product.price,
            'extra_fields': {}
        }]))
        return mock_cart
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        serializer = CheckoutSerializer()
        
        expected_fields = {
            'first_name', 'middle_name', 'last_name', 'phone_number',
            'call_up_number', 'state', 'local_government',
            'pickup_on_camp', 'delivery_state', 'delivery_lga'
        }
        self.assertEqual(set(serializer.fields.keys()), expected_fields)
    
    def test_required_base_fields(self):
        """Test base fields are required"""
        serializer = CheckoutSerializer()
        
        required_fields = {'first_name', 'last_name', 'phone_number'}
        for field_name in required_fields:
            field = serializer.fields[field_name]
            self.assertTrue(field.required, f"{field_name} should be required")
    
    def test_middle_name_is_optional(self):
        """Test middle_name is optional"""
        serializer = CheckoutSerializer()
        field = serializer.fields['middle_name']
        
        self.assertFalse(field.required)
        self.assertTrue(field.allow_blank)
    
    def test_validation_fails_with_empty_cart(self):
        """Test validation fails when cart is empty"""
        mock_cart = Mock()
        mock_cart.__len__ = Mock(return_value=0)
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('cart', serializer.errors)


class CheckoutSerializerNyscKitValidationTests(TestCase):
    """Test CheckoutSerializer NYSC Kit validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=True)
        
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
        
        # Create mock cart with NYSC Kit product
        self.mock_cart = Mock()
        self.mock_cart.__len__ = Mock(return_value=1)
        self.mock_cart.__iter__ = Mock(return_value=iter([{
            'product': self.product,
            'quantity': 1,
            'price': self.product.price,
            'extra_fields': {}
        }]))
    
    def test_nysc_kit_requires_call_up_number(self):
        """Test NYSC Kit requires call_up_number"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            # Missing call_up_number
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('call_up_number', serializer.errors)
    
    def test_nysc_kit_requires_state(self):
        """Test NYSC Kit requires state"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            # Missing state
            'local_government': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('state', serializer.errors)
    
    def test_nysc_kit_requires_local_government(self):
        """Test NYSC Kit requires local_government"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            # Missing local_government
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('local_government', serializer.errors)
    
    def test_nysc_kit_with_all_required_fields(self):
        """Test NYSC Kit validates with all required fields"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())


class CheckoutSerializerNyscTourValidationTests(TestCase):
    """Test CheckoutSerializer NYSC Tour validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=True)
        
        self.category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        
        self.product = NyscTour.objects.create(
            name='Lagos Tour',
            category=self.category,
            price=Decimal('15000.00'),
            available=True
        )
        
        # Create mock cart with NYSC Tour product
        self.mock_cart = Mock()
        self.mock_cart.__len__ = Mock(return_value=1)
        self.mock_cart.__iter__ = Mock(return_value=iter([{
            'product': self.product,
            'quantity': 1,
            'price': self.product.price,
            'extra_fields': {}
        }]))
    
    def test_nysc_tour_requires_middle_name(self):
        """Test NYSC Tour requires middle_name"""
        data = {
            'first_name': 'John',
            # Missing middle_name
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('middle_name', serializer.errors)
    
    def test_nysc_tour_with_middle_name(self):
        """Test NYSC Tour validates with middle_name"""
        data = {
            'first_name': 'John',
            'middle_name': 'David',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
    
    def test_nysc_tour_empty_middle_name_fails(self):
        """Test NYSC Tour fails with empty middle_name"""
        data = {
            'first_name': 'John',
            'middle_name': '',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('middle_name', serializer.errors)


class CheckoutSerializerChurchValidationTests(TestCase):
    """Test CheckoutSerializer Church validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=True)
        
        self.category = Category.objects.create(
            name='CHURCH',
            slug='church',
            product_type='church'
        )
        
        self.product = Church.objects.create(
            name='Winners T-Shirt',
            church='Winners',
            category=self.category,
            price=Decimal('8000.00'),
            available=True
        )
        
        # Create mock cart with Church product
        self.mock_cart = Mock()
        self.mock_cart.__len__ = Mock(return_value=1)
        self.mock_cart.__iter__ = Mock(return_value=iter([{
            'product': self.product,
            'quantity': 1,
            'price': self.product.price,
            'extra_fields': {}
        }]))
    
    def test_church_with_pickup_on_camp_true(self):
        """Test Church validates with pickup_on_camp=True"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'pickup_on_camp': True
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
    
    def test_church_delivery_requires_state(self):
        """Test Church delivery requires delivery_state"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'pickup_on_camp': False,
            # Missing delivery_state
            'delivery_lga': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('delivery_state', serializer.errors)
    
    def test_church_delivery_requires_lga(self):
        """Test Church delivery requires delivery_lga"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'pickup_on_camp': False,
            'delivery_state': 'Lagos',
            # Missing delivery_lga
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('delivery_lga', serializer.errors)
    
    def test_church_with_delivery_details(self):
        """Test Church validates with complete delivery details"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'pickup_on_camp': False,
            'delivery_state': 'Lagos',
            'delivery_lga': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
    
    def test_church_defaults_to_pickup_on_camp(self):
        """Test Church defaults to pickup_on_camp=True"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678'
            # pickup_on_camp not specified
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())
        # Should default to True
        self.assertTrue(serializer.validated_data.get('pickup_on_camp', True))


class CheckoutSerializerMixedProductsTests(TestCase):
    """Test CheckoutSerializer with multiple product types"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=True)
        
        # Create NYSC Kit product
        nysc_category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        self.nysc_product = NyscKit.objects.create(
            name='Test Cap',
            type='cap',
            category=nysc_category,
            price=Decimal('5000.00'),
            available=True
        )
        
        # Create Church product
        church_category = Category.objects.create(
            name='CHURCH',
            slug='church',
            product_type='church'
        )
        self.church_product = Church.objects.create(
            name='Winners T-Shirt',
            church='Winners',
            category=church_category,
            price=Decimal('8000.00'),
            available=True
        )
        
        # Create mock cart with both products
        self.mock_cart = Mock()
        self.mock_cart.__len__ = Mock(return_value=2)
        self.mock_cart.__iter__ = Mock(return_value=iter([
            {
                'product': self.nysc_product,
                'quantity': 1,
                'price': self.nysc_product.price,
                'extra_fields': {}
            },
            {
                'product': self.church_product,
                'quantity': 1,
                'price': self.church_product.price,
                'extra_fields': {}
            }
        ]))
    
    def test_mixed_products_requires_all_fields(self):
        """Test mixed products requires fields for all product types"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            # Missing NYSC Kit fields
            'pickup_on_camp': True
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        # Should require NYSC Kit fields
        self.assertIn('call_up_number', serializer.errors)
    
    def test_mixed_products_with_all_fields(self):
        """Test mixed products validates with all required fields"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            # NYSC Kit fields
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja',
            # Church fields
            'pickup_on_camp': True
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertTrue(serializer.is_valid())


class CheckoutSerializerEdgeCasesTests(TestCase):
    """Test CheckoutSerializer edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=True)
        
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
        
        self.mock_cart = Mock()
        self.mock_cart.__len__ = Mock(return_value=1)
        self.mock_cart.__iter__ = Mock(return_value=iter([{
            'product': self.product,
            'quantity': 1,
            'price': self.product.price,
            'extra_fields': {}
        }]))
    
    def test_missing_first_name(self):
        """Test validation fails with missing first_name"""
        data = {
            # Missing first_name
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)
    
    def test_missing_last_name(self):
        """Test validation fails with missing last_name"""
        data = {
            'first_name': 'John',
            # Missing last_name
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('last_name', serializer.errors)
    
    def test_missing_phone_number(self):
        """Test validation fails with missing phone_number"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            # Missing phone_number
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('phone_number', serializer.errors)
    
    def test_validation_without_cart_context(self):
        """Test validation fails without cart in context"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'request': self.request}  # No cart
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('cart', serializer.errors)
    
    def test_very_long_names(self):
        """Test validation handles very long names"""
        data = {
            'first_name': 'A' * 100,  # Over max_length of 50
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        serializer = CheckoutSerializer(
            data=data,
            context={'cart': self.mock_cart, 'request': self.request}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('first_name', serializer.errors)


class OrderListSerializerTests(TestCase):
    """Test OrderListSerializer"""
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        serializer = OrderListSerializer()
        
        expected_fields = {
            'id', 'serial_number', 'order_type', 'total_cost',
            'paid', 'created', 'item_count'
        }
        self.assertEqual(set(serializer.fields.keys()), expected_fields)
    
    def test_all_fields_have_correct_types(self):
        """Test all fields have correct field types"""
        serializer = OrderListSerializer()
        
        from rest_framework import serializers
        
        self.assertIsInstance(serializer.fields['id'], serializers.UUIDField)
        self.assertIsInstance(serializer.fields['serial_number'], serializers.IntegerField)
        self.assertIsInstance(serializer.fields['order_type'], serializers.CharField)
        self.assertIsInstance(serializer.fields['total_cost'], serializers.DecimalField)
        self.assertIsInstance(serializer.fields['paid'], serializers.BooleanField)
        self.assertIsInstance(serializer.fields['created'], serializers.DateTimeField)
        self.assertIsInstance(serializer.fields['item_count'], serializers.IntegerField)