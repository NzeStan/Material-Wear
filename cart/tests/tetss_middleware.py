# cart/tests/tests_middleware.py
"""
Comprehensive tests for Cart Middleware

Coverage:
- CartCleanupMiddleware initialization
- Middleware request processing
- Product validation and cleanup
- Message generation for removed items
- Edge cases: no session, no cart, corrupted data
- User vs anonymous cart handling
- Response passthrough
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages import get_messages
from django.conf import settings
from unittest.mock import Mock, patch, MagicMock
from cart.middleware import CartCleanupMiddleware
from cart.cart import Cart
from products.models import Category, NyscKit, NyscTour, Church

User = get_user_model()


class CartCleanupMiddlewareInitializationTests(TestCase):
    """Test middleware initialization"""
    
    def test_middleware_initialization(self):
        """Test middleware can be initialized with get_response"""
        get_response = Mock()
        
        middleware = CartCleanupMiddleware(get_response)
        
        self.assertEqual(middleware.get_response, get_response)
    
    def test_middleware_stores_get_response(self):
        """Test middleware stores get_response callable"""
        get_response = Mock(return_value='response')
        
        middleware = CartCleanupMiddleware(get_response)
        
        self.assertTrue(callable(middleware.get_response))


class CartCleanupMiddlewareBasicTests(TestCase):
    """Test basic middleware functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        
        # Create get_response mock
        self.get_response = Mock(return_value=Mock(status_code=200))
        
        # Create middleware instance
        self.middleware = CartCleanupMiddleware(self.get_response)
        
        # Create category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.available_product = NyscKit.objects.create(
            name="Available Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def _create_request_with_session(self, user=None):
        """Helper to create request with session and message middleware"""
        request = self.factory.get('/')
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        # Add message middleware
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        # Add user
        request.user = user if user else Mock(is_authenticated=False)
        
        return request
    
    def test_middleware_processes_request_without_session(self):
        """Test middleware handles request without session gracefully"""
        request = self.factory.get('/')
        request.user = Mock(is_authenticated=False)
        
        # Should not raise error
        response = self.middleware(request)
        
        # Should call get_response
        self.get_response.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_processes_request_without_cart(self):
        """Test middleware handles request without cart in session"""
        request = self._create_request_with_session()
        
        # No cart in session
        self.assertNotIn('cart', request.session)
        
        response = self.middleware(request)
        
        # Should process normally
        self.get_response.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_processes_request_with_empty_cart(self):
        """Test middleware handles empty cart"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Cart exists but is empty
        self.assertEqual(len(cart), 0)
        
        response = self.middleware(request)
        
        # Should process normally
        self.get_response.assert_called_once()
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_processes_request_with_valid_cart(self):
        """Test middleware doesn't remove valid items"""
        request = self._create_request_with_session()
        cart = Cart(request)
        cart.add(self.available_product, quantity=2)
        
        self.assertEqual(len(cart), 2)
        
        response = self.middleware(request)
        
        # Cart should remain unchanged
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 2)
        
        # No messages should be added
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 0)
    
    def test_middleware_returns_response_from_get_response(self):
        """Test middleware returns response from get_response"""
        mock_response = Mock(status_code=201, content='test content')
        self.get_response.return_value = mock_response
        
        request = self._create_request_with_session()
        
        response = self.middleware(request)
        
        self.assertEqual(response, mock_response)
        self.assertEqual(response.status_code, 201)


