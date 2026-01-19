# cart/tests/tests_middleware.py
"""
Comprehensive tests for CartCleanupMiddleware
Tests automatic cart cleanup on each request
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages import get_messages
from products.models import Category, NyscKit, NyscTour
from cart.cart import Cart
from cart.middleware import CartCleanupMiddleware
from decimal import Decimal

User = get_user_model()


class CartCleanupMiddlewareTest(TestCase):
    """Test CartCleanupMiddleware functionality"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        
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

    def get_request_with_middleware(self):
        """Helper to create request with full middleware stack"""
        request = self.factory.get('/')
        
        # Add session middleware
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        # Add message middleware
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        request.user = None
        return request

    def test_middleware_leaves_valid_cart_unchanged(self):
        """Test middleware doesn't remove valid items"""
        request = self.get_request_with_middleware()
        
        # Add valid items to cart
        cart = Cart(request)
        cart.add(self.vest, quantity=2, size='M')
        cart.add(self.tour, quantity=1, call_up_number='AB/22C/1234')
        cart.save()
        
        initial_count = len(cart)
        
        # Create middleware and process request
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Cart should remain unchanged
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), initial_count)

    def test_middleware_removes_deleted_products(self):
        """Test middleware removes items for deleted products"""
        request = self.get_request_with_middleware()
        
        # Add items to cart
        cart = Cart(request)
        cart.add(self.vest, quantity=2, size='M')
        cart.add(self.tour, quantity=1, call_up_number='AB/22C/1234')
        cart.save()
        
        # Delete one product
        self.vest.delete()
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Vest should be removed, tour should remain
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 1)

    def test_middleware_removes_unavailable_products(self):
        """Test middleware removes unavailable products"""
        request = self.get_request_with_middleware()
        
        # Add items to cart
        cart = Cart(request)
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        
        # Mark product as unavailable
        self.vest.available = False
        self.vest.save()
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Cart should be empty
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 0)

    def test_middleware_removes_out_of_stock_products(self):
        """Test middleware removes out of stock products"""
        request = self.get_request_with_middleware()
        
        # Add items to cart
        cart = Cart(request)
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        
        # Mark product as out of stock
        self.vest.out_of_stock = True
        self.vest.save()
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Cart should be empty
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 0)

    def test_middleware_adds_warning_message_for_deleted(self):
        """Test middleware adds warning message when items removed"""
        request = self.get_request_with_middleware()
        
        # Add item to cart
        cart = Cart(request)
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        
        # Delete product
        self.vest.delete()
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Check for warning message
        messages = list(get_messages(request))
        self.assertTrue(len(messages) > 0)
        self.assertIn('removed', str(messages[0]))

    def test_middleware_adds_message_for_out_of_stock(self):
        """Test middleware adds message for out of stock items"""
        request = self.get_request_with_middleware()
        
        # Add item to cart
        cart = Cart(request)
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        
        # Mark as out of stock
        self.vest.out_of_stock = True
        self.vest.save()
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Check for message
        messages = list(get_messages(request))
        self.assertTrue(len(messages) > 0)
        self.assertIn('out of stock', str(messages[0]).lower())

    def test_middleware_combines_messages(self):
        """Test middleware combines messages for multiple removal reasons"""
        request = self.get_request_with_middleware()
        
        # Create another product
        cap = NyscKit.objects.create(
            name='Quality Nysc Cap',
            type='cap',
            category=self.category,
            price=Decimal('1500.00'),
            available=True
        )
        
        # Add items to cart
        cart = Cart(request)
        cart.add(self.vest, quantity=1, size='M')
        cart.add(cap, quantity=1)
        cart.save()
        
        # Delete one, mark other out of stock
        self.vest.delete()
        cap.out_of_stock = True
        cap.save()
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Should have combined message
        messages = list(get_messages(request))
        self.assertTrue(len(messages) > 0)
        message_text = str(messages[0])
        self.assertIn('and', message_text)

    def test_middleware_no_message_for_valid_cart(self):
        """Test middleware doesn't add message when nothing removed"""
        request = self.get_request_with_middleware()
        
        # Add valid items
        cart = Cart(request)
        cart.add(self.vest, quantity=1, size='M')
        cart.save()
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Should have no messages
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 0)

    def test_middleware_handles_empty_cart(self):
        """Test middleware handles empty cart gracefully"""
        request = self.get_request_with_middleware()
        
        # Don't add anything to cart
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Should not raise errors
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 0)

    def test_middleware_handles_request_without_session(self):
        """Test middleware handles request without session"""
        request = self.factory.get('/')
        # Don't add session middleware
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Should not raise errors

    def test_middleware_handles_request_without_cart(self):
        """Test middleware handles request without cart key"""
        request = self.get_request_with_middleware()
        
        # Ensure no cart key in session
        if 'cart' in request.session:
            del request.session['cart']
        
        # Process request through middleware
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Should not raise errors

    def test_middleware_processes_on_every_request(self):
        """Test middleware runs on every request"""
        request = self.get_request_with_middleware()
        
        # Add item
        cart = Cart(request)
        cart.add(self.vest, quantity=1, size='M')
        cart.save()
        
        # Delete product
        self.vest.delete()
        
        # Process multiple requests
        middleware = CartCleanupMiddleware(lambda r: None)
        
        middleware(request)
        cart1 = Cart(request)
        count1 = len(cart1)
        
        # Process again (cart should already be clean)
        middleware(request)
        cart2 = Cart(request)
        count2 = len(cart2)
        
        self.assertEqual(count1, 0)
        self.assertEqual(count2, 0)

    def test_middleware_calls_get_response(self):
        """Test middleware calls get_response"""
        request = self.get_request_with_middleware()
        
        response_called = False
        
        def get_response(r):
            nonlocal response_called
            response_called = True
            return None
        
        middleware = CartCleanupMiddleware(get_response)
        middleware(request)
        
        self.assertTrue(response_called)

    def test_middleware_returns_response(self):
        """Test middleware returns response from get_response"""
        request = self.get_request_with_middleware()
        
        expected_response = "Test Response"
        
        def get_response(r):
            return expected_response
        
        middleware = CartCleanupMiddleware(get_response)
        response = middleware(request)
        
        self.assertEqual(response, expected_response)


