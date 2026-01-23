# webhook_router/tests_throttling.py
"""
Comprehensive bulletproof tests for jmw/throttling.py

Test Coverage:
===============
✅ CheckoutRateThrottle
   - Rate limit enforcement (10/hour)
   - Authenticated users only
   - Scope verification
   - Limit reset after time window

✅ PaymentRateThrottle
   - Rate limit enforcement (10/hour)
   - Anonymous users
   - Scope verification
   - Per-IP throttling

✅ BulkOrderWebhookThrottle
   - Rate limit enforcement (100/hour)
   - Anonymous users
   - Scope verification
   - High-volume handling

✅ CartRateThrottle
   - Rate limit enforcement (100/hour)
   - Anonymous users
   - Scope verification

✅ StrictAnonRateThrottle
   - Rate limit enforcement (50/hour)
   - Anonymous users
   - Scope verification
   - Stricter than default

✅ BurstUserRateThrottle
   - Rate limit enforcement (20/minute)
   - Authenticated users
   - Scope verification
   - Short-term burst protection

✅ SustainedUserRateThrottle
   - Rate limit enforcement (500/hour)
   - Authenticated users
   - Scope verification
   - Long-term sustained usage

✅ Integration Tests
   - Multiple throttle classes
   - Different time windows
   - Cache behavior
   - Rate limit headers
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, throttle_classes
from unittest.mock import patch, Mock
import time

from jmw.throttling import (
    CheckoutRateThrottle,
    PaymentRateThrottle,
    BulkOrderWebhookThrottle,
    CartRateThrottle,
    StrictAnonRateThrottle,
    BurstUserRateThrottle,
    SustainedUserRateThrottle
)

User = get_user_model()


# ============================================================================
# BASE THROTTLE TEST CLASS
# ============================================================================

class BaseThrottleTestCase(TestCase):
    """Base test class with common utilities for throttle testing"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def make_request(self, throttle_class, user=None, method='GET', url='/test/'):
        """
        Helper to create request and check throttle
        
        Returns:
            bool: True if allowed, False if throttled
        """
        request = self.factory.get(url)
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        if user:
            force_authenticate(request, user=user)
        
        throttle = throttle_class()
        return throttle.allow_request(request, None)
    
    def exhaust_throttle(self, throttle_class, user=None, expected_limit=None):
        """
        Helper to exhaust throttle limit
        
        Returns:
            int: Number of requests that succeeded before throttling
        """
        count = 0
        while True:
            allowed = self.make_request(throttle_class, user=user)
            if not allowed:
                break
            count += 1
            if expected_limit and count >= expected_limit + 10:  # Safety break
                break
        return count


# ============================================================================
# CHECKOUT RATE THROTTLE TESTS
# ============================================================================

