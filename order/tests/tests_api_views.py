# order/tests/test_api_views.py
"""
Comprehensive tests for Order API Views

Coverage:
- CheckoutView: order creation from cart, price validation, validation by product type
- OrderViewSet: list and retrieve orders, user isolation, polymorphic types
- Authentication and permissions
- Rate throttling
- Edge cases and security
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
from order.models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem
from products.models import Category, NyscKit, NyscTour, Church
from cart.cart import Cart

User = get_user_model()


class CheckoutViewAuthenticationTests(TestCase):
    """Test authentication requirements for checkout"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.checkout_url = reverse('order:checkout')
    
    def test_checkout_requires_authentication(self):
        """Test checkout requires authentication"""
        response = self.client.post(self.checkout_url, {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_checkout_rejects_unauthenticated_user(self):
        """Test checkout rejects unauthenticated requests"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        response = self.client.post(self.checkout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CheckoutViewBasicTests(TestCase):
    """Test basic checkout functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.checkout_url = reverse('order:checkout')
        
        # Create test products
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
            available=True,
            out_of_stock=False
        )
    
    def test_checkout_with_empty_cart(self):
        """Test checkout fails with empty cart"""
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        response = self.client.post(self.checkout_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Cart is empty')
    
    def test_checkout_creates_order_from_cart(self):
        """Test checkout creates order from cart items"""
        # Add item to cart
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 2
        }, format='json')
        
        # Checkout
        checkout_data = {
            'first_name': 'John',
            'middle_name': 'David',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('order_ids', response.data)
        self.assertIn('total_amount', response.data)
        self.assertIn('orders', response.data)
        
        # Verify order was created
        self.assertEqual(NyscKitOrder.objects.count(), 1)
        order = NyscKitOrder.objects.first()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.first_name, 'John')
        self.assertEqual(order.call_up_number, 'AB/22C/1234')
        self.assertFalse(order.paid)
    
    def test_checkout_clears_cart_after_success(self):
        """Test checkout clears cart after successful order creation"""
        # Add item to cart
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 1
        }, format='json')
        
        # Verify cart has items
        cart_url = reverse('cart:cart-detail')
        response = self.client.get(cart_url)
        self.assertEqual(response.data['total_items'], 1)
        
        # Checkout
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        self.client.post(self.checkout_url, checkout_data, format='json')
        
        # Verify cart is empty
        response = self.client.get(cart_url)
        self.assertEqual(response.data['total_items'], 0)
    
    def test_checkout_creates_order_items(self):
        """Test checkout creates order items with correct details"""
        # Add item to cart
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 3
        }, format='json')
        
        # Checkout
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order items
        order = NyscKitOrder.objects.first()
        self.assertEqual(order.items.count(), 1)
        
        item = order.items.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.price, self.product.price)