class MiddlewareEdgeCasesTest(TestCase):
    """Test edge cases in middleware"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        
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

    def get_request_with_middleware(self):
        """Helper to create request with middleware"""
        request = self.factory.get('/')
        
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        request.user = None
        return request

    def test_middleware_with_corrupted_cart_data(self):
        """Test middleware handles corrupted cart data"""
        request = self.get_request_with_middleware()
        
        # Corrupt cart data
        request.session['cart'] = 'corrupted_data'
        request.session.save()
        
        # Process request - should handle gracefully
        middleware = CartCleanupMiddleware(lambda r: None)
        try:
            middleware(request)
        except Exception as e:
            self.fail(f"Middleware raised unexpected exception: {e}")

    def test_middleware_with_invalid_item_keys(self):
        """Test middleware handles invalid item keys"""
        request = self.get_request_with_middleware()
        
        # Add invalid item key directly
        cart = Cart(request)
        cart.cart['invalid_key_format'] = {'quantity': 1}
        cart.save()
        
        # Process request
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Invalid key should be removed
        cart_after = Cart(request)
        self.assertNotIn('invalid_key_format', cart_after.cart)

    def test_middleware_with_mixed_valid_invalid_items(self):
        """Test middleware removes only invalid items"""
        request = self.get_request_with_middleware()
        
        cart = Cart(request)
        
        # Add valid item
        cart.add(self.vest, quantity=1, size='M')
        
        # Add invalid item directly
        cart.cart['invalid'] = {'quantity': 1}
        cart.save()
        
        # Process request
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Valid item should remain, invalid should be removed
        cart_after = Cart(request)
        self.assertGreater(len(cart_after.cart), 0)
        self.assertNotIn('invalid', cart_after.cart)

    def test_middleware_performance_with_large_cart(self):
        """Test middleware performance with many items"""
        request = self.get_request_with_middleware()
        
        cart = Cart(request)
        
        # Add many items
        for i in range(50):
            product = NyscKit.objects.create(
                name=f'Product {i}',
                type='cap',
                category=self.category,
                price=Decimal('1000.00'),
                available=True
            )
            cart.add(product, quantity=1)
        
        cart.save()
        
        # Process request - should complete quickly
        import time
        start = time.time()
        
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        duration = time.time() - start
        
        # Should complete in reasonable time (< 2 seconds)
        self.assertLess(duration, 2.0)

    def test_middleware_with_authenticated_user(self):
        """Test middleware works with authenticated users"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        request = self.get_request_with_middleware()
        request.user = user
        
        # Add item to user's cart
        cart = Cart(request)
        cart.add(self.vest, quantity=1, size='M')
        cart.save()
        
        # Delete product
        self.vest.delete()
        
        # Process request
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Item should be removed
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 0)

    def test_middleware_concurrent_requests(self):
        """Test middleware handles concurrent requests"""
        # Create multiple requests
        requests = [self.get_request_with_middleware() for _ in range(5)]
        
        # Add items to all carts
        for request in requests:
            cart = Cart(request)
            cart.add(self.vest, quantity=1, size='M')
            cart.save()
        
        # Delete product
        self.vest.delete()
        
        # Process all requests
        middleware = CartCleanupMiddleware(lambda r: None)
        
        for request in requests:
            middleware(request)
            cart = Cart(request)
            self.assertEqual(len(cart), 0)

    def test_middleware_with_multiple_deletions(self):
        """Test middleware removes multiple deleted items"""
        request = self.get_request_with_middleware()
        
        # Create multiple products
        products = []
        for i in range(5):
            product = NyscKit.objects.create(
                name=f'Product {i}',
                type='cap',
                category=self.category,
                price=Decimal('1000.00'),
                available=True
            )
            products.append(product)
        
        # Add all to cart
        cart = Cart(request)
        for product in products:
            cart.add(product, quantity=1)
        cart.save()
        
        # Delete some products
        for product in products[:3]:
            product.delete()
        
        # Process request
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Only 2 products should remain
        cart_after = Cart(request)
        self.assertEqual(len(cart_after.cart), 2)

    def test_middleware_message_format(self):
        """Test middleware message format is user-friendly"""
        request = self.get_request_with_middleware()
        
        # Add item and delete it
        cart = Cart(request)
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        
        self.vest.delete()
        
        # Process request
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Check message format
        messages = list(get_messages(request))
        self.assertTrue(len(messages) > 0)
        
        message_text = str(messages[0])
        
        # Should be informative
        self.assertIn('cart', message_text.lower())
        self.assertIn('updated', message_text.lower())

    def test_middleware_doesnt_affect_other_session_data(self):
        """Test middleware only modifies cart data"""
        request = self.get_request_with_middleware()
        
        # Add some other session data
        request.session['other_key'] = 'other_value'
        request.session['another_key'] = {'nested': 'data'}
        
        # Add cart item
        cart = Cart(request)
        cart.add(self.vest, quantity=1, size='M')
        cart.save()
        
        # Process request
        middleware = CartCleanupMiddleware(lambda r: None)
        middleware(request)
        
        # Other session data should be untouched
        self.assertEqual(request.session['other_key'], 'other_value')
        self.assertEqual(request.session['another_key'], {'nested': 'data'})


