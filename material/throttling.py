# material/throttling.py
"""
Custom rate throttling classes for API endpoints
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class CheckoutRateThrottle(UserRateThrottle):
    """
    Rate limit for checkout endpoint
    Prevents rapid order creation abuse
    """

    rate = "10/hour"
    scope = "checkout"


class PaymentRateThrottle(AnonRateThrottle):
    """
    Rate limit for payment webhooks
    Prevents payment spam
    """

    rate = "10/hour"
    scope = "payment"


class BulkOrderWebhookThrottle(AnonRateThrottle):
    """
    Rate limit for bulk order payment webhooks
    Prevents webhook spam attacks
    """

    rate = "100/hour"
    scope = "bulk_webhook"


class CartRateThrottle(AnonRateThrottle):
    """
    Rate limit for cart operations
    Prevents cart manipulation abuse
    """

    rate = "100/hour"
    scope = "cart"


class StrictAnonRateThrottle(AnonRateThrottle):
    """
    Strict rate limit for anonymous users
    """

    rate = "50/hour"
    scope = "anon_strict"


class BurstUserRateThrottle(UserRateThrottle):
    """
    Burst rate limit for authenticated users
    Allows short bursts but limits sustained usage
    """

    rate = "20/minute"
    scope = "burst"


class SustainedUserRateThrottle(UserRateThrottle):
    """
    Sustained rate limit for authenticated users
    """

    rate = "500/hour"
    scope = "sustained"


# ============================================================================
# LIVE FORMS — THROTTLE CLASSES
# Append these to material/throttling.py
# ============================================================================


class LiveFormSubmitThrottle(AnonRateThrottle):
    """
    Rate limit for live form entry submission.
    30 submissions per hour per IP — prevents spam flooding
    while allowing genuine group submissions from shared networks.
    """

    rate = "30/hour"
    scope = "live_form_submit"


class LiveFormViewThrottle(AnonRateThrottle):
    """
    Rate limit for live form polling (live_feed endpoint).
    200 requests per hour per IP — generous limit to support
    the 4-second polling interval (900 polls/hour max per tab).
    """

    rate = "200/hour"
    scope = "live_form_view"