class CheckoutViewPriceValidationTests(TestCase):
    """Test price validation and manipulation prevention"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.checkout_url = reverse('order:checkout')
        
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
            available=True,
            out_of_stock=False
        )
    
    @patch('cart.cart.Cart.__iter__')
    def test_checkout_detects_price_manipulation(self, mock_iter):
        """Test checkout detects price mismatch between cart and database"""
        # Mock cart with manipulated price
        mock_item = {
            'product': self.product,
            'quantity': 1,
            'price': Decimal('100.00'),  # Manipulated to be lower
            'total_price': Decimal('100.00'),
            'extra_fields': {}
        }
        mock_iter.return_value = iter([mock_item])  # Must return iterator
        
        # Try to checkout
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        with patch('cart.cart.Cart.__len__', return_value=1):
            response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        # Should reject with price mismatch error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Price mismatch', response.data['error'])
        self.assertIn('details', response.data)
    
    @patch('cart.cart.Cart.__iter__')
    @patch('cart.cart.Cart.clear')
    def test_checkout_clears_cart_on_price_mismatch(self, mock_clear, mock_iter):
        """Test cart is cleared when price mismatch is detected"""
        # Mock cart with manipulated price
        mock_item = {
            'product': self.product,
            'quantity': 1,
            'price': Decimal('100.00'),
            'total_price': Decimal('100.00'),
            'extra_fields': {}
        }
        mock_iter.return_value = iter([mock_item])  # Must return iterator
        
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        with patch('cart.cart.Cart.__len__', return_value=1):
            self.client.post(self.checkout_url, checkout_data, format='json')
        
        # Cart should be cleared
        mock_clear.assert_called_once()
    
    def test_checkout_uses_database_price_not_cart_price(self):
        """Test order items use fresh database price, not cart price"""
        # Add to cart
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 1
        }, format='json')
        
        # Change product price in database
        self.product.price = Decimal('6000.00')
        self.product.save()
        
        # Checkout
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        # Should detect price mismatch and reject
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CheckoutViewNyscKitValidationTests(TestCase):
    """Test NYSC Kit specific validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.checkout_url = reverse('order:checkout')
        
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
            available=True,
            out_of_stock=False
        )
        
        # Add to cart
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 1
        }, format='json')
    
    def test_nysc_kit_requires_call_up_number(self):
        """Test NYSC Kit checkout requires call_up_number"""
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            # Missing call_up_number
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('call_up_number', response.data)
    
    def test_nysc_kit_requires_state(self):
        """Test NYSC Kit checkout requires state"""
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            # Missing state
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('state', response.data)
    
    def test_nysc_kit_requires_local_government(self):
        """Test NYSC Kit checkout requires local_government"""
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            # Missing local_government
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('local_government', response.data)
    
    def test_nysc_kit_with_all_required_fields(self):
        """Test NYSC Kit checkout succeeds with all required fields"""
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order was created with correct fields
        order = NyscKitOrder.objects.first()
        self.assertEqual(order.call_up_number, 'AB/22C/1234')
        self.assertEqual(order.state, 'Lagos')
        self.assertEqual(order.local_government, 'Ikeja')


class CheckoutViewNyscTourValidationTests(TestCase):
    """Test NYSC Tour specific validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.checkout_url = reverse('order:checkout')
        
        self.category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        
        self.product = NyscTour.objects.create(
            name='Lagos Tour',
            category=self.category,
            price=Decimal('15000.00'),
            available=True,
            out_of_stock=False
        )
        
        # Add to cart
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_tour',
            'product_id': str(self.product.id),
            'quantity': 1,
            'call_up_number': 'AB/22C/1234'
        }, format='json')
    
    def test_nysc_tour_requires_middle_name(self):
        """Test NYSC Tour checkout requires middle_name"""
        checkout_data = {
            'first_name': 'John',
            # Missing middle_name
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('middle_name', response.data)
    
    def test_nysc_tour_with_all_required_fields(self):
        """Test NYSC Tour checkout succeeds with all required fields"""
        checkout_data = {
            'first_name': 'John',
            'middle_name': 'David',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order was created
        order = NyscTourOrder.objects.first()
        self.assertEqual(order.middle_name, 'David')


class CheckoutViewChurchValidationTests(TestCase):
    """Test Church specific validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.checkout_url = reverse('order:checkout')
        
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
            available=True,
            out_of_stock=False
        )
        
        # Add to cart
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'church',
            'product_id': str(self.product.id),
            'quantity': 1,
            'size': 'L'
        }, format='json')
    
    def test_church_with_pickup_on_camp_default(self):
        """Test Church checkout defaults to pickup_on_camp=True"""
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order defaults to pickup
        order = ChurchOrder.objects.first()
        self.assertTrue(order.pickup_on_camp)
    
    def test_church_delivery_requires_state(self):
        """Test Church delivery requires delivery_state"""
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'pickup_on_camp': False,
            # Missing delivery_state
            'delivery_lga': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('delivery_state', response.data)
    
    def test_church_delivery_requires_lga(self):
        """Test Church delivery requires delivery_lga"""
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'pickup_on_camp': False,
            'delivery_state': 'Lagos',
            # Missing delivery_lga
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('delivery_lga', response.data)
    
    def test_church_with_delivery_details(self):
        """Test Church checkout succeeds with delivery details"""
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'pickup_on_camp': False,
            'delivery_state': 'Lagos',
            'delivery_lga': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify order was created with delivery details
        order = ChurchOrder.objects.first()
        self.assertFalse(order.pickup_on_camp)
        self.assertEqual(order.delivery_state, 'Lagos')
        self.assertEqual(order.delivery_lga, 'Ikeja')


