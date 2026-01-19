# cart/tests/tests_signals.py
"""
Comprehensive tests for cart signals
Tests signal handlers for user logout and cart management
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_out
from django.contrib.sessions.middleware import SessionMiddleware
from products.models import Category, NyscKit
from cart.cart import Cart
from cart.signals import clear_user_cart_on_logout
from decimal import Decimal

User = get_user_model()


class CartLogoutSignalTest(TestCase):
    """Test clear_user_cart_on_logout signal"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
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

    def get_request_with_session(self, user=None):
        """Helper to create request with session"""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        request.user = user
        return request

    def test_logout_clears_user_cart(self):
        """Test logout signal clears authenticated user's cart"""
        # Create authenticated user's cart
        request = self.get_request_with_session(user=self.user)
        cart = Cart(request)
        
        # Add item to user's cart
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        
        # Verify cart has items
        self.assertEqual(len(cart), 2)
        
        # Get the cart key
        user_cart_key = f'cart_user_{self.user.id}'
        self.assertIn(user_cart_key, request.session)
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # User cart should be cleared
        self.assertNotIn(user_cart_key, request.session)

    def test_logout_preserves_anonymous_cart(self):
        """Test logout doesn't affect anonymous cart"""
        # Create anonymous cart
        request = self.get_request_with_session()
        anon_cart = Cart(request)
        anon_cart.add(self.vest, quantity=1, size='M')
        anon_cart.save()
        
        anon_cart_key = anon_cart.cart_key
        
        # Now login user
        request.user = self.user
        
        # Trigger logout (even though we just "logged in")
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Anonymous cart should still exist
        self.assertIn(anon_cart_key, request.session)

    def test_logout_with_empty_cart(self):
        """Test logout with empty cart doesn't cause errors"""
        request = self.get_request_with_session(user=self.user)
        
        # Don't add anything to cart
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Should not raise any errors
        # Verify no user cart key exists
        user_cart_key = f'cart_user_{self.user.id}'
        self.assertNotIn(user_cart_key, request.session)

    def test_logout_signal_handler_exists(self):
        """Test signal handler is properly connected"""
        # Get all receivers for user_logged_out signal
        receivers = user_logged_out.receivers
        
        # Check if our handler is connected
        handler_connected = any(
            receiver[1]() == clear_user_cart_on_logout 
            for receiver in receivers
        )
        
        self.assertTrue(handler_connected, "clear_user_cart_on_logout signal handler not connected")

    def test_multiple_users_logout(self):
        """Test logout signal works correctly for multiple users"""
        # Create multiple users
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@test.com',
            password='testpass123'
        )
        
        # Create carts for both users
        request1 = self.get_request_with_session(user=self.user)
        cart1 = Cart(request1)
        cart1.add(self.vest, quantity=2, size='M')
        cart1.save()
        
        request2 = self.get_request_with_session(user=user2)
        cart2 = Cart(request2)
        cart2.add(self.vest, quantity=3, size='L')
        cart2.save()
        
        # Logout user1
        user_logged_out.send(
            sender=self.user.__class__,
            request=request1,
            user=self.user
        )
        
        # User1's cart should be cleared
        user1_cart_key = f'cart_user_{self.user.id}'
        self.assertNotIn(user1_cart_key, request1.session)
        
        # User2's cart should remain (in their session)
        user2_cart_key = f'cart_user_{user2.id}'
        self.assertIn(user2_cart_key, request2.session)

    def test_logout_with_none_user(self):
        """Test logout signal handles None user gracefully"""
        request = self.get_request_with_session()
        
        # Trigger logout with None user
        user_logged_out.send(
            sender=User,
            request=request,
            user=None
        )
        
        # Should not raise any errors

    def test_logout_without_session(self):
        """Test logout signal handles request without session"""
        request = self.factory.get('/')
        request.user = self.user
        # Don't add session middleware
        
        # Trigger logout signal
        try:
            user_logged_out.send(
                sender=self.user.__class__,
                request=request,
                user=self.user
            )
            # Should handle gracefully
        except AttributeError:
            # Expected if session doesn't exist
            pass

    def test_logout_clears_cart_with_multiple_items(self):
        """Test logout clears cart with multiple items"""
        request = self.get_request_with_session(user=self.user)
        cart = Cart(request)
        
        # Add multiple items
        tour = NyscKit.objects.create(
            name='Camp Tour',
            type='cap',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )
        
        cart.add(self.vest, quantity=2, size='M')
        cart.add(self.vest, quantity=1, size='L')
        cart.add(tour, quantity=3)
        cart.save()
        
        # Verify cart has items
        self.assertEqual(len(cart.cart), 3)
        
        # Trigger logout
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # All items should be cleared
        user_cart_key = f'cart_user_{self.user.id}'
        self.assertNotIn(user_cart_key, request.session)

    def test_logout_signal_logging(self):
        """Test logout signal logs appropriately"""
        request = self.get_request_with_session(user=self.user)
        cart = Cart(request)
        cart.add(self.vest, quantity=1, size='M')
        cart.save()
        
        # Trigger logout - should log
        with self.assertLogs('cart.signals', level='INFO') as cm:
            user_logged_out.send(
                sender=self.user.__class__,
                request=request,
                user=self.user
            )
        
        # Check log message
        self.assertTrue(
            any(f'Cleared cart for user {self.user.id}' in message for message in cm.output)
        )


