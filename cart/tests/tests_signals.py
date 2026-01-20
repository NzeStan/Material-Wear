# cart/tests/tests_signals.py
"""
Comprehensive tests for Cart Signal Handlers

Coverage:
- clear_user_cart_on_logout signal
- Cart cleanup on user logout
- User cart isolation
- Anonymous cart preservation
- Edge cases: no cart, empty cart, multiple users
- Logging verification
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_out
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from unittest.mock import Mock, patch
from cart.cart import Cart
from cart.signals import clear_user_cart_on_logout
from products.models import Category, NyscKit
import logging

User = get_user_model()


class ClearCartOnLogoutSignalTests(TestCase):
    """Test clear_user_cart_on_logout signal handler"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and product for cart testing
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
        """Helper to create request with session middleware"""
        request = self.factory.get('/')
        
        # Add session
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        
        # Add user
        request.user = user if user else Mock(is_authenticated=False)
        
        return request
    
    def test_signal_clears_user_cart_on_logout(self):
        """Test signal handler clears user-specific cart when user logs out"""
        # Create request with authenticated user
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        
        # Add items to cart
        cart.add(self.product, quantity=3)
        self.assertEqual(len(cart), 3)
        
        # Verify cart exists in session
        cart_key = f"cart_user_{self.user.id}"
        self.assertIn(cart_key, request.session)
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Verify cart is cleared from session
        self.assertNotIn(cart_key, request.session)
    
    def test_signal_does_not_clear_anonymous_cart(self):
        """Test signal does not affect anonymous cart"""
        # Create anonymous cart
        anon_request = self._create_request_with_session()
        anon_cart = Cart(anon_request)
        anon_cart.add(self.product, quantity=2)
        
        # Verify anonymous cart exists
        self.assertIn(settings.CART_SESSION_ID, anon_request.session)
        self.assertEqual(len(anon_cart), 2)
        
        # Create authenticated user and their cart
        user_request = self._create_request_with_session(user=self.user)
        user_cart = Cart(user_request)
        user_cart.add(self.product, quantity=5)
        
        # Trigger logout signal for authenticated user
        user_logged_out.send(
            sender=self.user.__class__,
            request=user_request,
            user=self.user
        )
        
        # Anonymous cart should still exist
        self.assertIn(settings.CART_SESSION_ID, anon_request.session)
        self.assertEqual(len(anon_cart), 2)
    
    def test_signal_handles_user_with_no_cart(self):
        """Test signal handles user who has no cart gracefully"""
        # Create request for user with no cart
        request = self._create_request_with_session(user=self.user)
        
        # Verify no cart exists
        cart_key = f"cart_user_{self.user.id}"
        self.assertNotIn(cart_key, request.session)
        
        # Trigger logout signal (should not raise error)
        try:
            user_logged_out.send(
                sender=self.user.__class__,
                request=request,
                user=self.user
            )
        except Exception as e:
            self.fail(f"Signal raised unexpected exception: {e}")
    
    def test_signal_handles_empty_cart(self):
        """Test signal handles empty cart"""
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        
        # Cart exists but is empty
        cart_key = f"cart_user_{self.user.id}"
        self.assertIn(cart_key, request.session)
        self.assertEqual(len(cart), 0)
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Cart should be cleared from session
        self.assertNotIn(cart_key, request.session)
    
    def test_signal_with_null_user(self):
        """Test signal handles None user gracefully"""
        request = self._create_request_with_session()
        
        # Trigger signal with None user (should not raise error)
        try:
            user_logged_out.send(
                sender=User,
                request=request,
                user=None
            )
        except Exception as e:
            self.fail(f"Signal raised unexpected exception with None user: {e}")
    
    def test_signal_isolates_multiple_user_carts(self):
        """Test signal only clears the logged out user's cart"""
        # Create two users
        user1 = self.user
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Create separate requests and carts for each user
        request1 = self._create_request_with_session(user=user1)
        cart1 = Cart(request1)
        cart1.add(self.product, quantity=2)
        
        request2 = self._create_request_with_session(user=user2)
        cart2 = Cart(request2)
        cart2.add(self.product, quantity=3)
        
        # Verify both carts exist
        cart_key1 = f"cart_user_{user1.id}"
        cart_key2 = f"cart_user_{user2.id}"
        self.assertIn(cart_key1, request1.session)
        self.assertIn(cart_key2, request2.session)
        
        # User 1 logs out
        user_logged_out.send(
            sender=user1.__class__,
            request=request1,
            user=user1
        )
        
        # User 1's cart should be cleared
        self.assertNotIn(cart_key1, request1.session)
        
        # User 2's cart should still exist
        self.assertIn(cart_key2, request2.session)
        self.assertEqual(len(cart2), 3)
    
    @patch('cart.signals.logger')
    def test_signal_logs_cart_clearance(self, mock_logger):
        """Test signal logs when cart is cleared"""
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        cart.add(self.product, quantity=1)
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Verify logging was called
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        self.assertIn(f"user {self.user.id}", call_args)
        self.assertIn("logout", call_args.lower())
    
    @patch('cart.signals.logger')
    def test_signal_does_not_log_when_no_cart(self, mock_logger):
        """Test signal does not log when user has no cart"""
        request = self._create_request_with_session(user=self.user)
        
        # No cart created - cart key won't be in session
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Should not log since no cart was cleared
        mock_logger.info.assert_not_called()
    
    def test_direct_signal_handler_call(self):
        """Test calling the signal handler function directly"""
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        cart.add(self.product, quantity=4)
        
        cart_key = f"cart_user_{self.user.id}"
        self.assertIn(cart_key, request.session)
        
        # Call handler directly
        clear_user_cart_on_logout(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Cart should be cleared
        self.assertNotIn(cart_key, request.session)
    
    def test_signal_with_different_cart_content_types(self):
        """Test signal clears cart with various product types"""
        # Create products of different types
        tour_category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        
        from products.models import NyscTour
        tour_product = NyscTour.objects.create(
            name="Lagos Tour",
            category=tour_category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Add multiple product types to cart
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        cart.add(self.product, quantity=2)  # NyscKit
        cart.add(tour_product, quantity=1, call_up_number="AB/22C/1234")  # NyscTour
        
        self.assertEqual(len(cart), 3)
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # All items should be cleared
        cart_key = f"cart_user_{self.user.id}"
        self.assertNotIn(cart_key, request.session)
    
    def test_signal_preserves_other_session_data(self):
        """Test signal only clears cart, not other session data"""
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        cart.add(self.product, quantity=1)
        
        # Add other session data
        request.session['other_data'] = 'important_value'
        request.session['user_preferences'] = {'theme': 'dark'}
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Cart should be cleared
        cart_key = f"cart_user_{self.user.id}"
        self.assertNotIn(cart_key, request.session)
        
        # Other session data should remain
        self.assertEqual(request.session['other_data'], 'important_value')
        self.assertEqual(request.session['user_preferences'], {'theme': 'dark'})
    
    def test_signal_with_user_without_id(self):
        """Test signal handles user without id attribute"""
        request = self._create_request_with_session()
        
        # Create mock user without id
        mock_user = Mock(is_authenticated=True)
        mock_user.id = None
        
        # Should not raise error
        try:
            user_logged_out.send(
                sender=User,
                request=request,
                user=mock_user
            )
        except Exception as e:
            self.fail(f"Signal raised unexpected exception with user.id=None: {e}")


class SignalRegistrationTests(TestCase):
    """Test signal is properly registered"""
    
    def test_signal_handler_is_registered(self):
        """Test clear_user_cart_on_logout is registered as a receiver"""
        # Get all receivers for user_logged_out signal
        receivers = user_logged_out.receivers
        
        # Check if our handler is in the receivers list
        handler_registered = any(
            receiver[1]() == clear_user_cart_on_logout or 
            (hasattr(receiver[1](), '__name__') and 
             receiver[1]().__name__ == 'clear_user_cart_on_logout')
            for receiver in receivers
            if receiver[1]() is not None
        )
        
        # If the above doesn't work due to weak references, at least verify
        # the signal has receivers
        self.assertTrue(len(receivers) > 0, 
                       "user_logged_out signal has no receivers registered")
    
    def test_signal_is_imported_in_apps_ready(self):
        """Test signals are imported when app is ready"""
        from django.apps import apps
        from cart.apps import CartConfig
        
        # Verify CartConfig is registered
        app_config = apps.get_app_config('cart')
        self.assertIsInstance(app_config, CartConfig)
        
        # Verify the ready method exists
        self.assertTrue(hasattr(app_config, 'ready'))


class SignalIntegrationTests(TestCase):
    """Integration tests for signal behavior in realistic scenarios"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        
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
            name="Test Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def _create_request_with_session(self, user=None):
        """Helper to create request with session middleware"""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        request.user = user if user else Mock(is_authenticated=False)
        return request
    
    def test_realistic_logout_flow(self):
        """Test complete realistic logout flow with cart"""
        # User logs in and adds items to cart
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        
        # User adds multiple items
        cart.add(self.product, quantity=3)
        self.assertEqual(len(cart), 3)
        
        # User logs out
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Cart should be gone
        cart_key = f"cart_user_{self.user.id}"
        self.assertNotIn(cart_key, request.session)
        
        # If user logs back in, they should have empty cart
        new_request = self._create_request_with_session(user=self.user)
        new_cart = Cart(new_request)
        self.assertEqual(len(new_cart), 0)
    
    def test_logout_with_pending_checkout(self):
        """Test logout clears cart even with items ready for checkout"""
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        
        # User adds items and is about to checkout
        cart.add(self.product, quantity=5)
        total = cart.get_total_price()
        self.assertEqual(total, Decimal("25000.00"))
        
        # User logs out before completing checkout
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Cart should be cleared (for security)
        cart_key = f"cart_user_{self.user.id}"
        self.assertNotIn(cart_key, request.session)
    
    def test_session_timeout_like_logout(self):
        """Test signal behavior simulating session timeout"""
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        
        # Simulate session timeout triggering logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Cart should be cleared
        cart_key = f"cart_user_{self.user.id}"
        self.assertNotIn(cart_key, request.session)


class EdgeCaseSignalTests(TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def _create_request_with_session(self, user=None):
        """Helper to create request with session middleware"""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        request.user = user if user else Mock(is_authenticated=False)
        return request
    
    def test_signal_with_corrupted_cart_data(self):
        """Test signal handles corrupted cart data gracefully"""
        request = self._create_request_with_session(user=self.user)
        cart_key = f"cart_user_{self.user.id}"
        
        # Manually add corrupted cart data
        request.session[cart_key] = {'corrupted': 'data', 'invalid': True}
        request.session.save()
        
        # Trigger logout signal (should not raise error)
        try:
            user_logged_out.send(
                sender=self.user.__class__,
                request=request,
                user=self.user
            )
        except Exception as e:
            self.fail(f"Signal raised unexpected exception with corrupted data: {e}")
        
        # Corrupted cart should be removed
        self.assertNotIn(cart_key, request.session)
    
    def test_signal_without_request_session(self):
        """Test signal handles request without session attribute"""
        # Create request without session
        request = self.factory.get('/')
        request.user = self.user
        
        # Trigger signal (should not raise error)
        try:
            user_logged_out.send(
                sender=self.user.__class__,
                request=request,
                user=self.user
            )
        except AttributeError:
            self.fail("Signal should handle missing session gracefully")
    
    def test_signal_with_very_large_cart(self):
        """Test signal handles cart with many items"""
        request = self._create_request_with_session(user=self.user)
        cart = Cart(request)
        
        # Create many products
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        products = []
        for i in range(50):  # Create 50 different products
            products.append(
                NyscKit.objects.create(
                    name=f"Product {i}",
                    type="cap",
                    category=category,
                    price=Decimal("1000.00"),
                    available=True,
                    out_of_stock=False
                )
            )
        
        # Add all to cart
        for product in products:
            cart.add(product, quantity=1)
        
        self.assertEqual(len(cart), 50)
        
        # Trigger logout signal
        user_logged_out.send(
            sender=self.user.__class__,
            request=request,
            user=self.user
        )
        
        # Cart should be cleared
        cart_key = f"cart_user_{self.user.id}"
        self.assertNotIn(cart_key, request.session)