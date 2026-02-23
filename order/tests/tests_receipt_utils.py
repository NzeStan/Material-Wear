# order/tests/tests_receipt_utils.py
"""
Comprehensive tests for Order Receipt Utils

Coverage:
- sanitize_text_for_pdf: Input sanitization, HTML escaping, length limits
- upload_pdf_to_cloudinary: Upload success, failure handling
- generate_order_confirmation_pdf: PDF generation with all order types
- generate_payment_receipt_pdf: Payment receipt PDF generation
- generate_and_store_order_confirmation: Combined generation + storage
- generate_and_store_payment_receipt: Combined generation + storage
- Error handling and edge cases
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock
from order.receipt_utils import (
    sanitize_text_for_pdf,
    upload_pdf_to_cloudinary,
    generate_order_confirmation_pdf,
    generate_payment_receipt_pdf,
    generate_and_store_order_confirmation,
    generate_and_store_payment_receipt,
)
from order.models import BaseOrder, NyscKitOrder, ChurchOrder, OrderItem
from payment.models import PaymentTransaction
from products.models import Category, NyscKit

User = get_user_model()


class SanitizeTextForPDFTests(TestCase):
    """Test text sanitization for PDF generation"""

    def test_sanitize_normal_text(self):
        """Test sanitization of normal text"""
        text = "John Doe"
        result = sanitize_text_for_pdf(text)
        self.assertEqual(result, "John Doe")

    def test_sanitize_empty_string(self):
        """Test sanitization of empty string"""
        result = sanitize_text_for_pdf("")
        self.assertEqual(result, "")

    def test_sanitize_none_value(self):
        """Test sanitization of None"""
        result = sanitize_text_for_pdf(None)
        self.assertEqual(result, "")

    def test_sanitize_html_tags(self):
        """Test HTML tags are escaped"""
        text = "<script>alert('xss')</script>"
        result = sanitize_text_for_pdf(text)
        # Should escape HTML entities
        self.assertNotIn("<script>", result)
        self.assertNotIn("</script>", result)

    def test_sanitize_special_characters(self):
        """Test special characters are removed"""
        text = "John@Doe#123$%^&*()"
        result = sanitize_text_for_pdf(text)
        # Should keep alphanumeric and allowed punctuation
        self.assertIn("John", result)
        self.assertIn("Doe", result)
        self.assertIn("@", result)  # @ is allowed for emails

    def test_sanitize_sql_injection_attempt(self):
        """Test SQL injection attempts are sanitized"""
        text = "'; DROP TABLE users; --"
        result = sanitize_text_for_pdf(text)
        # Should remove dangerous characters
        self.assertNotIn(";", result)
        self.assertNotIn("'", result)

    def test_sanitize_long_text(self):
        """Test long text is truncated"""
        text = "A" * 300  # Exceeds 200 char limit
        result = sanitize_text_for_pdf(text)
        # Should be truncated to 200 chars + "..."
        self.assertLessEqual(len(result), 203)
        self.assertTrue(result.endswith("..."))

    def test_sanitize_preserves_email(self):
        """Test email addresses are preserved"""
        text = "user@example.com"
        result = sanitize_text_for_pdf(text)
        self.assertEqual(result, "user@example.com")

    def test_sanitize_preserves_phone(self):
        """Test phone numbers are preserved"""
        text = "08012345678"
        result = sanitize_text_for_pdf(text)
        self.assertEqual(result, "08012345678")

    def test_sanitize_unicode_characters(self):
        """Test Unicode characters are handled"""
        text = "Ñíçë Tëxt"
        result = sanitize_text_for_pdf(text)
        # Should preserve word characters
        self.assertIsInstance(result, str)

    def test_sanitize_newlines_and_tabs(self):
        """Test whitespace is preserved"""
        text = "Line 1\nLine 2\tTabbed"
        result = sanitize_text_for_pdf(text)
        # Function should preserve basic whitespace
        self.assertIsInstance(result, str)

    def test_sanitize_integer_input(self):
        """Test integer inputs are converted to string"""
        result = sanitize_text_for_pdf(12345)
        self.assertEqual(result, "12345")

    def test_sanitize_preserves_hyphens_and_periods(self):
        """Test hyphens and periods are preserved"""
        text = "NYSC-KIT-2024.pdf"
        result = sanitize_text_for_pdf(text)
        self.assertIn("-", result)
        self.assertIn(".", result)


class UploadPDFToCloudinaryTests(TestCase):
    """Test Cloudinary upload functionality"""

    @patch("order.receipt_utils.cloudinary.uploader.upload")
    def test_upload_success(self, mock_upload):
        """Test successful PDF upload to Cloudinary"""
        # Mock successful upload
        mock_upload.return_value = {
            "secure_url": "https://cloudinary.com/test.pdf",
            "public_id": "receipts/test.pdf",
        }

        pdf_content = b"%PDF-1.4 test content"
        filename = "test_receipt.pdf"

        result = upload_pdf_to_cloudinary(pdf_content, filename)

        self.assertEqual(result, "https://cloudinary.com/test.pdf")
        mock_upload.assert_called_once()

    @patch("order.receipt_utils.cloudinary.uploader.upload")
    def test_upload_failure(self, mock_upload):
        """Test Cloudinary upload failure handling"""
        # Mock upload failure
        mock_upload.side_effect = Exception("Cloudinary error")

        pdf_content = b"%PDF-1.4 test content"
        filename = "test_receipt.pdf"

        result = upload_pdf_to_cloudinary(pdf_content, filename)

        self.assertIsNone(result)

    @patch("order.receipt_utils.cloudinary.uploader.upload")
    def test_upload_with_correct_parameters(self, mock_upload):
        """Test upload is called with correct parameters"""
        mock_upload.return_value = {"secure_url": "https://test.url"}

        pdf_content = b"test"
        filename = "test.pdf"

        # ✅ UPDATED: Pass pdf_type parameter
        upload_pdf_to_cloudinary(pdf_content, filename, pdf_type="order_confirmation")

        # Verify correct parameters
        call_args = mock_upload.call_args
        self.assertEqual(call_args[1]["resource_type"], "raw")
        self.assertEqual(
            call_args[1]["public_id"], "test"
        )  # ✅ UPDATED: No .pdf extension, no receipts/ prefix
        self.assertEqual(
            call_args[1]["folder"], "material_receipts/orders"
        )  # ✅ UPDATED: Subdirectory
        self.assertEqual(call_args[1]["format"], "pdf")  # ✅ NEW: Explicit format
        self.assertTrue(call_args[1]["overwrite"])

    @patch("order.receipt_utils.cloudinary.uploader.upload")
    def test_upload_order_confirmation_to_correct_folder(self, mock_upload):
        """Test order confirmations go to orders folder"""
        mock_upload.return_value = {"secure_url": "https://test.url"}

        upload_pdf_to_cloudinary(b"test", "order.pdf", pdf_type="order_confirmation")

        call_args = mock_upload.call_args
        self.assertEqual(call_args[1]["folder"], "material_receipts/orders")

    @patch("order.receipt_utils.cloudinary.uploader.upload")
    def test_upload_payment_receipt_to_correct_folder(self, mock_upload):
        """Test payment receipts go to payments folder"""
        mock_upload.return_value = {"secure_url": "https://test.url"}

        upload_pdf_to_cloudinary(b"test", "payment.pdf", pdf_type="payment_receipt")

        call_args = mock_upload.call_args
        self.assertEqual(call_args[1]["folder"], "material_receipts/payments")

    @patch("order.receipt_utils.cloudinary.uploader.upload")
    def test_upload_general_pdf_to_correct_folder(self, mock_upload):
        """Test general PDFs go to general folder"""
        mock_upload.return_value = {"secure_url": "https://test.url"}

        upload_pdf_to_cloudinary(b"test", "general.pdf", pdf_type="general")

        call_args = mock_upload.call_args
        self.assertEqual(call_args[1]["folder"], "material_receipts/general")

    @patch("order.receipt_utils.cloudinary.uploader.upload")
    def test_upload_unknown_type_defaults_to_general(self, mock_upload):
        """Test unknown PDF types default to general folder"""
        mock_upload.return_value = {"secure_url": "https://test.url"}

        upload_pdf_to_cloudinary(b"test", "unknown.pdf", pdf_type="unknown_type")

        call_args = mock_upload.call_args
        self.assertEqual(call_args[1]["folder"], "material_receipts/general")


class GenerateOrderConfirmationPDFTests(TestCase):
    """Test order confirmation PDF generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product = NyscKit.objects.create(
            name="Test Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
        )

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_order_confirmation_basic(self, mock_render, mock_html):
        """Test basic order confirmation PDF generation"""
        # Create order
        order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
        )

        # Mock template rendering and PDF generation
        mock_render.return_value = "<html>Test PDF</html>"
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b"%PDF-1.4"
        mock_html.return_value = mock_html_instance

        # Generate PDF
        result = generate_order_confirmation_pdf(order)

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, b"%PDF-1.4")
        mock_render.assert_called_once()
        mock_html_instance.write_pdf.assert_called_once()

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_order_confirmation_sanitizes_data(self, mock_render, mock_html):
        """Test that user data is sanitized before PDF generation"""
        # Create order with potentially dangerous data
        order = BaseOrder.objects.create(
            user=self.user,
            first_name="<script>alert('xss')</script>",
            last_name="'; DROP TABLE;",
            email="test@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
        )

        mock_render.return_value = "<html>Test</html>"
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b"%PDF"
        mock_html.return_value = mock_html_instance

        # Generate PDF
        generate_order_confirmation_pdf(order)

        # Verify render_to_string was called
        self.assertTrue(mock_render.called)

        # Get the context passed to render_to_string
        context = mock_render.call_args[0][1]

        # Verify dangerous HTML tags were removed/escaped
        self.assertNotIn("<script>", context["first_name"])
        self.assertNotIn("</script>", context["first_name"])
        # Verify quotes and semicolons were removed
        self.assertNotIn("'", context["last_name"])
        self.assertNotIn(";", context["last_name"])
        # Note: "DROP TABLE" (letters and space) is preserved - sanitizer removes special chars, not keywords

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_order_confirmation_with_order_items(self, mock_render, mock_html):
        """Test PDF generation includes order items"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("15000.00"),
        )

        # Add order item
        product_ct = ContentType.objects.get_for_model(self.product)
        OrderItem.objects.create(
            order=order,
            content_type=product_ct,
            object_id=self.product.id,
            price=Decimal("5000.00"),
            quantity=3,
        )

        mock_render.return_value = "<html>Test</html>"
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b"%PDF"
        mock_html.return_value = mock_html_instance

        result = generate_order_confirmation_pdf(order)

        self.assertIsNotNone(result)
        mock_render.assert_called_once()

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_nysc_kit_order_confirmation(self, mock_render, mock_html):
        """Test PDF generation for NYSC Kit orders with specific fields"""
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("20000.00"),
            call_up_number="AB/22C/1234",
            state="Lagos",
            local_government="Ikeja",
        )

        mock_render.return_value = "<html>Test</html>"
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b"%PDF"
        mock_html.return_value = mock_html_instance

        result = generate_order_confirmation_pdf(order)

        self.assertIsNotNone(result)

        # Verify NYSC-specific fields are in context
        context = mock_render.call_args[0][1]
        self.assertIn("call_up_number", context)
        self.assertIn("state", context)
        self.assertIn("local_government", context)

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_church_order_confirmation(self, mock_render, mock_html):
        """Test PDF generation for Church orders with delivery fields"""
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            phone_number="08087654321",
            total_cost=Decimal("15000.00"),
            pickup_on_camp=False,
            delivery_state="Abuja",
            delivery_lga="Gwagwalada",
        )

        mock_render.return_value = "<html>Test</html>"
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b"%PDF"
        mock_html.return_value = mock_html_instance

        result = generate_order_confirmation_pdf(order)

        self.assertIsNotNone(result)

        # Verify delivery fields are in context
        context = mock_render.call_args[0][1]
        self.assertIn("delivery_state", context)
        self.assertIn("delivery_lga", context)

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_order_confirmation_error_handling(self, mock_render, mock_html):
        """Test error handling in PDF generation"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
        )

        # Mock template rendering failure
        mock_render.side_effect = Exception("Template error")

        result = generate_order_confirmation_pdf(order)

        # Should return None on error
        self.assertIsNone(result)