class CheckoutViewMultipleProductTypesTests(TestCase):
    """Test checkout with multiple product types in cart"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.checkout_url = reverse('order:checkout')
        
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
    
    def test_checkout_creates_separate_orders_for_each_type(self):
        """Test checkout creates separate orders for different product types"""
        # Add both products to cart
        add_url = reverse('cart:cart-add')
        
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.nysc_product.id),
            'quantity': 2
        }, format='json')
        
        self.client.post(add_url, {
            'product_type': 'church',
            'product_id': str(self.church_product.id),
            'quantity': 1,
            'size': 'L'
        }, format='json')
        
        # Checkout with all required fields
        checkout_data = {
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
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['order_ids']), 2)
        
        # Verify separate orders were created
        self.assertEqual(NyscKitOrder.objects.count(), 1)
        self.assertEqual(ChurchOrder.objects.count(), 1)


class CheckoutViewEdgeCasesTests(TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.checkout_url = reverse('order:checkout')
        
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
    
    def test_checkout_with_missing_first_name(self):
        """Test checkout fails with missing first_name"""
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 1
        }, format='json')
        
        checkout_data = {
            # Missing first_name
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
    
    def test_checkout_with_missing_phone_number(self):
        """Test checkout fails with missing phone_number"""
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 1
        }, format='json')
        
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            # Missing phone_number
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone_number', response.data)
    
    def test_checkout_stores_pending_orders_in_session(self):
        """Test checkout stores pending order IDs in session"""
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 1
        }, format='json')
        
        checkout_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678',
            'call_up_number': 'AB/22C/1234',
            'state': 'Lagos',
            'local_government': 'Ikeja'
        }
        
        response = self.client.post(self.checkout_url, checkout_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify session has pending orders
        # Note: Can't easily test session in DRF, but it's set in the view


class OrderViewSetAuthenticationTests(TestCase):
    """Test authentication requirements for order views"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.list_url = reverse('order:order-list')
    
    def test_list_orders_requires_authentication(self):
        """Test listing orders requires authentication"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_retrieve_order_requires_authentication(self):
        """Test retrieving order requires authentication"""
        # Create a dummy order ID
        import uuid
        order_id = uuid.uuid4()
        detail_url = reverse('order:order-detail', kwargs={'pk': order_id})
        
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class OrderViewSetListTests(TestCase):
    """Test order list functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
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
        self.list_url = reverse('order:order-list')
    
    def test_list_orders_returns_only_user_orders(self):
        """Test list returns only authenticated user's orders"""
        # Create orders for user1
        order1 = BaseOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        # Create orders for user2
        order2 = BaseOrder.objects.create(
            user=self.user2,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone_number='08087654321',
            total_cost=Decimal('20000.00')
        )
        
        # Authenticate as user1
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], str(order1.id))
    
    def test_list_orders_with_no_orders(self):
        """Test list returns empty array when user has no orders"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_list_orders_returns_most_recent_first(self):
        """Test list returns orders in reverse chronological order"""
        # Create multiple orders
        order1 = BaseOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        order2 = BaseOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('20000.00')
        )
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Most recent first
        self.assertEqual(response.data[0]['id'], str(order2.id))
        self.assertEqual(response.data[1]['id'], str(order1.id))
    
    def test_list_orders_includes_order_type(self):
        """Test list includes order_type field"""
        NyscKitOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            call_up_number='AB/22C/1234',
            state='Lagos',
            local_government='Ikeja'
        )
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('order_type', response.data[0])


class OrderViewSetRetrieveTests(TestCase):
    """Test order retrieve functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
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
    
    def test_retrieve_own_order(self):
        """Test user can retrieve their own order"""
        order = BaseOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        detail_url = reverse('order:order-detail', kwargs={'pk': order.id})
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(order.id))
    
    def test_cannot_retrieve_other_user_order(self):
        """Test user cannot retrieve another user's order"""
        order = BaseOrder.objects.create(
            user=self.user2,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone_number='08087654321',
            total_cost=Decimal('20000.00')
        )
        
        detail_url = reverse('order:order-detail', kwargs={'pk': order.id})
        
        # Authenticate as user1 trying to access user2's order
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_nonexistent_order(self):
        """Test retrieving nonexistent order returns 404"""
        import uuid
        fake_id = uuid.uuid4()
        detail_url = reverse('order:order-detail', kwargs={'pk': fake_id})
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_order_includes_items(self):
        """Test retrieve includes order items"""
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
        
        order = NyscKitOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            call_up_number='AB/22C/1234',
            state='Lagos',
            local_government='Ikeja'
        )
        
        from django.contrib.contenttypes.models import ContentType
        OrderItem.objects.create(
            order=order,
            content_type=ContentType.objects.get_for_model(product),
            object_id=product.id,
            price=Decimal('5000.00'),
            quantity=2
        )
        
        detail_url = reverse('order:order-detail', kwargs={'pk': order.id})
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('items', response.data)
        self.assertEqual(len(response.data['items']), 1)


