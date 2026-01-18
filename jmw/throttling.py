# jmw/throttling.py
"""
Custom rate throttling classes for API endpoints
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class CheckoutRateThrottle(UserRateThrottle):
    """
    Rate limit for checkout endpoint
    Prevents rapid order creation abuse
    """
    rate = '10/hour'
    scope = 'checkout'


class PaymentRateThrottle(UserRateThrottle):
    """
    Rate limit for payment initiation
    Prevents payment spam
    """
    rate = '10/hour'
    scope = 'payment'


class CartRateThrottle(AnonRateThrottle):
    """
    Rate limit for cart operations
    Prevents cart manipulation abuse
    """
    rate = '100/hour'
    scope = 'cart'


class StrictAnonRateThrottle(AnonRateThrottle):
    """
    Strict rate limit for anonymous users
    """
    rate = '50/hour'
    scope = 'anon_strict'


class BurstUserRateThrottle(UserRateThrottle):
    """
    Burst rate limit for authenticated users
    Allows short bursts but limits sustained usage
    """
    rate = '20/minute'
    scope = 'burst'


class SustainedUserRateThrottle(UserRateThrottle):
    """
    Sustained rate limit for authenticated users
    """
    rate = '500/hour'
    scope = 'sustained'