# cart/signals.py
"""
Cart-related signal handlers
"""
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@receiver(user_logged_out)
def clear_user_cart_on_logout(sender, request, user, **kwargs):
    """
    ✅ Clear user-specific cart on logout for security
    Keep anonymous cart separate
    """
    if user and user.id:
        cart_key = f"cart_user_{user.id}"
        if cart_key in request.session:
            del request.session[cart_key]
            logger.info(f"Cleared cart for user {user.id} on logout")