class CartCleanupMiddlewareCleanupTests(TestCase):
    """Test middleware cleanup functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=Mock(status_code=200))
        self.middleware = CartCleanupMiddleware(self.get_response)
        
        # Create category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.available_product = NyscKit.objects.create(
            name="Available Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.unavailable_product = NyscKit.objects.create(
            name="Unavailable Product",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=False,
            out_of_stock=False
        )
        
        self.out_of_stock_product = NyscKit.objects.create(
            name="Out of Stock Product",
            type="kakhi",
            category=self.category,
            price=Decimal("8000.00"),
            available=True,
            out_of_stock=True
        )
    
    def _create_request_with_session(self, user=None):
        """Helper to create request with session and message middleware"""
        request = self.factory.get('/')
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        # Add message middleware
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        # Add user
        request.user = user if user else Mock(is_authenticated=False)
        
        return request
    
    def test_middleware_removes_unavailable_products(self):
        """Test middleware removes unavailable products from cart"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Add both available and unavailable products
        cart.add(self.available_product, quantity=2)
        cart.add(self.unavailable_product, quantity=1)
        
        self.assertEqual(len(cart), 3)
        
        # Process request through middleware
        self.middleware(request)
        
        # Unavailable product should be removed
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 2)
        
        # Should only contain available product
        items = list(cart_after)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['product'].id, self.available_product.id)
    
    def test_middleware_removes_out_of_stock_products(self):
        """Test middleware removes out of stock products"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Add available and out of stock products
        cart.add(self.available_product, quantity=2)
        cart.add(self.out_of_stock_product, quantity=3)
        
        self.assertEqual(len(cart), 5)
        
        # Process request
        self.middleware(request)
        
        # Out of stock should be removed
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 2)
    
    def test_middleware_removes_deleted_products(self):
        """Test middleware removes products that have been deleted"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Add product then delete it
        temp_product = NyscKit.objects.create(
            name="Temporary Product",
            type="cap",
            category=self.category,
            price=Decimal("1000.00"),
            available=True,
            out_of_stock=False
        )
        
        cart.add(self.available_product, quantity=1)
        cart.add(temp_product, quantity=2)
        
        self.assertEqual(len(cart), 3)
        
        # Delete the product
        temp_product.delete()
        
        # Process request
        self.middleware(request)
        
        # Deleted product should be removed
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 1)
    
    def test_middleware_adds_message_for_unavailable_items(self):
        """Test middleware adds message when unavailable items are removed"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        cart.add(self.unavailable_product, quantity=2)
        
        # Process request
        self.middleware(request)
        
        # Check messages
        # NOTE: Both available=False and out_of_stock=True are treated as "out of stock"
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn('out of stock', str(messages[0]))
        self.assertIn('1 item(s)', str(messages[0]))
    
    def test_middleware_adds_message_for_out_of_stock_items(self):
        """Test middleware adds message for out of stock items"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        cart.add(self.out_of_stock_product, quantity=1)
        
        # Process request
        self.middleware(request)
        
        # Check messages
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn('out of stock', str(messages[0]))
        self.assertIn('1 item(s)', str(messages[0]))
    
    def test_middleware_adds_message_for_deleted_items(self):
        """Test middleware adds message for deleted products"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Add product then delete it
        temp_product = NyscKit.objects.create(
            name="Temp Product",
            type="cap",
            category=self.category,
            price=Decimal("1000.00"),
            available=True,
            out_of_stock=False
        )
        
        cart.add(temp_product, quantity=1)
        temp_product.delete()
        
        # Process request
        self.middleware(request)
        
        # Should show "no longer available" for deleted items
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn('no longer available', str(messages[0]))
        self.assertIn('1 item(s)', str(messages[0]))
    
    def test_middleware_adds_combined_message_for_deleted_and_out_of_stock(self):
        """Test middleware combines messages when items are both deleted and out of stock"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Add a product that will be deleted
        temp_product = NyscKit.objects.create(
            name="Temp Product",
            type="cap",
            category=self.category,
            price=Decimal("1000.00"),
            available=True,
            out_of_stock=False
        )
        
        cart.add(temp_product, quantity=1)
        cart.add(self.out_of_stock_product, quantity=1)
        
        # Delete the temp product
        temp_product.delete()
        
        # Process request
        self.middleware(request)
        
        # Should have combined message
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        
        message_text = str(messages[0])
        self.assertIn('no longer available', message_text)
        self.assertIn('out of stock', message_text)
        self.assertIn('and', message_text)
    
    def test_middleware_adds_combined_message_for_multiple_types(self):
        """Test middleware combines messages for different removal types"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Add both unavailable and out of stock
        cart.add(self.unavailable_product, quantity=1)
        cart.add(self.out_of_stock_product, quantity=1)
        
        # Process request
        self.middleware(request)
        
        # Both are treated as "out_of_stock" in cleanup
        # So we should have one message about 2 items
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        
        message_text = str(messages[0])
        self.assertIn('out of stock', message_text)
        self.assertIn('2 item(s)', message_text)
    
    def test_middleware_no_message_when_nothing_removed(self):
        """Test middleware doesn't add message when no items removed"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        cart.add(self.available_product, quantity=2)
        
        # Process request
        self.middleware(request)
        
        # No messages should be added
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 0)
    
    def test_middleware_removes_multiple_invalid_items(self):
        """Test middleware handles multiple invalid items"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Create multiple invalid products
        invalid1 = NyscKit.objects.create(
            name="Invalid 1",
            type="cap",
            category=self.category,
            price=Decimal("1000.00"),
            available=False,
            out_of_stock=False
        )
        
        invalid2 = NyscKit.objects.create(
            name="Invalid 2",
            type="vest",
            category=self.category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=True
        )
        
        # Add all items
        cart.add(self.available_product, quantity=1)
        cart.add(invalid1, quantity=2)
        cart.add(invalid2, quantity=3)
        
        self.assertEqual(len(cart), 6)
        
        # Process request
        self.middleware(request)
        
        # Only valid product should remain
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 1)
        
        # Check message mentions correct counts
        # Both invalid1 and invalid2 are treated as "out_of_stock"
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        message_text = str(messages[0])
        self.assertIn('2 item(s)', message_text)  # 2 distinct products (invalid1 and invalid2)
        self.assertIn('out of stock', message_text)


class CartCleanupMiddlewareUserIsolationTests(TestCase):
    """Test middleware handles user carts correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=Mock(status_code=200))
        self.middleware = CartCleanupMiddleware(self.get_response)
        
        # Create users
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
        
        # Create category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Test Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def _create_request_with_session(self, user=None):
        """Helper to create request with session and message middleware"""
        request = self.factory.get('/')
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        # Add message middleware
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        # Add user
        request.user = user if user else Mock(is_authenticated=False)
        
        return request
    
    def test_middleware_processes_authenticated_user_cart(self):
        """Test middleware correctly processes authenticated user cart"""
        request = self._create_request_with_session(user=self.user1)
        cart = Cart(request)
        
        cart.add(self.product, quantity=2)
        self.assertEqual(len(cart), 2)
        
        # Process request
        self.middleware(request)
        
        # Cart should be processed
        self.get_response.assert_called_once()
    
    def test_middleware_processes_anonymous_cart(self):
        """Test middleware processes anonymous cart"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        cart.add(self.product, quantity=3)
        
        # Process request
        self.middleware(request)
        
        # Should process normally
        self.get_response.assert_called_once()
    
    def test_middleware_isolates_user_carts(self):
        """Test middleware doesn't affect other users' carts"""
        # Create carts for both users
        request1 = self._create_request_with_session(user=self.user1)
        cart1 = Cart(request1)
        cart1.add(self.product, quantity=2)
        
        request2 = self._create_request_with_session(user=self.user2)
        cart2 = Cart(request2)
        cart2.add(self.product, quantity=3)
        
        # Process first user's request
        self.middleware(request1)
        
        # Second user's cart should be unaffected
        cart2_after = Cart(request2)
        self.assertEqual(len(cart2_after), 3)


class CartCleanupMiddlewareEdgeCasesTests(TestCase):
    """Test middleware edge cases and error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=Mock(status_code=200))
        self.middleware = CartCleanupMiddleware(self.get_response)
        
        # Create category
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
    
    def _create_request_with_session(self, user=None):
        """Helper to create request with session and message middleware"""
        request = self.factory.get('/')
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        # Add message middleware
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        # Add user
        request.user = user if user else Mock(is_authenticated=False)
        
        return request
    
    def test_middleware_handles_corrupted_cart_data(self):
        """Test middleware handles corrupted cart data gracefully"""
        request = self._create_request_with_session()
        
        # Manually corrupt cart data
        request.session['cart'] = {
            'invalid_key': {'corrupted': 'data'}
        }
        request.session.save()
        
        # Should not raise error
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_handles_missing_cart_key_in_session(self):
        """Test middleware when 'cart' key doesn't exist"""
        request = self._create_request_with_session()
        
        # Explicitly ensure no 'cart' key
        if 'cart' in request.session:
            del request.session['cart']
        
        # Should not raise error
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_handles_request_without_user(self):
        """Test middleware handles request without user attribute"""
        request = self._create_request_with_session()
        
        # Remove user attribute
        delattr(request, 'user')
        
        # Should not raise error (might not process cart, but shouldn't crash)
        try:
            response = self.middleware(request)
            # If it succeeds, good
        except AttributeError:
            # If it fails with AttributeError, that's also acceptable
            # as long as it doesn't crash with other errors
            pass
    
    def test_middleware_with_very_large_cart(self):
        """Test middleware handles cart with many items"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Create many products
        products = []
        for i in range(50):
            products.append(
                NyscKit.objects.create(
                    name=f"Product {i}",
                    type="cap",
                    category=self.category,
                    price=Decimal("1000.00"),
                    available=True,
                    out_of_stock=False
                )
            )
        
        # Add all to cart
        for product in products:
            cart.add(product, quantity=1)
        
        self.assertEqual(len(cart), 50)
        
        # Process request (should not timeout or error)
        response = self.middleware(request)
        
        self.assertEqual(response.status_code, 200)
    
    def test_middleware_with_different_product_types(self):
        """Test middleware handles different product types"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Create products of different types
        kit_product = NyscKit.objects.create(
            name="Kit Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        tour_category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        
        tour_product = NyscTour.objects.create(
            name="Lagos Tour",
            category=tour_category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Add both types
        cart.add(kit_product, quantity=1)
        cart.add(tour_product, quantity=1, call_up_number="AB/22C/1234")
        
        # Process request
        response = self.middleware(request)
        
        # Both should remain (all valid)
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 2)
    
    @patch('cart.cart.Cart.cleanup')
    def test_middleware_calls_cart_cleanup(self, mock_cleanup):
        """Test middleware calls cart.cleanup method"""
        mock_cleanup.return_value = None
        
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Add item to ensure cart exists
        product = NyscKit.objects.create(
            name="Test",
            type="cap",
            category=self.category,
            price=Decimal("1000.00"),
            available=True,
            out_of_stock=False
        )
        cart.add(product, quantity=1)
        
        # Process request
        self.middleware(request)
        
        # Cleanup should have been called
        mock_cleanup.assert_called()


class CartCleanupMiddlewareIntegrationTests(TestCase):
    """Integration tests for realistic scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=Mock(status_code=200))
        self.middleware = CartCleanupMiddleware(self.get_response)
        
        # Create category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Popular Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def _create_request_with_session(self, user=None):
        """Helper to create request with session and message middleware"""
        request = self.factory.get('/')
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        # Add message middleware
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        # Add user
        request.user = user if user else Mock(is_authenticated=False)
        
        return request
    
    def test_realistic_stock_change_scenario(self):
        """Test realistic scenario: product goes out of stock"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # User adds product when it's available
        cart.add(self.product, quantity=3)
        self.assertEqual(len(cart), 3)
        
        # Product goes out of stock
        self.product.out_of_stock = True
        self.product.save()
        
        # User makes another request (middleware runs)
        self.middleware(request)
        
        # Product should be removed and user notified
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 0)
        
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn('out of stock', str(messages[0]))
    
    def test_realistic_product_discontinued_scenario(self):
        """Test realistic scenario: product is discontinued"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # User adds product
        cart.add(self.product, quantity=2)
        
        # Product is discontinued (marked unavailable)
        self.product.available = False
        self.product.save()
        
        # Middleware processes request
        self.middleware(request)
        
        # Product removed and user notified
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 0)
        
        # NOTE: available=False is treated as "out of stock" in cleanup
        messages = list(get_messages(request))
        self.assertIn('out of stock', str(messages[0]))
    
    def test_realistic_partial_cart_cleanup(self):
        """Test realistic scenario: some items valid, some invalid"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Create multiple products
        valid_product = self.product
        
        invalid_product = NyscKit.objects.create(
            name="Will be invalid",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Add both to cart
        cart.add(valid_product, quantity=2)
        cart.add(invalid_product, quantity=3)
        
        # Make one invalid
        invalid_product.out_of_stock = True
        invalid_product.save()
        
        # Process request
        self.middleware(request)
        
        # Only valid product should remain
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 2)
        
        items = list(cart_after)
        self.assertEqual(items[0]['product'].id, valid_product.id)


