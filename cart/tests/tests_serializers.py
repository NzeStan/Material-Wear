# cart/tests/tests_serializers.py
"""
Comprehensive tests for cart serializers
Tests validation, data transformation, and edge cases
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from products.models import Category, NyscKit, NyscTour, Church
from measurement.models import Measurement
from cart.serializers import (
    AddToCartSerializer, UpdateCartItemSerializer,
    CartItemSerializer, CartSerializer
)
import uuid

User = get_user_model()


class AddToCartSerializerTest(TestCase):
    """Test AddToCartSerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )
        
        self.kakhi = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )
        
        self.cap = NyscKit.objects.create(
            name='Quality Nysc Cap',
            type='cap',
            category=self.category,
            price=Decimal('1500.00'),
            available=True
        )
        
        self.tour = NyscTour.objects.create(
            name='Camp Tour',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )
        
        self.church_category = Category.objects.create(
            name='CHURCH',
            slug='church',
            product_type='church'
        )
        
        self.church = Church.objects.create(
            name='RCCG Shirt',
            church='RCCG',
            category=self.church_category,
            price=Decimal('3500.00'),
            available=True
        )

    def test_vest_serializer_valid_data(self):
        """Test serializer with valid vest data"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 2,
            'size': 'M'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['product'], self.vest)
        self.assertEqual(serializer.validated_data['extra_fields']['size'], 'M')

    def test_vest_serializer_missing_size(self):
        """Test serializer rejects vest without size"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('size', serializer.errors)

    def test_vest_serializer_invalid_size(self):
        """Test serializer rejects invalid vest size"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'INVALID_SIZE'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('size', serializer.errors)

    def test_kakhi_serializer_authenticated_with_measurement(self):
        """Test serializer accepts kakhi with measurement"""
        # Create measurement
        Measurement.objects.create(
            user=self.user,
            shoulder=Decimal('18.5'),
            chest=Decimal('42.0'),
            waist=Decimal('34.0'),
            hips=Decimal('40.0'),
            trouser_length=Decimal('42.0'),
            trouser_waist=Decimal('34.0'),
            shirt_length=Decimal('30.0'),
            sleeve=Decimal('24.0'),
            neck=Decimal('16.0'),
            cap=Decimal('22.5'),
            thigh=Decimal('24.0'),
            knee=Decimal('15.0')
        )
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['extra_fields']['size'], 'measurement')

    def test_kakhi_serializer_without_measurement(self):
        """Test serializer rejects kakhi without measurement"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)

    def test_kakhi_serializer_unauthenticated(self):
        """Test serializer rejects kakhi for anonymous users"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = None
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())

    def test_cap_serializer_auto_size(self):
        """Test serializer automatically sets cap size"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['extra_fields']['size'], 'free_size')

    def test_tour_serializer_with_call_up_number(self):
        """Test serializer accepts tour with call up number"""
        data = {
            'product_type': 'nysc_tour',
            'product_id': str(self.tour.id),
            'quantity': 1,
            'call_up_number': 'AB/22C/1234'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['extra_fields']['call_up_number'], 'AB/22C/1234')

    def test_tour_serializer_optional_call_up_number(self):
        """Test call up number is optional for tour"""
        data = {
            'product_type': 'nysc_tour',
            'product_id': str(self.tour.id),
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())

    def test_church_serializer_with_custom_text(self):
        """Test serializer accepts church with custom text"""
        data = {
            'product_type': 'church',
            'product_id': str(self.church.id),
            'quantity': 1,
            'size': 'XL',
            'custom_name_text': 'PASTOR JOHN'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['extra_fields']['custom_name_text'], 'PASTOR JOHN')

    def test_church_serializer_requires_size(self):
        """Test church requires size"""
        data = {
            'product_type': 'church',
            'product_id': str(self.church.id),
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('size', serializer.errors)

    def test_serializer_invalid_product_type(self):
        """Test serializer rejects invalid product type"""
        data = {
            'product_type': 'invalid_type',
            'product_id': str(uuid.uuid4()),
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_type', serializer.errors)

    def test_serializer_nonexistent_product(self):
        """Test serializer rejects nonexistent product"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(uuid.uuid4()),
            'quantity': 1,
            'size': 'M'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())

    def test_serializer_unavailable_product(self):
        """Test serializer rejects unavailable product"""
        self.vest.available = False
        self.vest.save()
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'M'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())

    def test_serializer_out_of_stock_product(self):
        """Test serializer rejects out of stock product"""
        self.vest.out_of_stock = True
        self.vest.save()
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'M'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())

    def test_serializer_zero_quantity(self):
        """Test serializer rejects zero quantity"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 0,
            'size': 'M'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)

    def test_serializer_negative_quantity(self):
        """Test serializer rejects negative quantity"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': -5,
            'size': 'M'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)

    def test_serializer_override_flag(self):
        """Test serializer accepts override flag"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 5,
            'size': 'M',
            'override': True
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.validated_data['override'])

    def test_serializer_default_override_false(self):
        """Test override defaults to False"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'M'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertTrue(serializer.is_valid())
        self.assertFalse(serializer.validated_data['override'])

    def test_serializer_missing_required_fields(self):
        """Test serializer requires essential fields"""
        data = {
            'product_type': 'nysc_kit',
            'quantity': 1
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)


class UpdateCartItemSerializerTest(TestCase):
    """Test UpdateCartItemSerializer"""

    def test_valid_quantity_update(self):
        """Test serializer with valid quantity"""
        data = {'quantity': 5}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['quantity'], 5)

    def test_zero_quantity(self):
        """Test serializer accepts zero (for removal)"""
        data = {'quantity': 0}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['quantity'], 0)

    def test_negative_quantity(self):
        """Test serializer rejects negative quantity"""
        data = {'quantity': -5}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)

    def test_missing_quantity(self):
        """Test serializer requires quantity"""
        data = {}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)

    def test_non_integer_quantity(self):
        """Test serializer rejects non-integer quantity"""
        data = {'quantity': 'not_a_number'}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())

    def test_float_quantity(self):
        """Test serializer handles float quantity"""
        data = {'quantity': 5.5}
        serializer = UpdateCartItemSerializer(data=data)
        
        # Should either accept and convert or reject
        if serializer.is_valid():
            self.assertIsInstance(serializer.validated_data['quantity'], int)


class CartItemSerializerTest(TestCase):
    """Test CartItemSerializer"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_serializer_output(self):
        """Test serializer output structure"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'product': self.vest,
            'quantity': 2,
            'price': Decimal('2000.00'),
            'extra_fields': {'size': 'M'}
        }
        
        serializer = CartItemSerializer(data)
        output = serializer.data
        
        self.assertEqual(output['product_type'], 'nysc_kit')
        self.assertEqual(output['product_id'], str(self.vest.id))
        self.assertEqual(output['quantity'], 2)
        self.assertEqual(Decimal(output['price']), Decimal('2000.00'))
        self.assertIn('product', output)

    def test_serializer_product_details(self):
        """Test serializer includes product details"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'product': self.vest,
            'quantity': 1,
            'price': Decimal('2000.00'),
            'extra_fields': {}
        }
        
        serializer = CartItemSerializer(data)
        output = serializer.data
        
        product_data = output['product']
        self.assertEqual(product_data['name'], self.vest.name)
        self.assertEqual(Decimal(product_data['price']), self.vest.price)


