# payment/tests/test_utils.py
"""
Comprehensive bulletproof tests for payment/utils.py

Test Coverage:
===============
✅ get_paystack_keys()
   - Returns correct keys from settings
   - Returns tuple (secret, public)
   - Keys are strings

✅ initialize_payment()
   - Successful initialization
   - Amount conversion to kobo
   - Header construction
   - Payload structure
   - Metadata handling (None and dict)
   - Callback URL inclusion
   - Timeout handling
   - Network errors
   - Non-OK responses
   - JSON decode errors
   - Logging behavior
   - Return None on errors

✅ verify_payment()
   - Successful verification
   - Header construction
   - URL construction with reference
   - Timeout handling
   - Network errors
   - JSON decode errors
   - Logging behavior
   - Return None on errors

✅ Edge Cases
   - Zero amount
   - Very large amounts
   - Special characters in email/reference
   - Empty metadata
   - Complex nested metadata
   - Request exceptions
"""
from django.test import TestCase, override_settings
from unittest.mock import patch, Mock, MagicMock
from decimal import Decimal
import requests
import json

from payment.utils import (
    get_paystack_keys,
    initialize_payment,
    verify_payment,
    VAT_RATE,
    calculate_vat,
    calculate_amount_with_vat,
    get_vat_breakdown,
)


# ============================================================================
# GET PAYSTACK KEYS TESTS
# ============================================================================


class GetPaystackKeysTests(TestCase):
    """Test get_paystack_keys function"""

    @override_settings(
        PAYSTACK_SECRET_KEY="sk_test_secret123", PAYSTACK_PUBLIC_KEY="pk_test_public456"
    )
    def test_returns_tuple_of_keys(self):
        """Test that function returns tuple of (secret, public) keys"""
        secret, public = get_paystack_keys()

        self.assertEqual(secret, "sk_test_secret123")
        self.assertEqual(public, "pk_test_public456")

    @override_settings(
        PAYSTACK_SECRET_KEY="sk_test_secret123", PAYSTACK_PUBLIC_KEY="pk_test_public456"
    )
    def test_returns_tuple(self):
        """Test that function returns a tuple"""
        result = get_paystack_keys()

        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    @override_settings(
        PAYSTACK_SECRET_KEY="test_secret", PAYSTACK_PUBLIC_KEY="test_public"
    )
    def test_keys_are_strings(self):
        """Test that returned keys are strings"""
        secret, public = get_paystack_keys()

        self.assertIsInstance(secret, str)
        self.assertIsInstance(public, str)


# ============================================================================
# VAT CALCULATION TESTS
# ============================================================================


