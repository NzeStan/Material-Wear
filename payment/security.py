# payment/security.py
"""
Security utilities for payment processing
"""
import hmac
import hashlib
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def verify_paystack_signature(payload_body, signature):
    """
    Verify Paystack webhook signature
    
    Args:
        payload_body: Raw request body (bytes)
        signature: Signature from X-Paystack-Signature header
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    if not signature:
        logger.error("Webhook signature missing")
        return False
    
    try:
        # Ensure payload is bytes
        if isinstance(payload_body, str):
            payload_body = payload_body.encode('utf-8')
        
        # Get secret key
        secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
        
        # Compute expected signature
        computed_signature = hmac.new(
            secret,
            payload_body,
            hashlib.sha512
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(computed_signature, signature)
        
        if not is_valid:
            logger.warning(
                f"Invalid webhook signature. "
                f"Expected: {computed_signature[:10]}..., "
                f"Got: {signature[:10]}..."
            )
        
        return is_valid
        
    except Exception as e:
        logger.exception(f"Error verifying webhook signature: {str(e)}")
        return False


def sanitize_payment_log_data(data):
    """
    Remove sensitive fields from payment data before logging
    
    Args:
        data: Payment response data dict
        
    Returns:
        dict: Sanitized data safe for logging
    """
    if not isinstance(data, dict):
        return data
    
    # Fields that should never be logged
    sensitive_fields = [
        'authorization',
        'card',
        'customer',
        'authorization_code',
        'card_type',
        'last4',
        'exp_month',
        'exp_year',
        'bin',
        'bank',
        'channel',
        'signature',
        'account_name',
    ]
    
    # Create a copy to avoid modifying original
    sanitized = data.copy()
    
    # Recursively sanitize nested dicts
    for key, value in sanitized.items():
        if key.lower() in [f.lower() for f in sensitive_fields]:
            sanitized[key] = '[REDACTED]'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_payment_log_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_payment_log_data(item) if isinstance(item, dict) else item
                for item in value
            ]
    
    return sanitized