class SignalIntegrationTest(TestCase):
    """Test signal integration with Django auth system"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
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

    def get_request_with_session(self, user=None):
        """Helper to create request with session"""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        request.user = user
        return request

    def test_cart_workflow_login_add_logout(self):
        """Test complete workflow: login -> add to cart -> logout"""
        # Start with anonymous cart
        request = self.get_request_with_session()
        anon_cart = Cart(request)
        anon_cart.add(self.vest, quantity=1, size='M')
        anon_cart.save()
        
        # "Login" - simulate authentication
        request.user = self.user
        auth_cart = Cart(request)
        
        # Anonymous cart should be migrated
        self.assertEqual(len(auth_cart), 1)
        
        # Add more items as authenticated user
        auth_cart.add(self.vest, quantity=2, size='L')
        auth_cart.save()
        
        # Logout
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # User cart should be cleared
        user_cart_key = f'cart_user_{self.user.id}'
        self.assertNotIn(user_cart_key, request.session)

    def test_signal_fires_on_actual_logout(self):
        """Test signal fires during actual Django logout"""
        from django.contrib.auth import logout
        
        request = self.get_request_with_session(user=self.user)
        cart = Cart(request)
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        
        # Store cart key
        user_cart_key = f'cart_user_{self.user.id}'
        self.assertIn(user_cart_key, request.session)
        
        # Perform actual logout
        logout(request)
        
        # Cart should be cleared by signal
        self.assertNotIn(user_cart_key, request.session)


class SignalEdgeCasesTest(TestCase):
    """Test edge cases in signal handling"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

    def get_request_with_session(self, user=None):
        """Helper to create request with session"""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        request.user = user
        return request

    def test_signal_with_corrupted_session(self):
        """Test signal handles corrupted session data"""
        request = self.get_request_with_session(user=self.user)
        
        # Corrupt the session
        request.session['cart_user_{}'.format(self.user.id)] = 'corrupted_data'
        
        # Trigger logout
        try:
            user_logged_out.send(
                sender=self.user.__class__,
                request=request,
                user=self.user
            )
            # Should handle gracefully
        except Exception as e:
            self.fail(f"Signal raised unexpected exception: {e}")

    def test_signal_with_invalid_user_id(self):
        """Test signal handles invalid user ID"""
        request = self.get_request_with_session(user=self.user)
        
        # Set invalid user ID
        self.user.id = None
        
        # Trigger logout
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Should not raise errors

    def test_concurrent_logout_signals(self):
        """Test multiple simultaneous logout signals"""
        users = [
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            )
            for i in range(5)
        ]
        
        requests = [
            self.get_request_with_session(user=user)
            for user in users
        ]
        
        # Trigger all logouts
        for request, user in zip(requests, users):
            user_logged_out.send(
                sender=user.__class__,
                request=request,
                user=user
            )
        
        # All should complete without errors

    def test_signal_with_already_cleared_cart(self):
        """Test signal when cart already cleared"""
        request = self.get_request_with_session(user=self.user)
        
        # Manually clear cart first
        user_cart_key = f'cart_user_{self.user.id}'
        if user_cart_key in request.session:
            del request.session[user_cart_key]
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Should not raise errors

    def test_signal_performance(self):
        """Test signal handler performance with large cart"""
        from products.models import NyscKit, Category
        
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        request = self.get_request_with_session(user=self.user)
        cart = Cart(request)
        
        # Add many items
        for i in range(50):
            product = NyscKit.objects.create(
                name=f'Product {i}',
                type='vest',
                category=category,
                price=Decimal('1000.00'),
                available=True
            )
            cart.add(product, quantity=1, size='M')
        
        cart.save()
        
        # Trigger logout - should complete quickly
        import time
        start = time.time()
        
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        duration = time.time() - start
        
        # Should complete in reasonable time (< 1 second)
        self.assertLess(duration, 1.0)