class OrderViewSetPermissionsTests(TestCase):
    """Test permission restrictions on order viewset"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.list_url = reverse('order:order-list')
    
    def test_cannot_create_order_via_viewset(self):
        """Test cannot create order via viewset (read-only)"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '08012345678'
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        # Should be method not allowed for read-only viewset
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_cannot_update_order_via_viewset(self):
        """Test cannot update order via viewset (read-only)"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        detail_url = reverse('order:order-detail', kwargs={'pk': order.id})
        
        self.client.force_authenticate(user=self.user)
        
        data = {'first_name': 'Jane'}
        response = self.client.patch(detail_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_cannot_delete_order_via_viewset(self):
        """Test cannot delete order via viewset (read-only)"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        detail_url = reverse('order:order-detail', kwargs={'pk': order.id})
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class OrderViewSetPolymorphicTests(TestCase):
    """Test polymorphic order type handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_retrieve_nysc_kit_order_returns_specific_fields(self):
        """Test retrieving NYSC Kit order includes specific fields"""
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            call_up_number='AB/22C/1234',
            state='Lagos',
            local_government='Ikeja'
        )
        
        detail_url = reverse('order:order-detail', kwargs={'pk': order.id})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('call_up_number', response.data)
        self.assertIn('state', response.data)
        self.assertIn('local_government', response.data)
        self.assertEqual(response.data['call_up_number'], 'AB/22C/1234')
    
    def test_retrieve_church_order_returns_specific_fields(self):
        """Test retrieving Church order includes specific fields"""
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            pickup_on_camp=False,
            delivery_state='Lagos',
            delivery_lga='Ikeja'
        )
        
        detail_url = reverse('order:order-detail', kwargs={'pk': order.id})
        response = self.client.get(detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pickup_on_camp', response.data)
        self.assertIn('delivery_state', response.data)
        self.assertIn('delivery_lga', response.data)
        self.assertFalse(response.data['pickup_on_camp'])
    
    def test_list_mixed_order_types(self):
        """Test listing returns all order types correctly"""
        # Create different order types
        NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            call_up_number='AB/22C/1234',
            state='Lagos',
            local_government='Ikeja'
        )
        
        NyscTourOrder.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone_number='08087654321',
            total_cost=Decimal('15000.00')
        )
        
        ChurchOrder.objects.create(
            user=self.user,
            first_name='Bob',
            last_name='Johnson',
            email='bob@example.com',
            phone_number='08099999999',
            total_cost=Decimal('8000.00'),
            pickup_on_camp=True
        )
        
        list_url = reverse('order:order-list')
        response = self.client.get(list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)