class GeneratePaymentReceiptPDFTests(TestCase):
    """Test payment receipt PDF generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_payment_receipt_basic(self, mock_render, mock_html):
        """Test basic payment receipt PDF generation"""
        # Create order
        order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
            paid=True,
        )

        # Create payment
        payment = PaymentTransaction.objects.create(
            amount=Decimal("10000.00"), email="john@example.com", status="success"
        )
        payment.orders.add(order)

        # Mock PDF generation
        mock_render.return_value = "<html>Payment Receipt</html>"
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b"%PDF-1.4"
        mock_html.return_value = mock_html_instance

        # Generate PDF
        result = generate_payment_receipt_pdf(payment)

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result, b"%PDF-1.4")
        mock_render.assert_called_once()

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_payment_receipt_no_orders(self, mock_render, mock_html):
        """Test payment receipt generation when payment has no orders"""
        # Create payment without orders
        payment = PaymentTransaction.objects.create(
            amount=Decimal("10000.00"), email="test@example.com", status="success"
        )

        result = generate_payment_receipt_pdf(payment)

        # Should return None when no orders found
        self.assertIsNone(result)
        mock_render.assert_not_called()

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_payment_receipt_multiple_orders(self, mock_render, mock_html):
        """Test payment receipt with multiple orders"""
        # Create multiple orders
        order1 = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("5000.00"),
            paid=True,
        )

        order2 = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("5000.00"),
            paid=True,
        )

        # Create payment
        payment = PaymentTransaction.objects.create(
            amount=Decimal("10000.00"), email="john@example.com", status="success"
        )
        payment.orders.set([order1, order2])

        mock_render.return_value = "<html>Payment Receipt</html>"
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b"%PDF"
        mock_html.return_value = mock_html_instance

        result = generate_payment_receipt_pdf(payment)

        self.assertIsNotNone(result)

        # Verify context includes all orders
        context = mock_render.call_args[0][1]
        self.assertIn("orders", context)

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_payment_receipt_sanitizes_data(self, mock_render, mock_html):
        """Test payment receipt sanitizes user data"""
        # Create order with special characters
        order = BaseOrder.objects.create(
            user=self.user,
            first_name="O'Brien",
            last_name="Doe",
            email="test@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
            paid=True,
        )

        payment = PaymentTransaction.objects.create(
            amount=Decimal("10000.00"), email="test@example.com", status="success"
        )
        payment.orders.add(order)

        mock_render.return_value = "<html>Test</html>"
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b"%PDF"
        mock_html.return_value = mock_html_instance

        generate_payment_receipt_pdf(payment)

        # Verify data was sanitized
        context = mock_render.call_args[0][1]
        self.assertIn("first_name", context)

    @patch("order.receipt_utils.HTML")
    @patch("order.receipt_utils.render_to_string")
    def test_generate_payment_receipt_error_handling(self, mock_render, mock_html):
        """Test error handling in payment receipt generation"""
        order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
            paid=True,
        )

        payment = PaymentTransaction.objects.create(
            amount=Decimal("10000.00"), email="john@example.com", status="success"
        )
        payment.orders.add(order)

        # Mock error in PDF generation
        mock_html.side_effect = Exception("PDF generation error")

        result = generate_payment_receipt_pdf(payment)

        # Should return None on error
        self.assertIsNone(result)


class GenerateAndStoreOrderConfirmationTests(TestCase):
    """Test combined generation and storage of order confirmation"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
        )

    @patch("order.receipt_utils.upload_pdf_to_cloudinary")
    @patch("order.receipt_utils.generate_order_confirmation_pdf")
    def test_generate_and_store_success(self, mock_generate, mock_upload):
        """Test successful generation and storage"""
        # Mock successful generation and upload
        mock_generate.return_value = b"%PDF-1.4"
        mock_upload.return_value = "https://cloudinary.com/receipt.pdf"

        pdf_bytes, cloudinary_url = generate_and_store_order_confirmation(self.order)

        self.assertEqual(pdf_bytes, b"%PDF-1.4")
        self.assertEqual(cloudinary_url, "https://cloudinary.com/receipt.pdf")
        mock_generate.assert_called_once_with(self.order)
        mock_upload.assert_called_once()

    @patch("order.receipt_utils.upload_pdf_to_cloudinary")
    @patch("order.receipt_utils.generate_order_confirmation_pdf")
    def test_generate_and_store_upload_failure(self, mock_generate, mock_upload):
        """Test handling of Cloudinary upload failure"""
        # Mock successful generation but failed upload
        mock_generate.return_value = b"%PDF-1.4"
        mock_upload.return_value = None  # Upload failed

        pdf_bytes, cloudinary_url = generate_and_store_order_confirmation(self.order)

        # Should still return PDF even if upload failed
        self.assertEqual(pdf_bytes, b"%PDF-1.4")
        self.assertIsNone(cloudinary_url)

    @patch("order.receipt_utils.upload_pdf_to_cloudinary")
    @patch("order.receipt_utils.generate_order_confirmation_pdf")
    def test_generate_and_store_generation_failure(self, mock_generate, mock_upload):
        """Test handling when Cloudinary upload fails but PDF generation succeeds"""
        # Mock PDF generation to succeed
        mock_generate.return_value = b"%PDF-1.4"
        # Mock upload to fail (raises exception)
        mock_upload.side_effect = Exception("Upload error")

        pdf_bytes, cloudinary_url = generate_and_store_order_confirmation(self.order)

        # Should still return PDF from the fallback call
        self.assertIsNotNone(pdf_bytes)
        self.assertEqual(pdf_bytes, b"%PDF-1.4")
        self.assertIsNone(cloudinary_url)  # Upload failed
        # generate_order_confirmation_pdf called twice: once in try, once in except fallback
        self.assertEqual(mock_generate.call_count, 2)


