# cart/tests/tests_serializers.py
"""
Comprehensive tests for Cart Serializers

Coverage:
- CartItemSerializer (product serialization)
- AddToCartSerializer (validation logic for all product types)
- UpdateCartItemSerializer (quantity validation)
- CartSerializer (full cart serialization)
- ClearCartSerializer (empty serializer)
- Security: authentication requirements, measurement requirements
- Edge cases: invalid data, missing fields, boundary values
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from unittest.mock import Mock
from cart.serializers import (
    CartItemSerializer, AddToCartSerializer, UpdateCartItemSerializer,
    CartSerializer, ClearCartSerializer, VALID_VEST_SIZES, VALID_CHURCH_SIZES
)
from products.models import Category, NyscKit, NyscTour, Church
from measurement.models import Measurement
import uuid

User = get_user_model()


class CartItemSerializerTests(TestCase):
    """Test CartItemSerializer"""
    
    def setUp(self):
        # Create category
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        # Create product
        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_serialize_cart_item(self):
        """Test serializing a cart item"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'product': self.product,
            'quantity': 2,
            'price': Decimal("5000.00"),
            'total_price': Decimal("10000.00"),
            'extra_fields': {'size': 'free_size'},
            'item_key': 'test_key'
        }
        
        serializer = CartItemSerializer(data)
        result = serializer.data
        
        self.assertEqual(result['product_type'], 'nysc_kit')
        self.assertEqual(result['quantity'], 2)
        self.assertEqual(Decimal(result['price']), Decimal("5000.00"))
        self.assertIn('product', result)
    
    def test_get_product_for_nysc_kit(self):
        """Test get_product method returns NyscKit serialization"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'product': self.product,
            'quantity': 1,
            'price': Decimal("5000.00"),
            'total_price': Decimal("5000.00"),
            'extra_fields': {},
            'item_key': 'test_key'
        }
        
        serializer = CartItemSerializer(data)
        product_data = serializer.data['product']
        
        self.assertIsNotNone(product_data)
        self.assertEqual(product_data['name'], "Quality Nysc Cap")
    
    def test_get_product_for_different_types(self):
        """Test get_product works for all product types"""
        # Create categories and products for each type
        tour_category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        church_category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        
        tour = NyscTour.objects.create(
            name="Lagos",
            category=tour_category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        church = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=church_category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Test each type
        for product in [self.product, tour, church]:
            data = {
                'product': product,
                'product_type': product.product_type,
                'product_id': str(product.id),
                'quantity': 1,
                'price': product.price,
                'total_price': product.price,
                'extra_fields': {},
                'item_key': 'key'
            }
            serializer = CartItemSerializer(data)
            self.assertIsNotNone(serializer.data['product'])


class AddToCartSerializerBasicValidationTests(TestCase):
    """Test basic field validation for AddToCartSerializer"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create category and product
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=False)
    
    def test_valid_product_type_choices(self):
        """Test product_type must be one of valid choices"""
        valid_types = ['nysc_kit', 'nysc_tour', 'church']
        
        for ptype in valid_types:
            data = {
                'product_type': ptype,
                'product_id': str(uuid.uuid4()),
                'quantity': 1
            }
            serializer = AddToCartSerializer(data=data, context={'request': self.request})
            # Should not raise error for valid types
            serializer.is_valid()
    
    def test_invalid_product_type(self):
        """Test invalid product_type is rejected"""
        data = {
            'product_type': 'invalid_type',
            'product_id': str(uuid.uuid4()),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_type', serializer.errors)
    
    def test_quantity_minimum_value(self):
        """Test quantity must be at least 1"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 0
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)
    
    def test_negative_quantity(self):
        """Test negative quantity is rejected"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': -5
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)
    
    def test_invalid_uuid_format(self):
        """Test invalid UUID format is rejected"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': 'not-a-uuid',
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)
    
    def test_override_field_default_false(self):
        """Test override field defaults to False"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        serializer.is_valid()
        self.assertEqual(serializer.validated_data.get('override', False), False)


