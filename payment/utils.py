# payment/utils.py
import json
import requests
from decimal import Decimal
from django.conf import settings
from .security import sanitize_payment_log_data  # ✅ ADD THIS
import logging

logger = logging.getLogger(__name__)

# VAT Configuration
VAT_RATE = Decimal('0.075')  # 7.5% VAT


def calculate_vat(amount):
    """
    Calculate VAT amount for a given base amount.

    Args:
        amount: The base amount (Decimal or convertible to Decimal)

    Returns:
        Decimal: The VAT amount (7.5% of the base amount)
    """
    amount = Decimal(str(amount))
    return (amount * VAT_RATE).quantize(Decimal('0.01'))


def calculate_amount_with_vat(amount):
    """
    Calculate total amount including VAT.

    Args:
        amount: The base amount (Decimal or convertible to Decimal)

    Returns:
        Decimal: The total amount including 7.5% VAT
    """
    amount = Decimal(str(amount))
    vat = calculate_vat(amount)
    return amount + vat


def get_vat_breakdown(amount):
    """
    Get a detailed VAT breakdown for an amount.

    Args:
        amount: The base amount (Decimal or convertible to Decimal)

    Returns:
        dict: Contains base_amount, vat_amount, vat_rate, and total_amount
    """
    amount = Decimal(str(amount))
    vat = calculate_vat(amount)
    return {
        'base_amount': amount,
        'vat_amount': vat,
        'vat_rate': float(VAT_RATE * 100),  # 7.5
        'total_amount': amount + vat
    }


def get_paystack_keys():
    return settings.PAYSTACK_SECRET_KEY, settings.PAYSTACK_PUBLIC_KEY


def initialize_payment(amount, email, reference, callback_url, metadata=None):
    """
    Initialize payment with Paystack
    ✅ ENHANCED: Now sanitizes logs
    """
    secret_key, _ = get_paystack_keys()

    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "amount": int(amount * 100),  # Convert to kobo
        "email": email,
        "reference": reference,
        "callback_url": callback_url,
        "metadata": metadata or {},
    }

    # ✅ Log sanitized payload
    logger.info(
        f"Initializing Paystack payment - Reference: {reference}, "
        f"Amount: {amount}, Email: {email[:3]}***"
    )

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response_data = response.json()
        
        # ✅ Log sanitized response
        logger.info(
            f"Paystack initialization response: "
            f"{sanitize_payment_log_data(response_data)}"
        )

        if not response.ok:
            logger.error(
                f"Paystack initialization error: "
                f"{response_data.get('message', 'Unknown error')}"
            )
            return None

        return response_data

    except requests.Timeout:
        logger.error("Paystack API timeout during payment initialization")
        return None
    except Exception as e:
        logger.error(f"Error initializing Paystack payment: {str(e)}")
        return None


def verify_payment(reference):
    """
    Verify payment with Paystack
    ✅ ENHANCED: Now sanitizes logs
    """
    secret_key, _ = get_paystack_keys()

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {secret_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response_data = response.json()
        
        # ✅ Log sanitized response
        logger.info(
            f"Paystack verification response for {reference}: "
            f"{sanitize_payment_log_data(response_data)}"
        )
        
        return response_data
        
    except requests.Timeout:
        logger.error(f"Paystack API timeout during verification of {reference}")
        return None
    except Exception as e:
        logger.error(f"Error verifying payment {reference}: {str(e)}")
        return None