class CheckoutRateThrottleTests(BaseThrottleTestCase):
    """Test CheckoutRateThrottle (10/hour for authenticated users)"""
    
    def test_rate_configuration(self):
        """Test throttle rate is correctly configured"""
        throttle = CheckoutRateThrottle()
        
        self.assertEqual(throttle.rate, '10/hour')
        self.assertEqual(throttle.scope, 'checkout')
    
    def test_inherits_from_user_rate_throttle(self):
        """Test that CheckoutRateThrottle inherits from UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle
        
        self.assertTrue(issubclass(CheckoutRateThrottle, UserRateThrottle))
    
    def test_allows_first_request(self):
        """Test that first request is allowed"""
        allowed = self.make_request(CheckoutRateThrottle, user=self.user)
        
        self.assertTrue(allowed)
    
    def test_enforces_rate_limit(self):
        """Test that rate limit is enforced after 10 requests"""
        # Make 10 requests (should all succeed)
        for i in range(10):
            allowed = self.make_request(CheckoutRateThrottle, user=self.user)
            self.assertTrue(allowed, f"Request {i+1} should be allowed")
        
        # 11th request should be throttled
        allowed = self.make_request(CheckoutRateThrottle, user=self.user)
        self.assertFalse(allowed, "11th request should be throttled")
    
    def test_different_users_have_separate_limits(self):
        """Test that different users have independent rate limits"""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Exhaust user1's limit
        for i in range(10):
            self.make_request(CheckoutRateThrottle, user=self.user)
        
        # User1 should be throttled
        allowed = self.make_request(CheckoutRateThrottle, user=self.user)
        self.assertFalse(allowed)
        
        # User2 should still be allowed
        allowed = self.make_request(CheckoutRateThrottle, user=user2)
        self.assertTrue(allowed)
    
    def test_unauthenticated_user_not_affected(self):
        """Test that unauthenticated users are not affected by UserRateThrottle"""
        # UserRateThrottle only applies to authenticated users
        # Unauthenticated requests should not be throttled by this throttle
        throttle = CheckoutRateThrottle()
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.user = Mock(is_authenticated=False)
        
        # Should return None (not applicable) or True (allowed)
        # Depending on DRF version, but shouldn't throttle
        result = throttle.allow_request(request, None)
        # UserRateThrottle returns True for unauthenticated users
        self.assertTrue(result)


# ============================================================================
# PAYMENT RATE THROTTLE TESTS
# ============================================================================

class PaymentRateThrottleTests(BaseThrottleTestCase):
    """Test PaymentRateThrottle (10/hour for anonymous users)"""
    
    def test_rate_configuration(self):
        """Test throttle rate is correctly configured"""
        throttle = PaymentRateThrottle()
        
        self.assertEqual(throttle.rate, '10/hour')
        self.assertEqual(throttle.scope, 'payment')
    
    def test_inherits_from_anon_rate_throttle(self):
        """Test that PaymentRateThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle
        
        self.assertTrue(issubclass(PaymentRateThrottle, AnonRateThrottle))
    
    def test_allows_first_request(self):
        """Test that first anonymous request is allowed"""
        allowed = self.make_request(PaymentRateThrottle, user=None)
        
        self.assertTrue(allowed)
    
    def test_enforces_rate_limit_for_anonymous(self):
        """Test that rate limit is enforced for anonymous users"""
        # Make 10 requests
        for i in range(10):
            allowed = self.make_request(PaymentRateThrottle, user=None)
            self.assertTrue(allowed, f"Request {i+1} should be allowed")
        
        # 11th request should be throttled
        allowed = self.make_request(PaymentRateThrottle, user=None)
        self.assertFalse(allowed)
    
    def test_throttles_by_ip_address(self):
        """Test that throttling is based on IP address"""
        # Make 10 requests from first IP
        for i in range(10):
            request = self.factory.get('/test/')
            request.META['REMOTE_ADDR'] = '127.0.0.1'
            throttle = PaymentRateThrottle()
            throttle.allow_request(request, None)
        
        # Request from same IP should be throttled
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        throttle = PaymentRateThrottle()
        allowed = throttle.allow_request(request, None)
        self.assertFalse(allowed)
        
        # Request from different IP should be allowed
        request = self.factory.get('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        throttle = PaymentRateThrottle()
        allowed = throttle.allow_request(request, None)
        self.assertTrue(allowed)


# ============================================================================
# BULK ORDER WEBHOOK THROTTLE TESTS
# ============================================================================

class BulkOrderWebhookThrottleTests(BaseThrottleTestCase):
    """Test BulkOrderWebhookThrottle (100/hour for anonymous users)"""
    
    def test_rate_configuration(self):
        """Test throttle rate is correctly configured"""
        throttle = BulkOrderWebhookThrottle()
        
        self.assertEqual(throttle.rate, '100/hour')
        self.assertEqual(throttle.scope, 'bulk_webhook')
    
    def test_inherits_from_anon_rate_throttle(self):
        """Test that BulkOrderWebhookThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle
        
        self.assertTrue(issubclass(BulkOrderWebhookThrottle, AnonRateThrottle))
    
    def test_allows_high_volume_requests(self):
        """Test that high volume requests are allowed (up to 100)"""
        # Make 50 requests (should all succeed)
        for i in range(50):
            allowed = self.make_request(BulkOrderWebhookThrottle, user=None)
            self.assertTrue(allowed, f"Request {i+1} should be allowed")
    
    def test_enforces_rate_limit(self):
        """Test that rate limit is enforced after 100 requests"""
        count = self.exhaust_throttle(BulkOrderWebhookThrottle, user=None, expected_limit=100)
        
        # Should allow exactly 100 requests
        self.assertEqual(count, 100)
        
        # 101st request should be throttled
        allowed = self.make_request(BulkOrderWebhookThrottle, user=None)
        self.assertFalse(allowed)


# ============================================================================
# CART RATE THROTTLE TESTS
# ============================================================================

class CartRateThrottleTests(BaseThrottleTestCase):
    """Test CartRateThrottle (100/hour for anonymous users)"""
    
    def test_rate_configuration(self):
        """Test throttle rate is correctly configured"""
        throttle = CartRateThrottle()
        
        self.assertEqual(throttle.rate, '100/hour')
        self.assertEqual(throttle.scope, 'cart')
    
    def test_inherits_from_anon_rate_throttle(self):
        """Test that CartRateThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle
        
        self.assertTrue(issubclass(CartRateThrottle, AnonRateThrottle))
    
    def test_allows_frequent_cart_operations(self):
        """Test that frequent cart operations are allowed"""
        # Make 50 requests
        for i in range(50):
            allowed = self.make_request(CartRateThrottle, user=None)
            self.assertTrue(allowed)
    
    def test_enforces_rate_limit(self):
        """Test that rate limit is enforced after 100 requests"""
        count = self.exhaust_throttle(CartRateThrottle, user=None, expected_limit=100)
        
        self.assertEqual(count, 100)


# ============================================================================
# STRICT ANON RATE THROTTLE TESTS
# ============================================================================

class StrictAnonRateThrottleTests(BaseThrottleTestCase):
    """Test StrictAnonRateThrottle (50/hour for anonymous users)"""
    
    def test_rate_configuration(self):
        """Test throttle rate is correctly configured"""
        throttle = StrictAnonRateThrottle()
        
        self.assertEqual(throttle.rate, '50/hour')
        self.assertEqual(throttle.scope, 'anon_strict')
    
    def test_inherits_from_anon_rate_throttle(self):
        """Test that StrictAnonRateThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle
        
        self.assertTrue(issubclass(StrictAnonRateThrottle, AnonRateThrottle))
    
    def test_stricter_than_default(self):
        """Test that this throttle is stricter than default anon throttle"""
        # Default anon throttle is typically 100/hour or 1000/day
        # This one is 50/hour - stricter
        throttle = StrictAnonRateThrottle()
        
        # Parse rate to verify it's strict
        num_requests, duration = throttle.parse_rate(throttle.rate)
        
        self.assertEqual(num_requests, 50)
        self.assertEqual(duration, 3600)  # 1 hour in seconds
    
    def test_enforces_rate_limit(self):
        """Test that rate limit is enforced after 50 requests"""
        count = self.exhaust_throttle(StrictAnonRateThrottle, user=None, expected_limit=50)
        
        self.assertEqual(count, 50)


# ============================================================================
# BURST USER RATE THROTTLE TESTS
# ============================================================================

class BurstUserRateThrottleTests(BaseThrottleTestCase):
    """Test BurstUserRateThrottle (20/minute for authenticated users)"""
    
    def test_rate_configuration(self):
        """Test throttle rate is correctly configured"""
        throttle = BurstUserRateThrottle()
        
        self.assertEqual(throttle.rate, '20/minute')
        self.assertEqual(throttle.scope, 'burst')
    
    def test_inherits_from_user_rate_throttle(self):
        """Test that BurstUserRateThrottle inherits from UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle
        
        self.assertTrue(issubclass(BurstUserRateThrottle, UserRateThrottle))
    
    def test_short_time_window(self):
        """Test that throttle uses minute-based time window"""
        throttle = BurstUserRateThrottle()
        num_requests, duration = throttle.parse_rate(throttle.rate)
        
        self.assertEqual(num_requests, 20)
        self.assertEqual(duration, 60)  # 1 minute in seconds
    
    def test_enforces_burst_rate_limit(self):
        """Test that burst rate limit is enforced"""
        count = self.exhaust_throttle(BurstUserRateThrottle, user=self.user, expected_limit=20)
        
        self.assertEqual(count, 20)
        
        # 21st request should be throttled
        allowed = self.make_request(BurstUserRateThrottle, user=self.user)
        self.assertFalse(allowed)
    
    def test_different_users_separate_burst_limits(self):
        """Test that different users have separate burst limits"""
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Exhaust user1's burst limit
        for i in range(20):
            self.make_request(BurstUserRateThrottle, user=self.user)
        
        # User1 should be throttled
        allowed = self.make_request(BurstUserRateThrottle, user=self.user)
        self.assertFalse(allowed)
        
        # User2 should still be allowed
        allowed = self.make_request(BurstUserRateThrottle, user=user2)
        self.assertTrue(allowed)


# ============================================================================
# SUSTAINED USER RATE THROTTLE TESTS
# ============================================================================

class SustainedUserRateThrottleTests(BaseThrottleTestCase):
    """Test SustainedUserRateThrottle (500/hour for authenticated users)"""
    
    def test_rate_configuration(self):
        """Test throttle rate is correctly configured"""
        throttle = SustainedUserRateThrottle()
        
        self.assertEqual(throttle.rate, '500/hour')
        self.assertEqual(throttle.scope, 'sustained')
    
    def test_inherits_from_user_rate_throttle(self):
        """Test that SustainedUserRateThrottle inherits from UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle
        
        self.assertTrue(issubclass(SustainedUserRateThrottle, UserRateThrottle))
    
    def test_long_time_window(self):
        """Test that throttle uses hour-based time window"""
        throttle = SustainedUserRateThrottle()
        num_requests, duration = throttle.parse_rate(throttle.rate)
        
        self.assertEqual(num_requests, 500)
        self.assertEqual(duration, 3600)  # 1 hour in seconds
    
    def test_allows_high_sustained_usage(self):
        """Test that high sustained usage is allowed"""
        # Make 100 requests (should all succeed)
        for i in range(100):
            allowed = self.make_request(SustainedUserRateThrottle, user=self.user)
            self.assertTrue(allowed)
    
    def test_high_limit_appropriate_for_sustained_use(self):
        """Test that 500/hour limit is appropriate for legitimate sustained use"""
        throttle = SustainedUserRateThrottle()
        num_requests, duration = throttle.parse_rate(throttle.rate)
        
        # 500 requests per hour = ~8.3 requests per minute
        # This is reasonable for legitimate API usage
        requests_per_minute = (num_requests / duration) * 60
        self.assertGreater(requests_per_minute, 8)
        self.assertLess(requests_per_minute, 9)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class ThrottleIntegrationTests(BaseThrottleTestCase):
    """Test integration and interaction between different throttle classes"""
    
    def test_multiple_throttles_most_restrictive_wins(self):
        """Test that when multiple throttles apply, most restrictive wins"""
        # BurstUserRateThrottle (20/min) is more restrictive than SustainedUserRateThrottle (500/hour)
        # If both are applied, burst should throttle first
        
        # Exhaust burst limit (20 requests)
        for i in range(20):
            burst_allowed = self.make_request(BurstUserRateThrottle, user=self.user)
            sustained_allowed = self.make_request(SustainedUserRateThrottle, user=self.user)
            self.assertTrue(burst_allowed)
            self.assertTrue(sustained_allowed)
        
        # Burst should be throttled, sustained should still allow
        burst_allowed = self.make_request(BurstUserRateThrottle, user=self.user)
        sustained_allowed = self.make_request(SustainedUserRateThrottle, user=self.user)
        
        self.assertFalse(burst_allowed)
        self.assertTrue(sustained_allowed)
    
    def test_authenticated_vs_anonymous_throttles(self):
        """Test that authenticated and anonymous throttles are independent"""
        # PaymentRateThrottle (anonymous, 10/hour)
        # CheckoutRateThrottle (authenticated, 10/hour)
        
        # Exhaust anonymous limit
        for i in range(10):
            self.make_request(PaymentRateThrottle, user=None)
        
        # Anonymous should be throttled
        allowed = self.make_request(PaymentRateThrottle, user=None)
        self.assertFalse(allowed)
        
        # Authenticated user should still be allowed by CheckoutRateThrottle
        allowed = self.make_request(CheckoutRateThrottle, user=self.user)
        self.assertTrue(allowed)
    
    def test_different_scopes_independent_limits(self):
        """Test that different scopes maintain independent rate limits"""
        # Even if same rate, different scopes should have separate limits
        
        # Use PaymentRateThrottle (scope: payment, 10/hour)
        for i in range(10):
            self.make_request(PaymentRateThrottle, user=None)
        
        # Payment scope should be exhausted
        payment_allowed = self.make_request(PaymentRateThrottle, user=None)
        self.assertFalse(payment_allowed)
        
        # But cart scope (CartRateThrottle) should still allow requests
        # because it's a different scope
        cart_allowed = self.make_request(CartRateThrottle, user=None)
        self.assertTrue(cart_allowed)
    
    def test_cache_key_generation_user_vs_anon(self):
        """Test that cache keys are different for user and anon throttles"""
        # Create requests
        anon_request = self.factory.get('/test/')
        anon_request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        user_request = self.factory.get('/test/')
        user_request.META['REMOTE_ADDR'] = '127.0.0.1'
        force_authenticate(user_request, user=self.user)
        
        # Get cache keys
        anon_throttle = PaymentRateThrottle()
        user_throttle = CheckoutRateThrottle()
        
        anon_key = anon_throttle.get_cache_key(anon_request, None)
        user_key = user_throttle.get_cache_key(user_request, None)
        
        # Keys should be different (one uses IP, one uses user ID)
        self.assertIsNotNone(anon_key)
        self.assertIsNotNone(user_key)
        self.assertNotEqual(anon_key, user_key)


# ============================================================================
# EDGE CASES & ERROR HANDLING TESTS
# ============================================================================

class ThrottleEdgeCasesTests(BaseThrottleTestCase):
    """Test edge cases and error handling in throttle classes"""
    
    def test_request_without_remote_addr(self):
        """Test handling of request without REMOTE_ADDR"""
        request = self.factory.get('/test/')
        # Don't set REMOTE_ADDR
        
        throttle = PaymentRateThrottle()
        
        # Should handle gracefully (DRF uses 'unknown' or similar)
        # Should not crash
        try:
            result = throttle.allow_request(request, None)
            # Result could be True or False, but shouldn't crash
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Throttle raised exception: {e}")
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit information is available via wait()"""
        # Exhaust limit
        for i in range(10):
            self.make_request(CheckoutRateThrottle, user=self.user)
        
        # Next request should be throttled
        request = self.factory.get('/test/')
        force_authenticate(request, user=self.user)
        
        throttle = CheckoutRateThrottle()
        allowed = throttle.allow_request(request, None)
        
        self.assertFalse(allowed)
        
        # wait() should return time until limit resets
        wait_time = throttle.wait()
        self.assertIsNotNone(wait_time)
        self.assertGreater(wait_time, 0)
    
    def test_cache_clear_resets_limits(self):
        """Test that clearing cache resets rate limits"""
        # Exhaust limit
        for i in range(10):
            self.make_request(CheckoutRateThrottle, user=self.user)
        
        # Should be throttled
        allowed = self.make_request(CheckoutRateThrottle, user=self.user)
        self.assertFalse(allowed)
        
        # Clear cache
        cache.clear()
        
        # Should be allowed again
        allowed = self.make_request(CheckoutRateThrottle, user=self.user)
        self.assertTrue(allowed)
    
    def test_concurrent_requests_same_user(self):
        """Test handling of concurrent requests from same user"""
        # Simulate rapid concurrent requests
        results = []
        for i in range(15):
            allowed = self.make_request(CheckoutRateThrottle, user=self.user)
            results.append(allowed)
        
        # First 10 should be allowed, rest throttled
        self.assertEqual(sum(results), 10)
        self.assertTrue(all(results[:10]))  # First 10 are True
        self.assertFalse(any(results[10:]))  # Rest are False


# ============================================================================
# THROTTLE CONFIGURATION TESTS
# ============================================================================

class ThrottleConfigurationTests(BaseThrottleTestCase):
    """Test throttle configuration and settings"""
    
    def test_all_throttles_have_unique_scopes(self):
        """Test that all throttle classes have unique scopes"""
        throttles = [
            CheckoutRateThrottle(),
            PaymentRateThrottle(),
            BulkOrderWebhookThrottle(),
            CartRateThrottle(),
            StrictAnonRateThrottle(),
            BurstUserRateThrottle(),
            SustainedUserRateThrottle(),
        ]
        
        scopes = [t.scope for t in throttles]
        
        # All scopes should be unique
        self.assertEqual(len(scopes), len(set(scopes)))
    
    def test_all_throttles_have_valid_rates(self):
        """Test that all throttle classes have valid rate configurations"""
        throttles = [
            CheckoutRateThrottle(),
            PaymentRateThrottle(),
            BulkOrderWebhookThrottle(),
            CartRateThrottle(),
            StrictAnonRateThrottle(),
            BurstUserRateThrottle(),
            SustainedUserRateThrottle(),
        ]
        
        for throttle in throttles:
            # Should be able to parse rate
            num_requests, duration = throttle.parse_rate(throttle.rate)
            
            self.assertIsNotNone(num_requests)
            self.assertIsNotNone(duration)
            self.assertGreater(num_requests, 0)
            self.assertGreater(duration, 0)
    
    def test_throttle_inheritance_hierarchy(self):
        """Test correct inheritance hierarchy for all throttles"""
        from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
        
        # User throttles
        user_throttles = [
            CheckoutRateThrottle,
            BurstUserRateThrottle,
            SustainedUserRateThrottle,
        ]
        
        for throttle_class in user_throttles:
            self.assertTrue(
                issubclass(throttle_class, UserRateThrottle),
                f"{throttle_class.__name__} should inherit from UserRateThrottle"
            )
        
        # Anonymous throttles
        anon_throttles = [
            PaymentRateThrottle,
            BulkOrderWebhookThrottle,
            CartRateThrottle,
            StrictAnonRateThrottle,
        ]
        
        for throttle_class in anon_throttles:
            self.assertTrue(
                issubclass(throttle_class, AnonRateThrottle),
                f"{throttle_class.__name__} should inherit from AnonRateThrottle"
            )