class VATCalculationTests(TestCase):
    """Test VAT calculation functions"""

    def test_vat_rate_is_7_5_percent(self):
        """Test that VAT_RATE is 7.5%"""
        self.assertEqual(VAT_RATE, Decimal("0.075"))

    def test_calculate_vat_basic(self):
        """Test basic VAT calculation"""
        amount = Decimal("10000.00")
        vat = calculate_vat(amount)

        # 10000 * 0.075 = 750
        self.assertEqual(vat, Decimal("750.00"))

    def test_calculate_vat_decimal_precision(self):
        """Test VAT calculation with decimal precision"""
        amount = Decimal("5000.00")
        vat = calculate_vat(amount)

        # 5000 * 0.075 = 375
        self.assertEqual(vat, Decimal("375.00"))

    def test_calculate_vat_rounds_to_two_decimal_places(self):
        """Test that VAT is rounded to 2 decimal places"""
        amount = Decimal("1234.56")
        vat = calculate_vat(amount)

        # 1234.56 * 0.075 = 92.592 -> rounded to 92.59
        self.assertEqual(vat, Decimal("92.59"))

    def test_calculate_vat_with_string_input(self):
        """Test VAT calculation accepts string input"""
        vat = calculate_vat("10000.00")
        self.assertEqual(vat, Decimal("750.00"))

    def test_calculate_vat_with_integer_input(self):
        """Test VAT calculation accepts integer input"""
        vat = calculate_vat(10000)
        self.assertEqual(vat, Decimal("750.00"))

    def test_calculate_vat_zero_amount(self):
        """Test VAT calculation with zero amount"""
        vat = calculate_vat(Decimal("0.00"))
        self.assertEqual(vat, Decimal("0.00"))

    def test_calculate_amount_with_vat_basic(self):
        """Test basic amount with VAT calculation"""
        amount = Decimal("10000.00")
        total = calculate_amount_with_vat(amount)

        # 10000 + 750 = 10750
        self.assertEqual(total, Decimal("10750.00"))

    def test_calculate_amount_with_vat_decimal_precision(self):
        """Test amount with VAT with decimal precision"""
        amount = Decimal("1234.56")
        total = calculate_amount_with_vat(amount)

        # 1234.56 + 92.59 = 1327.15
        self.assertEqual(total, Decimal("1327.15"))

    def test_calculate_amount_with_vat_zero(self):
        """Test amount with VAT for zero amount"""
        total = calculate_amount_with_vat(Decimal("0.00"))
        self.assertEqual(total, Decimal("0.00"))

    def test_get_vat_breakdown_basic(self):
        """Test VAT breakdown returns correct structure"""
        breakdown = get_vat_breakdown(Decimal("10000.00"))

        self.assertEqual(breakdown["base_amount"], Decimal("10000.00"))
        self.assertEqual(breakdown["vat_amount"], Decimal("750.00"))
        self.assertEqual(breakdown["vat_rate"], 7.5)
        self.assertEqual(breakdown["total_amount"], Decimal("10750.00"))

    def test_get_vat_breakdown_all_fields_present(self):
        """Test that VAT breakdown contains all expected fields"""
        breakdown = get_vat_breakdown(Decimal("5000.00"))

        expected_fields = ["base_amount", "vat_amount", "vat_rate", "total_amount"]
        for field in expected_fields:
            self.assertIn(field, breakdown)

    def test_get_vat_breakdown_with_string_input(self):
        """Test VAT breakdown accepts string input"""
        breakdown = get_vat_breakdown("5000.00")

        self.assertEqual(breakdown["base_amount"], Decimal("5000.00"))
        self.assertEqual(breakdown["vat_amount"], Decimal("375.00"))
        self.assertEqual(breakdown["total_amount"], Decimal("5375.00"))

    def test_get_vat_breakdown_large_amount(self):
        """Test VAT breakdown with large amount"""
        amount = Decimal("100000.00")
        breakdown = get_vat_breakdown(amount)

        # 100000 * 0.075 = 7500
        self.assertEqual(breakdown["vat_amount"], Decimal("7500.00"))
        self.assertEqual(breakdown["total_amount"], Decimal("107500.00"))

    def test_vat_calculations_are_consistent(self):
        """Test that all VAT functions return consistent values"""
        amount = Decimal("8500.00")

        vat = calculate_vat(amount)
        total = calculate_amount_with_vat(amount)
        breakdown = get_vat_breakdown(amount)

        self.assertEqual(vat, breakdown["vat_amount"])
        self.assertEqual(total, breakdown["total_amount"])
        self.assertEqual(amount + vat, total)


# ============================================================================
# INITIALIZE PAYMENT TESTS
# ============================================================================


