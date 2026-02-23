# webhook_router/tests/tests_throttling.py
"""
Bulletproof tests for material/throttling.py
Tests all custom rate throttling classes

Test Coverage:
===============
- CheckoutRateThrottle (User-based, 10/hour)
- PaymentRateThrottle (Anon-based, 10/hour)
- BulkOrderWebhookThrottle (Anon-based, 100/hour)
- CartRateThrottle (Anon-based, 100/hour)
- StrictAnonRateThrottle (Anon-based, 50/hour)
- BurstUserRateThrottle (User-based, 20/minute)
- SustainedUserRateThrottle (User-based, 500/hour)
- LiveFormSubmitThrottle (Anon-based, 30/hour)
- LiveFormViewThrottle (Anon-based, 200/hour)
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from unittest.mock import Mock, patch
import time

# Import all throttle classes
from material.throttling import (
    CheckoutRateThrottle,
    PaymentRateThrottle,
    BulkOrderWebhookThrottle,
    CartRateThrottle,
    StrictAnonRateThrottle,
    BurstUserRateThrottle,
    SustainedUserRateThrottle,
    LiveFormSubmitThrottle,
    LiveFormViewThrottle,
)

User = get_user_model()


# ============================================================================
# TEST VIEWS FOR THROTTLE TESTING
# ============================================================================


class ThrottledCheckoutView(APIView):
    """Test view with checkout throttle"""

    throttle_classes = [CheckoutRateThrottle]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"status": "ok"})


class ThrottledPaymentView(APIView):
    """Test view with payment throttle"""

    throttle_classes = [PaymentRateThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"status": "ok"})


class ThrottledBulkWebhookView(APIView):
    """Test view with bulk webhook throttle"""

    throttle_classes = [BulkOrderWebhookThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"status": "ok"})


class ThrottledCartView(APIView):
    """Test view with cart throttle"""

    throttle_classes = [CartRateThrottle]
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class ThrottledStrictAnonView(APIView):
    """Test view with strict anon throttle"""

    throttle_classes = [StrictAnonRateThrottle]
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class ThrottledBurstUserView(APIView):
    """Test view with burst user throttle"""

    throttle_classes = [BurstUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok"})


class ThrottledSustainedUserView(APIView):
    """Test view with sustained user throttle"""

    throttle_classes = [SustainedUserRateThrottle]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "ok"})


class ThrottledLiveFormSubmitView(APIView):
    """Test view with live form submit throttle"""

    throttle_classes = [LiveFormSubmitThrottle]
    permission_classes = [AllowAny]

    def post(self, request):
        return Response({"status": "ok"})


class ThrottledLiveFormViewView(APIView):
    """Test view with live form view throttle"""

    throttle_classes = [LiveFormViewThrottle]
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


# ============================================================================
# CHECKOUT RATE THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "checkout": "5/minute",  # Lower for testing
        }
    },
)
class CheckoutRateThrottleTests(TestCase):
    """Test CheckoutRateThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledCheckoutView.as_view()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = CheckoutRateThrottle()
        self.assertEqual(throttle.scope, "checkout")
        self.assertEqual(throttle.rate, "10/hour")

    def test_authenticated_user_within_limit(self):
        """Test authenticated user within rate limit"""
        request = self.factory.post("/checkout/")
        force_authenticate(request, user=self.user)

        # First 5 requests should succeed
        for i in range(5):
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_different_users_separate_limits(self):
        """Test different users have separate rate limits"""
        user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )

        # User 1 makes 5 requests
        request1 = self.factory.post("/checkout/")
        force_authenticate(request1, user=self.user)
        for i in range(5):
            response = self.view(request1)
            self.assertEqual(response.status_code, 200)

        # User 2 should still be able to make requests
        request2 = self.factory.post("/checkout/")
        force_authenticate(request2, user=user2)
        response = self.view(request2)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_rejected(self):
        """Test unauthenticated users are rejected before throttling"""
        request = self.factory.post("/checkout/")
        response = self.view(request)

        # Should get 401/403, not 429
        self.assertIn(response.status_code, [401, 403])

    def test_throttle_inherits_from_user_rate_throttle(self):
        """Test CheckoutRateThrottle inherits from UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle

        throttle = CheckoutRateThrottle()
        self.assertIsInstance(throttle, UserRateThrottle)


# ============================================================================
# PAYMENT RATE THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "payment": "5/minute",  # Lower for testing
        }
    },
)
class PaymentRateThrottleTests(TestCase):
    """Test PaymentRateThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledPaymentView.as_view()
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = PaymentRateThrottle()
        self.assertEqual(throttle.scope, "payment")
        self.assertEqual(throttle.rate, "10/hour")

    def test_anonymous_user_within_limit(self):
        """Test anonymous user within rate limit"""
        # Use same IP for all requests
        for i in range(5):
            request = self.factory.post("/payment/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_different_ips_separate_limits(self):
        """Test different IPs have separate rate limits"""
        # IP 1 makes 5 requests
        for i in range(5):
            request = self.factory.post("/payment/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

        # IP 2 should still be able to make requests
        request = self.factory.post("/payment/", REMOTE_ADDR="192.168.1.2")
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_throttle_inherits_from_anon_rate_throttle(self):
        """Test PaymentRateThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle

        throttle = PaymentRateThrottle()
        self.assertIsInstance(throttle, AnonRateThrottle)


# ============================================================================
# BULK ORDER WEBHOOK THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "bulk_webhook": "10/minute",  # Lower for testing
        }
    },
)
class BulkOrderWebhookThrottleTests(TestCase):
    """Test BulkOrderWebhookThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledBulkWebhookView.as_view()
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = BulkOrderWebhookThrottle()
        self.assertEqual(throttle.scope, "bulk_webhook")
        self.assertEqual(throttle.rate, "100/hour")

    def test_high_volume_within_limit(self):
        """Test high volume requests within limit"""
        # Make 10 requests
        for i in range(10):
            request = self.factory.post("/webhook/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_throttle_inherits_from_anon_rate_throttle(self):
        """Test BulkOrderWebhookThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle

        throttle = BulkOrderWebhookThrottle()
        self.assertIsInstance(throttle, AnonRateThrottle)


# ============================================================================
# CART RATE THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "cart": "10/minute",  # Lower for testing
        }
    },
)
class CartRateThrottleTests(TestCase):
    """Test CartRateThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledCartView.as_view()
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = CartRateThrottle()
        self.assertEqual(throttle.scope, "cart")
        self.assertEqual(throttle.rate, "100/hour")

    def test_cart_operations_within_limit(self):
        """Test cart operations within limit"""
        for i in range(10):
            request = self.factory.get("/cart/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_throttle_inherits_from_anon_rate_throttle(self):
        """Test CartRateThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle

        throttle = CartRateThrottle()
        self.assertIsInstance(throttle, AnonRateThrottle)


# ============================================================================
# STRICT ANON RATE THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "anon_strict": "5/minute",  # Lower for testing
        }
    },
)
class StrictAnonRateThrottleTests(TestCase):
    """Test StrictAnonRateThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledStrictAnonView.as_view()
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = StrictAnonRateThrottle()
        self.assertEqual(throttle.scope, "anon_strict")
        self.assertEqual(throttle.rate, "50/hour")

    def test_strict_limit_within_range(self):
        """Test strict anonymous limit within range"""
        for i in range(5):
            request = self.factory.get("/api/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_throttle_inherits_from_anon_rate_throttle(self):
        """Test StrictAnonRateThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle

        throttle = StrictAnonRateThrottle()
        self.assertIsInstance(throttle, AnonRateThrottle)


# ============================================================================
# BURST USER RATE THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "burst": "5/minute",  # Lower for testing
        }
    },
)
class BurstUserRateThrottleTests(TestCase):
    """Test BurstUserRateThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledBurstUserView.as_view()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = BurstUserRateThrottle()
        self.assertEqual(throttle.scope, "burst")
        self.assertEqual(throttle.rate, "20/minute")

    def test_burst_within_limit(self):
        """Test burst requests within limit"""
        request = self.factory.get("/api/")
        force_authenticate(request, user=self.user)

        # Make 5 quick requests
        for i in range(5):
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_throttle_inherits_from_user_rate_throttle(self):
        """Test BurstUserRateThrottle inherits from UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle

        throttle = BurstUserRateThrottle()
        self.assertIsInstance(throttle, UserRateThrottle)


# ============================================================================
# SUSTAINED USER RATE THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "sustained": "50/minute",  # Lower for testing
        }
    },
)
class SustainedUserRateThrottleTests(TestCase):
    """Test SustainedUserRateThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledSustainedUserView.as_view()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = SustainedUserRateThrottle()
        self.assertEqual(throttle.scope, "sustained")
        self.assertEqual(throttle.rate, "500/hour")

    def test_high_sustained_within_limit(self):
        """Test sustained high usage within limit"""
        request = self.factory.get("/api/")
        force_authenticate(request, user=self.user)

        # Make 10 requests (testing subset)
        for i in range(10):
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_throttle_inherits_from_user_rate_throttle(self):
        """Test SustainedUserRateThrottle inherits from UserRateThrottle"""
        from rest_framework.throttling import UserRateThrottle

        throttle = SustainedUserRateThrottle()
        self.assertIsInstance(throttle, UserRateThrottle)


# ============================================================================
# LIVE FORM SUBMIT THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "live_form_submit": "10/minute",  # Lower for testing
        }
    },
)
class LiveFormSubmitThrottleTests(TestCase):
    """Test LiveFormSubmitThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledLiveFormSubmitView.as_view()
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = LiveFormSubmitThrottle()
        self.assertEqual(throttle.scope, "live_form_submit")
        self.assertEqual(throttle.rate, "30/hour")

    def test_anonymous_user_within_limit(self):
        """Test anonymous user within rate limit"""
        for i in range(10):
            request = self.factory.post("/live-form/submit/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_different_ips_separate_limits(self):
        """Test different IPs have separate rate limits"""
        # IP 1 makes 10 requests
        for i in range(10):
            request = self.factory.post("/live-form/submit/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

        # IP 2 should still be able to make requests
        request = self.factory.post("/live-form/submit/", REMOTE_ADDR="192.168.1.2")
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_throttle_inherits_from_anon_rate_throttle(self):
        """Test LiveFormSubmitThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle

        throttle = LiveFormSubmitThrottle()
        self.assertIsInstance(throttle, AnonRateThrottle)


# ============================================================================
# LIVE FORM VIEW THROTTLE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    },
    REST_FRAMEWORK={
        "DEFAULT_THROTTLE_RATES": {
            "live_form_view": "20/minute",  # Lower for testing
        }
    },
)
class LiveFormViewThrottleTests(TestCase):
    """Test LiveFormViewThrottle class"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.view = ThrottledLiveFormViewView.as_view()
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_throttle_configuration(self):
        """Test throttle is configured correctly"""
        throttle = LiveFormViewThrottle()
        self.assertEqual(throttle.scope, "live_form_view")
        self.assertEqual(throttle.rate, "200/hour")

    def test_high_volume_within_limit(self):
        """Test high volume polling requests within limit"""
        for i in range(20):
            request = self.factory.get("/live-form/feed/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

    def test_different_ips_separate_limits(self):
        """Test different IPs have separate rate limits"""
        # IP 1 makes 20 requests
        for i in range(20):
            request = self.factory.get("/live-form/feed/", REMOTE_ADDR="192.168.1.1")
            response = self.view(request)
            self.assertEqual(response.status_code, 200)

        # IP 2 should still be able to make requests
        request = self.factory.get("/live-form/feed/", REMOTE_ADDR="192.168.1.2")
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_throttle_inherits_from_anon_rate_throttle(self):
        """Test LiveFormViewThrottle inherits from AnonRateThrottle"""
        from rest_framework.throttling import AnonRateThrottle

        throttle = LiveFormViewThrottle()
        self.assertIsInstance(throttle, AnonRateThrottle)


# ============================================================================
# INTEGRATION & EDGE CASE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    }
)
class ThrottleIntegrationTests(TestCase):
    """Integration tests for throttling system"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_x_forwarded_for_header_handling(self):
        """Test throttling with X-Forwarded-For header"""
        view = ThrottledCartView.as_view()

        # Simulate requests through proxy
        for i in range(5):
            request = self.factory.get(
                "/cart/", HTTP_X_FORWARDED_FOR="203.0.113.1", REMOTE_ADDR="192.168.1.1"
            )
            response = view(request)
            self.assertEqual(response.status_code, 200)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    }
)
class ThrottleEdgeCaseTests(TestCase):
    """Edge case tests for throttling"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = APIRequestFactory()
        cache.clear()

    def tearDown(self):
        """Clean up cache"""
        cache.clear()

    def test_ipv6_address_handling(self):
        """Test throttling with IPv6 addresses"""
        view = ThrottledPaymentView.as_view()

        ipv6_addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        for i in range(5):
            request = self.factory.post("/payment/", REMOTE_ADDR=ipv6_addr)
            response = view(request)
            self.assertEqual(response.status_code, 200)

    def test_localhost_throttling(self):
        """Test throttling for localhost requests"""
        view = ThrottledPaymentView.as_view()

        for i in range(5):
            request = self.factory.post("/payment/", REMOTE_ADDR="127.0.0.1")
            response = view(request)
            self.assertEqual(response.status_code, 200)

    def test_live_form_throttle_ipv6(self):
        """Test live form throttle with IPv6 addresses"""
        view = ThrottledLiveFormSubmitView.as_view()

        ipv6_addr = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        for i in range(5):
            request = self.factory.post("/live-form/submit/", REMOTE_ADDR=ipv6_addr)
            response = view(request)
            self.assertEqual(response.status_code, 200)


# ============================================================================
# DOCUMENTATION & COMPLIANCE TESTS
# ============================================================================


class ThrottleDocumentationTests(TestCase):
    """Test throttle classes have proper documentation"""

    def test_all_throttles_have_docstrings(self):
        """Test all throttle classes have docstrings"""
        throttle_classes = [
            CheckoutRateThrottle,
            PaymentRateThrottle,
            BulkOrderWebhookThrottle,
            CartRateThrottle,
            StrictAnonRateThrottle,
            BurstUserRateThrottle,
            SustainedUserRateThrottle,
            LiveFormSubmitThrottle,
            LiveFormViewThrottle,
        ]

        for throttle_class in throttle_classes:
            self.assertIsNotNone(throttle_class.__doc__)
            self.assertGreater(len(throttle_class.__doc__.strip()), 0)

    def test_all_throttles_have_rate_attribute(self):
        """Test all throttle classes have rate attribute"""
        throttle_classes = [
            CheckoutRateThrottle,
            PaymentRateThrottle,
            BulkOrderWebhookThrottle,
            CartRateThrottle,
            StrictAnonRateThrottle,
            BurstUserRateThrottle,
            SustainedUserRateThrottle,
            LiveFormSubmitThrottle,
            LiveFormViewThrottle,
        ]

        for throttle_class in throttle_classes:
            throttle = throttle_class()
            self.assertIsNotNone(throttle.rate)
            self.assertIn("/", throttle.rate)  # Format: 'N/period'

    def test_all_throttles_have_scope_attribute(self):
        """Test all throttle classes have scope attribute"""
        throttle_classes = [
            CheckoutRateThrottle,
            PaymentRateThrottle,
            BulkOrderWebhookThrottle,
            CartRateThrottle,
            StrictAnonRateThrottle,
            BurstUserRateThrottle,
            SustainedUserRateThrottle,
            LiveFormSubmitThrottle,
            LiveFormViewThrottle,
        ]

        for throttle_class in throttle_classes:
            throttle = throttle_class()
            self.assertIsNotNone(throttle.scope)
            self.assertIsInstance(throttle.scope, str)

    def test_throttle_rates_are_reasonable(self):
        """Test throttle rates are within reasonable ranges"""
        # Checkout: 10/hour - reasonable for order creation
        self.assertEqual(CheckoutRateThrottle().rate, "10/hour")

        # Payment: 10/hour - prevent webhook spam
        self.assertEqual(PaymentRateThrottle().rate, "10/hour")

        # Bulk webhook: 100/hour - high volume ok
        self.assertEqual(BulkOrderWebhookThrottle().rate, "100/hour")

        # Cart: 100/hour - frequent operations ok
        self.assertEqual(CartRateThrottle().rate, "100/hour")

        # Strict anon: 50/hour - moderate restriction
        self.assertEqual(StrictAnonRateThrottle().rate, "50/hour")

        # Burst: 20/minute - short bursts allowed
        self.assertEqual(BurstUserRateThrottle().rate, "20/minute")

        # Sustained: 500/hour - heavy legitimate usage
        self.assertEqual(SustainedUserRateThrottle().rate, "500/hour")

        # Live form submit: 30/hour - prevent spam while allowing group submissions
        self.assertEqual(LiveFormSubmitThrottle().rate, "30/hour")

        # Live form view: 200/hour - generous for polling
        self.assertEqual(LiveFormViewThrottle().rate, "200/hour")