class CartSerializerTest(TestCase):
    """Test CartSerializer"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )
        
        self.tour = NyscTour.objects.create(
            name='Camp Tour',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )

    def test_empty_cart_serialization(self):
        """Test serializing empty cart"""
        data = {
            'items': [],
            'total_items': 0,
            'total_cost': Decimal('0'),
            'grouped_by_type': {}
        }
        
        serializer = CartSerializer(data)
        output = serializer.data
        
        self.assertEqual(len(output['items']), 0)
        self.assertEqual(output['total_items'], 0)
        self.assertEqual(Decimal(output['total_cost']), Decimal('0'))

    def test_cart_with_items_serialization(self):
        """Test serializing cart with items"""
        items = [
            {
                'product_type': 'nysc_kit',
                'product_id': str(self.vest.id),
                'product': self.vest,
                'quantity': 2,
                'price': Decimal('2000.00'),
                'total_price': Decimal('4000.00'),
                'extra_fields': {'size': 'M'},
                'item_key': 'test_key_1'
            },
            {
                'product_type': 'nysc_tour',
                'product_id': str(self.tour.id),
                'product': self.tour,
                'quantity': 1,
                'price': Decimal('5000.00'),
                'total_price': Decimal('5000.00'),
                'extra_fields': {'call_up_number': 'AB/22C/1234'},
                'item_key': 'test_key_2'
            }
        ]
        
        data = {
            'items': items,
            'total_items': 3,
            'total_cost': Decimal('9000.00'),
            'grouped_by_type': {
                'NyscKit': [items[0]],
                'NyscTour': [items[1]]
            }
        }
        
        serializer = CartSerializer(data)
        output = serializer.data
        
        self.assertEqual(len(output['items']), 2)
        self.assertEqual(output['total_items'], 3)
        self.assertEqual(Decimal(output['total_cost']), Decimal('9000.00'))


class SerializerEdgeCasesTest(TestCase):
    """Test edge cases and error scenarios"""

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_serializer_with_very_long_custom_text(self):
        """Test serializer handles very long custom text"""
        church_category = Category.objects.create(
            name='CHURCH',
            slug='church',
            product_type='church'
        )
        
        church = Church.objects.create(
            name='RCCG Shirt',
            church='RCCG',
            category=church_category,
            price=Decimal('3500.00'),
            available=True
        )
        
        data = {
            'product_type': 'church',
            'product_id': str(church.id),
            'quantity': 1,
            'size': 'XL',
            'custom_name_text': 'A' * 1000  # Very long text
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        # Should either truncate or reject
        if serializer.is_valid():
            text = serializer.validated_data['extra_fields'].get('custom_name_text', '')
            self.assertLessEqual(len(text), 500)  # Assuming max length

    def test_serializer_with_special_characters(self):
        """Test serializer handles special characters in fields"""
        data = {
            'product_type': 'nysc_tour',
            'product_id': str(NyscTour.objects.create(
                name='Tour',
                category=self.category,
                price=Decimal('5000.00')
            ).id),
            'quantity': 1,
            'call_up_number': 'AB/22C/1234!@#$%'
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        # Should handle gracefully
        is_valid = serializer.is_valid()
        self.assertIsInstance(is_valid, bool)

    def test_serializer_without_request_context(self):
        """Test serializer behavior without request context"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'M'
        }
        
        serializer = AddToCartSerializer(data=data)
        
        # Should handle missing context gracefully
        # May be invalid due to missing user context
        is_valid = serializer.is_valid()
        self.assertIsInstance(is_valid, bool)

    def test_serializer_with_empty_strings(self):
        """Test serializer handles empty string values"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': ''  # Empty string
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        self.assertFalse(serializer.is_valid())

    def test_serializer_with_null_values(self):
        """Test serializer handles null values"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': None
        }
        
        request = self.factory.post('/')
        request.user = self.user
        serializer = AddToCartSerializer(data=data, context={'request': request})
        
        # Should reject None for required fields
        self.assertFalse(serializer.is_valid())