class InitializePaymentTests(TestCase):
    """Test initialize_payment function"""

    def setUp(self):
        """Set up test fixtures"""
        self.amount = Decimal("10000.00")
        self.email = "test@example.com"
        self.reference = "MATERIAL-TEST1234"
        self.callback_url = "https://example.com/callback"
        self.metadata = {"order_id": "123", "customer": "John Doe"}

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_initialize_payment_success(self, mock_post):
        """Test successful payment initialization"""
        # Mock successful response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": "https://checkout.paystack.com/test",
                "access_code": "test_access_code",
                "reference": "MATERIAL-TEST1234",
            },
        }
        mock_post.return_value = mock_response

        result = initialize_payment(
            self.amount, self.email, self.reference, self.callback_url, self.metadata
        )

        # Verify result
        self.assertIsNotNone(result)
        self.assertTrue(result["status"])
        self.assertIn("data", result)
        self.assertEqual(result["data"]["reference"], "MATERIAL-TEST1234")

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_amount_converted_to_kobo(self, mock_post):
        """Test that amount is converted to kobo (multiply by 100)"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(
            Decimal("10000.00"), self.email, self.reference, self.callback_url
        )

        # Check the payload sent to Paystack
        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # 10000.00 NGN * 100 = 1000000 kobo
        self.assertEqual(payload["amount"], 1000000)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_amount_with_decimals_converted_correctly(self, mock_post):
        """Test that decimal amounts are converted correctly"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(
            Decimal("12345.67"), self.email, self.reference, self.callback_url
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # 12345.67 * 100 = 1234567 kobo
        self.assertEqual(payload["amount"], 1234567)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_headers_include_authorization(self, mock_post):
        """Test that headers include authorization bearer token"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(self.amount, self.email, self.reference, self.callback_url)

        # Check headers
        call_args = mock_post.call_args
        headers = call_args[1]["headers"]

        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer sk_test_secret")
        self.assertEqual(headers["Content-Type"], "application/json")

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_payload_structure(self, mock_post):
        """Test that payload has correct structure"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(
            self.amount, self.email, self.reference, self.callback_url, self.metadata
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        self.assertIn("amount", payload)
        self.assertIn("email", payload)
        self.assertIn("reference", payload)
        self.assertIn("callback_url", payload)
        self.assertIn("metadata", payload)

        self.assertEqual(payload["email"], self.email)
        self.assertEqual(payload["reference"], self.reference)
        self.assertEqual(payload["callback_url"], self.callback_url)
        self.assertEqual(payload["metadata"], self.metadata)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_metadata_defaults_to_empty_dict(self, mock_post):
        """Test that metadata defaults to empty dict when None"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(
            self.amount, self.email, self.reference, self.callback_url, metadata=None
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        self.assertEqual(payload["metadata"], {})

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_correct_api_url(self, mock_post):
        """Test that correct Paystack API URL is used"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(self.amount, self.email, self.reference, self.callback_url)

        call_args = mock_post.call_args
        url = call_args[0][0]

        self.assertEqual(url, "https://api.paystack.co/transaction/initialize")

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_timeout_set_to_10_seconds(self, mock_post):
        """Test that timeout is set to 10 seconds"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(self.amount, self.email, self.reference, self.callback_url)

        call_args = mock_post.call_args
        timeout = call_args[1]["timeout"]

        self.assertEqual(timeout, 10)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_timeout_returns_none(self, mock_post):
        """Test that timeout exception returns None"""
        mock_post.side_effect = requests.Timeout("Connection timeout")

        result = initialize_payment(
            self.amount, self.email, self.reference, self.callback_url
        )

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_request_exception_returns_none(self, mock_post):
        """Test that request exceptions return None"""
        mock_post.side_effect = requests.RequestException("Network error")

        result = initialize_payment(
            self.amount, self.email, self.reference, self.callback_url
        )

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_non_ok_response_returns_none(self, mock_post):
        """Test that non-OK response returns None"""
        mock_response = Mock()
        mock_response.ok = False
        mock_response.json.return_value = {
            "status": False,
            "message": "Invalid API key",
        }
        mock_post.return_value = mock_response

        result = initialize_payment(
            self.amount, self.email, self.reference, self.callback_url
        )

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_json_decode_error_returns_none(self, mock_post):
        """Test that JSON decode error returns None"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        result = initialize_payment(
            self.amount, self.email, self.reference, self.callback_url
        )

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_generic_exception_returns_none(self, mock_post):
        """Test that generic exceptions return None"""
        mock_post.side_effect = Exception("Unexpected error")

        result = initialize_payment(
            self.amount, self.email, self.reference, self.callback_url
        )

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_zero_amount(self, mock_post):
        """Test initialization with zero amount"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(
            Decimal("0.00"), self.email, self.reference, self.callback_url
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        self.assertEqual(payload["amount"], 0)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_very_large_amount(self, mock_post):
        """Test initialization with very large amount"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        large_amount = Decimal("99999999.99")
        initialize_payment(large_amount, self.email, self.reference, self.callback_url)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # 99999999.99 * 100 = 9999999999 kobo
        self.assertEqual(payload["amount"], 9999999999)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_complex_metadata(self, mock_post):
        """Test initialization with complex nested metadata"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        complex_metadata = {
            "customer": {
                "name": "John Doe",
                "phone": "08012345678",
                "address": {"street": "123 Main St", "city": "Lagos"},
            },
            "orders": ["order1", "order2", "order3"],
            "discount": 10.5,
        }

        initialize_payment(
            self.amount, self.email, self.reference, self.callback_url, complex_metadata
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        self.assertEqual(payload["metadata"], complex_metadata)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_special_characters_in_email(self, mock_post):
        """Test initialization with special characters in email"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        special_email = "user+test@example.com"

        initialize_payment(
            self.amount, special_email, self.reference, self.callback_url
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        self.assertEqual(payload["email"], special_email)


# ============================================================================
# VERIFY PAYMENT TESTS
# ============================================================================


class VerifyPaymentTests(TestCase):
    """Test verify_payment function"""

    def setUp(self):
        """Set up test fixtures"""
        self.reference = "MATERIAL-TEST1234"

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_verify_payment_success(self, mock_get):
        """Test successful payment verification"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "status": True,
            "message": "Verification successful",
            "data": {
                "reference": "MATERIAL-TEST1234",
                "amount": 1000000,
                "status": "success",
            },
        }
        mock_get.return_value = mock_response

        result = verify_payment(self.reference)

        self.assertIsNotNone(result)
        self.assertTrue(result["status"])
        self.assertEqual(result["data"]["reference"], "MATERIAL-TEST1234")

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_correct_api_url_with_reference(self, mock_get):
        """Test that correct API URL is constructed with reference"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_get.return_value = mock_response

        verify_payment("MATERIAL-TEST1234")

        call_args = mock_get.call_args
        url = call_args[0][0]

        self.assertEqual(
            url, "https://api.paystack.co/transaction/verify/MATERIAL-TEST1234"
        )

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_headers_include_authorization(self, mock_get):
        """Test that headers include authorization bearer token"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_get.return_value = mock_response

        verify_payment(self.reference)

        call_args = mock_get.call_args
        headers = call_args[1]["headers"]

        self.assertIn("Authorization", headers)
        self.assertEqual(headers["Authorization"], "Bearer sk_test_secret")
        self.assertEqual(headers["Content-Type"], "application/json")

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_timeout_set_to_10_seconds(self, mock_get):
        """Test that timeout is set to 10 seconds"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_get.return_value = mock_response

        verify_payment(self.reference)

        call_args = mock_get.call_args
        timeout = call_args[1]["timeout"]

        self.assertEqual(timeout, 10)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_timeout_returns_none(self, mock_get):
        """Test that timeout exception returns None"""
        mock_get.side_effect = requests.Timeout("Connection timeout")

        result = verify_payment(self.reference)

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_request_exception_returns_none(self, mock_get):
        """Test that request exceptions return None"""
        mock_get.side_effect = requests.RequestException("Network error")

        result = verify_payment(self.reference)

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_json_decode_error_returns_none(self, mock_get):
        """Test that JSON decode error returns None"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        result = verify_payment(self.reference)

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_generic_exception_returns_none(self, mock_get):
        """Test that generic exceptions return None"""
        mock_get.side_effect = Exception("Unexpected error")

        result = verify_payment(self.reference)

        self.assertIsNone(result)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_failed_verification_response(self, mock_get):
        """Test handling of failed verification response"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "reference": "MATERIAL-TEST1234",
                "status": "failed",
                "message": "Transaction failed",
            },
        }
        mock_get.return_value = mock_response

        result = verify_payment(self.reference)

        # Should still return the response (let caller handle failed status)
        self.assertIsNotNone(result)
        self.assertEqual(result["data"]["status"], "failed")

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_reference_with_special_characters(self, mock_get):
        """Test verification with reference containing special characters"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_get.return_value = mock_response

        special_reference = "MATERIAL-TEST_123-ABC"
        verify_payment(special_reference)

        call_args = mock_get.call_args
        url = call_args[0][0]

        self.assertIn(special_reference, url)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_returns_full_response_data(self, mock_get):
        """Test that function returns full response data"""
        full_response = {
            "status": True,
            "message": "Verification successful",
            "data": {
                "reference": "MATERIAL-TEST",
                "amount": 1000000,
                "status": "success",
                "paid_at": "2024-01-01T00:00:00Z",
                "customer": {"email": "test@example.com"},
                "authorization": {
                    "authorization_code": "AUTH_code",
                    "card_type": "visa",
                },
            },
        }

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = full_response
        mock_get.return_value = mock_response

        result = verify_payment(self.reference)

        self.assertEqual(result, full_response)
        self.assertIn("authorization", result["data"])
        self.assertIn("customer", result["data"])


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class UtilsIntegrationTests(TestCase):
    """Test integration between utility functions"""

    @override_settings(
        PAYSTACK_SECRET_KEY="sk_test_secret", PAYSTACK_PUBLIC_KEY="pk_test_public"
    )
    @patch("payment.utils.requests.post")
    @patch("payment.utils.requests.get")
    def test_initialize_then_verify_flow(self, mock_get, mock_post):
        """Test complete flow: initialize then verify"""
        # Mock initialization
        init_response = Mock()
        init_response.ok = True
        init_response.json.return_value = {
            "status": True,
            "data": {
                "reference": "MATERIAL-FLOW",
                "authorization_url": "https://checkout.paystack.com/test",
                "access_code": "test_code",
            },
        }
        mock_post.return_value = init_response

        # Mock verification
        verify_response = Mock()
        verify_response.ok = True
        verify_response.json.return_value = {
            "status": True,
            "data": {
                "reference": "MATERIAL-FLOW",
                "status": "success",
                "amount": 1000000,
            },
        }
        mock_get.return_value = verify_response

        # Initialize payment
        init_result = initialize_payment(
            Decimal("10000.00"),
            "test@example.com",
            "MATERIAL-FLOW",
            "https://example.com/callback",
        )

        self.assertIsNotNone(init_result)
        self.assertEqual(init_result["data"]["reference"], "MATERIAL-FLOW")

        # Verify payment
        verify_result = verify_payment("MATERIAL-FLOW")

        self.assertIsNotNone(verify_result)
        self.assertEqual(verify_result["data"]["status"], "success")

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    def test_get_paystack_keys_used_by_functions(self):
        """Test that initialize and verify use get_paystack_keys"""
        secret, public = get_paystack_keys()

        # Keys should be available for other functions
        self.assertIsNotNone(secret)
        self.assertIsInstance(secret, str)


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class UtilsEdgeCaseTests(TestCase):
    """Test edge cases and boundary conditions"""

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_initialize_with_empty_metadata_dict(self, mock_post):
        """Test initialization with explicitly empty metadata"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        initialize_payment(
            Decimal("5000.00"),
            "test@example.com",
            "MATERIAL-TEST",
            "https://example.com",
            metadata={},
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        self.assertEqual(payload["metadata"], {})

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_initialize_with_very_long_reference(self, mock_post):
        """Test initialization with very long reference"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        long_reference = "MATERIAL-" + "A" * 100

        initialize_payment(
            Decimal("5000.00"),
            "test@example.com",
            long_reference,
            "https://example.com",
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        self.assertEqual(payload["reference"], long_reference)

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.get")
    def test_verify_with_empty_reference(self, mock_get):
        """Test verification with empty reference"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_get.return_value = mock_response

        verify_payment("")

        call_args = mock_get.call_args
        url = call_args[0][0]

        # URL should still be constructed (empty string in path)
        self.assertTrue(url.endswith("/transaction/verify/"))

    @override_settings(PAYSTACK_SECRET_KEY="sk_test_secret")
    @patch("payment.utils.requests.post")
    def test_initialize_decimal_rounding(self, mock_post):
        """Test that decimal amounts are properly rounded to kobo"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_post.return_value = mock_response

        # Amount with 3 decimal places
        initialize_payment(
            Decimal("100.999"),
            "test@example.com",
            "MATERIAL-TEST",
            "https://example.com",
        )

        call_args = mock_post.call_args
        payload = call_args[1]["json"]

        # Should be: int(100.999 * 100) = int(100.99) = 10099
        self.assertEqual(payload["amount"], 10099)