class MiddlewareIntegrationTest(TestCase):
    """Test middleware integration with Django request/response cycle"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        
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

    def get_request_with_middleware(self):
        """Helper to create request with middleware"""
        request = self.factory.get('/')
        
        session_middleware = SessionMiddleware(lambda x: x)
        session_middleware.process_request(request)
        request.session.save()
        
        message_middleware = MessageMiddleware(lambda x: x)
        message_middleware.process_request(request)
        
        request.user = None
        return request

    def test_middleware_in_request_cycle(self):
        """Test middleware works in full request cycle"""
        request = self.get_request_with_middleware()
        
        # Add item to cart
        cart = Cart(request)
        cart.add(self.vest, quantity=1, size='M')
        cart.save()
        
        # Mark product as out of stock (simulating change between requests)
        self.vest.out_of_stock = True
        self.vest.save()
        
        # Create middleware instance
        def view(r):
            # View would execute here
            return "view_response"
        
        middleware = CartCleanupMiddleware(view)
        
        # Process request
        response = middleware(request)
        
        # Cart should be cleaned
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 0)
        
        # Response should be returned
        self.assertEqual(response, "view_response")

    def test_middleware_order_doesnt_matter(self):
        """Test cleanup works regardless of when middleware is called"""
        request = self.get_request_with_middleware()
        
        # Add item
        cart = Cart(request)
        cart.add(self.vest, quantity=1, size='M')
        cart.save()
        
        # Delete product
        self.vest.delete()
        
        # Process through middleware multiple times
        middleware = CartCleanupMiddleware(lambda r: None)
        
        middleware(request)
        middleware(request)
        middleware(request)
        
        # Should be idempotent
        cart_after = Cart(request)
        self.assertEqual(len(cart_after), 0)