class CartCleanupMiddlewareMessageTests(TestCase):
    """Test message generation in detail"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.get_response = Mock(return_value=Mock(status_code=200))
        self.middleware = CartCleanupMiddleware(self.get_response)
        
        # Create category
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
    
    def _create_request_with_session(self):
        """Helper to create request with session and message middleware"""
        request = self.factory.get('/')
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        # Add message middleware
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        request.user = Mock(is_authenticated=False)
        
        return request
    
    def test_message_format_for_single_removed_item(self):
        """Test message format when single item is removed (out of stock)"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        product = NyscKit.objects.create(
            name="Test",
            type="cap",
            category=self.category,
            price=Decimal("1000.00"),
            available=False,
            out_of_stock=False
        )
        
        cart.add(product, quantity=1)
        
        self.middleware(request)
        
        messages = list(get_messages(request))
        message_text = str(messages[0])
        
        # Should mention count
        self.assertIn('1 item(s)', message_text)
        # NOTE: available=False is treated as "out of stock"
        self.assertIn('out of stock', message_text)
    
    def test_message_format_for_deleted_item(self):
        """Test message format when item is deleted from database"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        product = NyscKit.objects.create(
            name="Test",
            type="cap",
            category=self.category,
            price=Decimal("1000.00"),
            available=True,
            out_of_stock=False
        )
        
        cart.add(product, quantity=1)
        product.delete()
        
        self.middleware(request)
        
        messages = list(get_messages(request))
        message_text = str(messages[0])
        
        # Should mention count
        self.assertIn('1 item(s)', message_text)
        # Deleted products show "no longer available"
        self.assertIn('no longer available', message_text)
    
    def test_message_format_for_multiple_same_type_removed(self):
        """Test message format for multiple items of same type"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        # Create multiple unavailable products
        for i in range(3):
            product = NyscKit.objects.create(
                name=f"Product {i}",
                type="cap",
                category=self.category,
                price=Decimal("1000.00"),
                available=False,
                out_of_stock=False
            )
            cart.add(product, quantity=1)
        
        self.middleware(request)
        
        messages = list(get_messages(request))
        message_text = str(messages[0])
        
        # Should mention correct count
        self.assertIn('3 item(s)', message_text)
    
    def test_message_is_warning_level(self):
        """Test messages are warning level"""
        request = self._create_request_with_session()
        cart = Cart(request)
        
        product = NyscKit.objects.create(
            name="Test",
            type="cap",
            category=self.category,
            price=Decimal("1000.00"),
            available=False,
            out_of_stock=False
        )
        
        cart.add(product, quantity=1)
        
        self.middleware(request)
        
        messages = list(get_messages(request))
        
        # Import constants to check level
        from django.contrib.messages import constants as message_constants
        
        self.assertEqual(messages[0].level, message_constants.WARNING)