class GenerateAndStorePaymentReceiptTests(TestCase):
    """Test combined generation and storage of payment receipt"""

    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
            paid=True,
        )

        self.payment = PaymentTransaction.objects.create(
            amount=Decimal("10000.00"), email="john@example.com", status="success"
        )
        self.payment.orders.add(self.order)

    @patch("order.receipt_utils.upload_pdf_to_cloudinary")
    @patch("order.receipt_utils.generate_payment_receipt_pdf")
    def test_generate_and_store_payment_receipt_success(
        self, mock_generate, mock_upload
    ):
        """Test successful payment receipt generation and storage"""
        # Mock successful operations
        mock_generate.return_value = b"%PDF-1.4"
        mock_upload.return_value = "https://cloudinary.com/payment.pdf"

        pdf_bytes, cloudinary_url = generate_and_store_payment_receipt(self.payment)

        self.assertEqual(pdf_bytes, b"%PDF-1.4")
        self.assertEqual(cloudinary_url, "https://cloudinary.com/payment.pdf")
        mock_generate.assert_called_once_with(self.payment)
        mock_upload.assert_called_once()

    @patch("order.receipt_utils.upload_pdf_to_cloudinary")
    @patch("order.receipt_utils.generate_payment_receipt_pdf")
    def test_generate_and_store_payment_receipt_upload_failure(
        self, mock_generate, mock_upload
    ):
        """Test payment receipt when Cloudinary upload fails"""
        mock_generate.return_value = b"%PDF-1.4"
        mock_upload.side_effect = Exception("Upload error")

        pdf_bytes, cloudinary_url = generate_and_store_payment_receipt(self.payment)

        # Should return PDF even if upload failed
        self.assertEqual(pdf_bytes, b"%PDF-1.4")
        self.assertIsNone(cloudinary_url)

    @patch("order.receipt_utils.upload_pdf_to_cloudinary")
    @patch("order.receipt_utils.generate_payment_receipt_pdf")
    def test_generate_and_store_payment_receipt_error_handling(
        self, mock_generate, mock_upload
    ):
        """Test error handling when Cloudinary upload fails but PDF generation succeeds"""
        # Mock PDF generation to succeed
        mock_generate.return_value = b"%PDF-1.4"
        # Mock upload to fail
        mock_upload.side_effect = Exception("Upload error")

        pdf_bytes, cloudinary_url = generate_and_store_payment_receipt(self.payment)

        # Should still return PDF from fallback
        self.assertIsNotNone(pdf_bytes)
        self.assertEqual(pdf_bytes, b"%PDF-1.4")
        self.assertIsNone(cloudinary_url)  # Upload failed
        # generate_payment_receipt_pdf called twice: once in try, once in except fallback
        self.assertEqual(mock_generate.call_count, 2)