class AddToCartSerializerProductValidationTests(TestCase):
    """Test product existence and availability validation"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=False)
        
        # Create category
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        # Create products with different availability states
        self.available_product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.unavailable_product = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=False,
            out_of_stock=False
        )
        
        self.out_of_stock_product = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("7000.00"),
            available=True,
            out_of_stock=True
        )
    
    def test_nonexistent_product(self):
        """Test validation fails for non-existent product"""
        fake_uuid = str(uuid.uuid4())
        data = {
            'product_type': 'nysc_kit',
            'product_id': fake_uuid,
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)
        self.assertIn('not found', str(serializer.errors['product_id']).lower())
    
    def test_unavailable_product(self):
        """Test validation fails for unavailable product"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.unavailable_product.id),
            'quantity': 1,
            'size': 'M'  # Vest requires size
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)
        self.assertIn('not available', str(serializer.errors['product_id']).lower())
    
    def test_out_of_stock_product(self):
        """Test validation fails for out of stock product"""
        # Create authenticated user with measurement for kakhi
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Measurement.objects.create(
            user=user,
            chest=Decimal("40.00"),
            is_deleted=False
        )
        self.request.user = user
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.out_of_stock_product.id),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('product_id', serializer.errors)
        self.assertIn('not available', str(serializer.errors['product_id']).lower())
    
    def test_available_product_passes(self):
        """Test available product passes validation"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.available_product.id),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())


class AddToCartSerializerNyscKitValidationTests(TestCase):
    """Test NYSC Kit specific validation (Kakhi, Vest, Cap)"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create category
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        # Create products for each type
        self.kakhi = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("7000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.cap = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_kakhi_requires_authentication(self):
        """Test Kakhi purchase requires authenticated user"""
        request = self.factory.post('/')
        request.user = Mock(is_authenticated=False)
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('user', serializer.errors)
        self.assertIn('logged in', str(serializer.errors['user']).lower())
    
    def test_kakhi_requires_measurement(self):
        """Test Kakhi purchase requires user to have measurement"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        request = self.factory.post('/')
        request.user = user
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('measurement', serializer.errors)
        self.assertIn('measurement profile', str(serializer.errors['measurement']).lower())
    
    def test_kakhi_with_valid_measurement(self):
        """Test Kakhi purchase succeeds with valid measurement"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        measurement = Measurement.objects.create(
            user=user,
            chest=Decimal("40.00"),
            waist=Decimal("32.00"),
            is_deleted=False
        )
        
        request = self.factory.post('/')
        request.user = user
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        # Check extra_fields contains measurement info
        self.assertEqual(serializer.validated_data['extra_fields']['size'], 'measurement')
        self.assertEqual(
            serializer.validated_data['extra_fields']['measurement_id'],
            str(measurement.id)
        )
    
    def test_kakhi_ignores_deleted_measurement(self):
        """Test Kakhi validation ignores soft-deleted measurements"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create deleted measurement
        Measurement.objects.create(
            user=user,
            chest=Decimal("40.00"),
            is_deleted=True  # Soft deleted
        )
        
        request = self.factory.post('/')
        request.user = user
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('measurement', serializer.errors)
    
    def test_cap_auto_assigns_free_size(self):
        """Test Cap automatically gets free_size"""
        request = self.factory.post('/')
        request.user = Mock(is_authenticated=False)
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 1
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid())
        
        # Check free_size is auto-assigned
        self.assertEqual(serializer.validated_data['extra_fields']['size'], 'free_size')
    
    def test_vest_requires_size(self):
        """Test Vest requires size selection"""
        request = self.factory.post('/')
        request.user = Mock(is_authenticated=False)
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1
            # Missing size
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('size', serializer.errors)
    
    def test_vest_validates_size_against_valid_sizes(self):
        """Test Vest size must be from VALID_VEST_SIZES"""
        request = self.factory.post('/')
        request.user = Mock(is_authenticated=False)
        
        # Test invalid size
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'INVALID_SIZE'
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('size', serializer.errors)
    
    def test_vest_accepts_all_valid_sizes(self):
        """Test Vest accepts all sizes from VALID_VEST_SIZES"""
        request = self.factory.post('/')
        request.user = Mock(is_authenticated=False)
        
        for size in VALID_VEST_SIZES:
            data = {
                'product_type': 'nysc_kit',
                'product_id': str(self.vest.id),
                'quantity': 1,
                'size': size
            }
            
            serializer = AddToCartSerializer(data=data, context={'request': request})
            self.assertTrue(serializer.is_valid(), f"Size {size} should be valid")
            self.assertEqual(serializer.validated_data['extra_fields']['size'], size)


class AddToCartSerializerChurchValidationTests(TestCase):
    """Test Church product validation"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=False)
        
        # Create category and product
        self.category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        
        self.church_product = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=self.category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_church_requires_size(self):
        """Test Church product requires size"""
        data = {
            'product_type': 'church',
            'product_id': str(self.church_product.id),
            'quantity': 1
            # Missing size
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('size', serializer.errors)
    
    def test_church_validates_size(self):
        """Test Church size must be from VALID_CHURCH_SIZES"""
        data = {
            'product_type': 'church',
            'product_id': str(self.church_product.id),
            'quantity': 1,
            'size': 'INVALID'
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('size', serializer.errors)
    
    def test_church_accepts_all_valid_sizes(self):
        """Test Church accepts all sizes from VALID_CHURCH_SIZES"""
        for size in VALID_CHURCH_SIZES:
            data = {
                'product_type': 'church',
                'product_id': str(self.church_product.id),
                'quantity': 1,
                'size': size
            }
            
            serializer = AddToCartSerializer(data=data, context={'request': self.request})
            self.assertTrue(serializer.is_valid(), f"Size {size} should be valid")
    
    def test_church_custom_name_optional(self):
        """Test custom_name_text is optional for Church"""
        data = {
            'product_type': 'church',
            'product_id': str(self.church_product.id),
            'quantity': 1,
            'size': 'M'
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('custom_name_text', serializer.validated_data['extra_fields'])
    
    def test_church_with_custom_name(self):
        """Test Church accepts custom_name_text"""
        data = {
            'product_type': 'church',
            'product_id': str(self.church_product.id),
            'quantity': 1,
            'size': 'L',
            'custom_name_text': 'PASTOR JOHN'
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data['extra_fields']['custom_name_text'],
            'PASTOR JOHN'
        )


class AddToCartSerializerNyscTourValidationTests(TestCase):
    """Test NYSC Tour product validation"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=False)
        
        # Create category and product
        self.category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        
        self.tour_product = NyscTour.objects.create(
            name="Lagos",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_tour_requires_call_up_number(self):
        """Test NYSC Tour requires call_up_number"""
        data = {
            'product_type': 'nysc_tour',
            'product_id': str(self.tour_product.id),
            'quantity': 1
            # Missing call_up_number
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('call_up_number', serializer.errors)
    
    def test_tour_with_valid_call_up_number(self):
        """Test NYSC Tour accepts valid call_up_number"""
        data = {
            'product_type': 'nysc_tour',
            'product_id': str(self.tour_product.id),
            'quantity': 1,
            'call_up_number': 'AB/22C/1234'
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data['extra_fields']['call_up_number'],
            'AB/22C/1234'
        )
    
    def test_tour_accepts_various_call_up_formats(self):
        """Test NYSC Tour accepts different call-up number formats"""
        formats = [
            'AB/22C/1234',
            'LA/23A/5678',
            'KD/21B/9999',
        ]
        
        for call_up in formats:
            data = {
                'product_type': 'nysc_tour',
                'product_id': str(self.tour_product.id),
                'quantity': 1,
                'call_up_number': call_up
            }
            
            serializer = AddToCartSerializer(data=data, context={'request': self.request})
            self.assertTrue(serializer.is_valid(), f"Call-up {call_up} should be valid")


class UpdateCartItemSerializerTests(TestCase):
    """Test UpdateCartItemSerializer"""
    
    def test_valid_quantity(self):
        """Test valid quantity is accepted"""
        data = {'quantity': 5}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['quantity'], 5)
    
    def test_zero_quantity_allowed(self):
        """Test quantity of 0 is allowed (means remove)"""
        data = {'quantity': 0}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['quantity'], 0)
    
    def test_negative_quantity_rejected(self):
        """Test negative quantity is rejected"""
        data = {'quantity': -1}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('quantity', serializer.errors)
    
    def test_large_quantity(self):
        """Test very large quantity is accepted"""
        data = {'quantity': 10000}
        serializer = UpdateCartItemSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['quantity'], 10000)


class CartSerializerTests(TestCase):
    """Test CartSerializer"""
    
    def setUp(self):
        # Create categories
        self.kit_category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        self.tour_category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        
        # Create products
        self.cap = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.kit_category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.tour = NyscTour.objects.create(
            name="Lagos",
            category=self.tour_category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_serialize_cart(self):
        """Test serializing full cart"""
        cart_data = {
            'items': [
                {
                    'product': self.cap,
                    'product_type': 'nysc_kit',
                    'product_id': str(self.cap.id),
                    'quantity': 2,
                    'price': Decimal("5000.00"),
                    'total_price': Decimal("10000.00"),
                    'extra_fields': {},
                    'item_key': 'key1'
                },
                {
                    'product': self.tour,
                    'product_type': 'nysc_tour',
                    'product_id': str(self.tour.id),
                    'quantity': 1,
                    'price': Decimal("3000.00"),
                    'total_price': Decimal("3000.00"),
                    'extra_fields': {},
                    'item_key': 'key2'
                }
            ],
            'total_items': 3,
            'total_cost': Decimal("13000.00")
        }
        
        serializer = CartSerializer(cart_data)
        result = serializer.data
        
        self.assertEqual(result['total_items'], 3)
        self.assertEqual(Decimal(result['total_cost']), Decimal("13000.00"))
        self.assertEqual(len(result['items']), 2)
    
    def test_get_grouped_by_type(self):
        """Test grouping items by product type"""
        cart_data = {
            'items': [
                {
                    'product': self.cap,
                    'product_type': 'nysc_kit',
                    'product_id': str(self.cap.id),
                    'quantity': 2,
                    'price': Decimal("5000.00"),
                    'total_price': Decimal("10000.00"),
                    'extra_fields': {},
                    'item_key': 'key1'
                },
                {
                    'product': self.tour,
                    'product_type': 'nysc_tour',
                    'product_id': str(self.tour.id),
                    'quantity': 1,
                    'price': Decimal("3000.00"),
                    'total_price': Decimal("3000.00"),
                    'extra_fields': {},
                    'item_key': 'key2'
                }
            ],
            'total_items': 3,
            'total_cost': Decimal("13000.00")
        }
        
        serializer = CartSerializer(cart_data)
        grouped = serializer.data['grouped_by_type']
        
        self.assertIn('NyscKit', grouped)
        self.assertIn('NyscTour', grouped)
        self.assertEqual(len(grouped['NyscKit']), 1)
        self.assertEqual(len(grouped['NyscTour']), 1)


class ClearCartSerializerTests(TestCase):
    """Test ClearCartSerializer"""
    
    def test_empty_serializer(self):
        """Test ClearCartSerializer accepts no data"""
        serializer = ClearCartSerializer(data={})
        self.assertTrue(serializer.is_valid())
    
    def test_ignores_extra_data(self):
        """Test extra data is ignored"""
        serializer = ClearCartSerializer(data={'extra': 'data'})
        self.assertTrue(serializer.is_valid())


class AddToCartSerializerEdgeCasesTests(TestCase):
    """Test edge cases and boundary conditions"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.post('/')
        self.request.user = Mock(is_authenticated=False)
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_very_large_quantity(self):
        """Test very large quantity is accepted"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 999999
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
    
    def test_empty_string_size(self):
        """Test empty string size is treated as missing"""
        vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(vest.id),
            'quantity': 1,
            'size': ''  # Empty string
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('size', serializer.errors)
    
    def test_whitespace_only_call_up_number(self):
        """Test whitespace-only call_up_number is rejected"""
        tour_category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        tour = NyscTour.objects.create(
            name="Lagos",
            category=tour_category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        data = {
            'product_type': 'nysc_tour',
            'product_id': str(tour.id),
            'quantity': 1,
            'call_up_number': '   '  # Whitespace only
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        # Should fail validation - empty after strip
        self.assertFalse(serializer.is_valid())
    
    def test_unicode_in_custom_name(self):
        """Test unicode characters in custom_name_text"""
        church_category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        church = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=church_category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=False
        )
        
        data = {
            'product_type': 'church',
            'product_id': str(church.id),
            'quantity': 1,
            'size': 'M',
            'custom_name_text': '王牧师 PASTOR'  # Unicode characters
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data['extra_fields']['custom_name_text'],
            '王牧师 PASTOR'
        )
    
    def test_very_long_custom_name(self):
        """Test very long custom_name_text"""
        church_category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        church = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=church_category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=False
        )
        
        long_name = 'A' * 500
        data = {
            'product_type': 'church',
            'product_id': str(church.id),
            'quantity': 1,
            'size': 'L',
            'custom_name_text': long_name
        }
        
        serializer = AddToCartSerializer(data=data, context={'request': self.request})
        # Should accept long names (validation happens elsewhere if needed)
        self.assertTrue(serializer.is_valid())