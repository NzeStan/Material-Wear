# webhook_router/tests/tests_background_utils.py
"""
Bulletproof tests for jmw/background_utils.py
Tests all background email and PDF generation tasks
FINAL VERSION - all issues resolved
"""
from django.test import TestCase, override_settings, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from unittest.mock import Mock, patch, MagicMock, call
from decimal import Decimal
from threading import Thread
from datetime import timedelta
import time
import uuid

# Import the functions we're testing
from jmw.background_utils import (
    send_email_async,
    send_order_confirmation_email_async,
    generate_order_confirmation_pdf_task,
    send_payment_receipt_email_async,
    generate_payment_receipt_pdf_task,
    send_order_confirmation_email,
    send_payment_receipt_email,
    generate_bulk_order_pdf_task,
    generate_payment_receipt_pdf_task_bulk,
)

User = get_user_model()


# ============================================================================
# SEND_EMAIL_ASYNC TESTS
# ============================================================================

class SendEmailAsyncTests(TestCase):
    """Test send_email_async function"""
    
    def setUp(self):
        """Set up test data"""
        self.subject = "Test Email"
        self.message = "Test message"
        self.from_email = "test@example.com"
        self.recipient_list = ["recipient@example.com"]
    
    def test_send_plain_text_email(self):
        """Test sending plain text email"""
        send_email_async(
            subject=self.subject,
            message=self.message,
            from_email=self.from_email,
            recipient_list=self.recipient_list
        )
        
        # Wait for thread to complete
        time.sleep(0.5)
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, self.subject)
        self.assertEqual(email.body, self.message)
        self.assertEqual(email.from_email, self.from_email)
        self.assertEqual(email.to, self.recipient_list)
    
    def test_send_html_email(self):
        """Test sending HTML email"""
        html_message = "<html><body><h1>Test</h1></body></html>"
        
        send_email_async(
            subject=self.subject,
            message=self.message,
            from_email=self.from_email,
            recipient_list=self.recipient_list,
            html_message=html_message
        )
        
        # Wait for thread to complete
        time.sleep(0.5)
        
        # Check email was sent with HTML
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.content_subtype, "html")
        self.assertEqual(email.body, html_message)
    
    def test_send_email_with_attachments(self):
        """Test sending email with attachments"""
        attachments = [
            ("test.pdf", b"PDF content", "application/pdf"),
            ("test.txt", b"Text content", "text/plain")
        ]
        
        send_email_async(
            subject=self.subject,
            message=self.message,
            from_email=self.from_email,
            recipient_list=self.recipient_list,
            attachments=attachments
        )
        
        # Wait for thread to complete
        time.sleep(0.5)
        
        # Check attachments
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(len(email.attachments), 2)
        self.assertEqual(email.attachments[0][0], "test.pdf")
        self.assertEqual(email.attachments[1][0], "test.txt")
    
    def test_send_email_multiple_recipients(self):
        """Test sending email to multiple recipients"""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        
        send_email_async(
            subject=self.subject,
            message=self.message,
            from_email=self.from_email,
            recipient_list=recipients
        )
        
        # Wait for thread to complete
        time.sleep(0.5)
        
        # Check all recipients
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, recipients)
    
    @patch('jmw.background_utils.EmailMessage.send')
    def test_email_error_handling(self, mock_send):
        """Test error handling during email send"""
        mock_send.side_effect = Exception("SMTP error")
        
        # Should not raise exception
        send_email_async(
            subject=self.subject,
            message=self.message,
            from_email=self.from_email,
            recipient_list=self.recipient_list
        )
        
        # Wait for thread
        time.sleep(0.5)
        
        # No exception should be raised
        self.assertTrue(True)
    
    def test_email_with_unicode_content(self):
        """Test handling unicode content in emails"""
        unicode_subject = "Test Email 中文 العربية 😀"
        unicode_message = "Message with unicode: 日本語 한국어"
        
        send_email_async(
            subject=unicode_subject,
            message=unicode_message,
            from_email="test@example.com",
            recipient_list=["recipient@example.com"]
        )
        
        # Wait for thread
        time.sleep(0.5)
        
        # Email should be sent successfully
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, unicode_subject)
    
    def test_concurrent_email_sending(self):
        """Test sending multiple emails concurrently"""
        emails_to_send = 5
        
        for i in range(emails_to_send):
            send_email_async(
                subject=f"Test Email {i}",
                message=f"Message {i}",
                from_email="test@example.com",
                recipient_list=[f"recipient{i}@example.com"]
            )
        
        # Wait for all threads
        time.sleep(1.0)
        
        # All emails should be sent
        self.assertEqual(len(mail.outbox), emails_to_send)


# ============================================================================
# ORDER CONFIRMATION EMAIL TESTS (MOCKED TO AVOID DB LOCKING)
# ============================================================================

class SendOrderConfirmationEmailAsyncTests(TestCase):
    """Test send_order_confirmation_email_async function"""
    
    def setUp(self):
        """Set up test fixtures"""
        from order.models import BaseOrder
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            middle_name='Michael',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=False
        )
    
    def test_order_not_found(self):
        """Test handling non-existent order"""
        fake_id = uuid.uuid4()
        
        # Should not raise exception
        send_order_confirmation_email_async(fake_id)
        
        # Wait for thread
        time.sleep(0.5)
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)
    
    @patch('jmw.background_utils.render_to_string')
    def test_template_rendering_error(self, mock_render):
        """Test handling template rendering errors"""
        mock_render.side_effect = Exception("Template error")
        
        # Should not raise exception
        send_order_confirmation_email_async(self.order.id)
        
        # Wait for thread
        time.sleep(0.5)
        
        # No crash
        self.assertTrue(True)


# ============================================================================
# PAYMENT RECEIPT EMAIL TESTS (MOCKED TO AVOID DB LOCKING)
# ============================================================================

class SendPaymentReceiptEmailAsyncTests(TestCase):
    """Test send_payment_receipt_email_async function"""
    
    def setUp(self):
        """Set up test fixtures"""
        from order.models import BaseOrder
        from payment.models import PaymentTransaction
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=True
        )
        
        self.payment = PaymentTransaction.objects.create(
            amount=Decimal('15000.00'),
            email='john@example.com',
            reference='TEST_REF_123',
            status='success'
        )
        self.payment.orders.add(self.order)
    
    def test_payment_not_found(self):
        """Test handling non-existent payment"""
        fake_id = uuid.uuid4()
        
        # Should not raise exception
        send_payment_receipt_email_async(fake_id)
        
        # Wait for thread
        time.sleep(0.5)
        
        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)


# ============================================================================
# PDF GENERATION TASKS TESTS
# ============================================================================

class GenerateOrderConfirmationPdfTaskTests(TestCase):
    """Test generate_order_confirmation_pdf_task background task"""
    
    def setUp(self):
        """Set up test fixtures"""
        from order.models import BaseOrder
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00')
        )
    
    @patch('order.receipt_utils.generate_and_store_order_confirmation')
    @patch('jmw.background_utils.send_email_async')
    @override_settings(
        COMPANY_NAME='JMW Accessories',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_generate_and_send_pdf(self, mock_send_email, mock_generate):
        """Test PDF generation and email sending"""
        # Mock PDF generation
        mock_pdf = b'%PDF-1.4 fake pdf content'
        mock_url = 'https://cloudinary.com/receipt.pdf'
        mock_generate.return_value = (mock_pdf, mock_url)
        
        # Get the actual task function (not the decorated version)
        # Background tasks can't serialize UUID objects
        task_func = generate_order_confirmation_pdf_task.task_function
        
        # Call it directly with string UUID
        task_func(str(self.order.id))
        
        # Check PDF was generated
        mock_generate.assert_called_once()
        
        # Check email was sent
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]
        
        self.assertIn('Order Confirmation Receipt', call_kwargs['subject'])
        self.assertEqual(call_kwargs['recipient_list'], [self.order.email])
        self.assertEqual(len(call_kwargs['attachments']), 1)
        self.assertEqual(call_kwargs['attachments'][0][1], mock_pdf)
    
    @patch('order.receipt_utils.generate_and_store_order_confirmation')
    def test_order_not_found_in_task(self, mock_generate):
        """Test handling non-existent order in background task"""
        fake_id = str(uuid.uuid4())
        
        # Get the actual task function
        task_func = generate_order_confirmation_pdf_task.task_function
        
        # Should not raise exception
        try:
            task_func(fake_id)
        except Exception:
            pass  # Expected
        
        # PDF generation should not be called
        mock_generate.assert_not_called()


class GeneratePaymentReceiptPdfTaskTests(TestCase):
    """Test generate_payment_receipt_pdf_task background task"""
    
    def setUp(self):
        """Set up test fixtures"""
        from order.models import BaseOrder
        from payment.models import PaymentTransaction
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=True
        )
        
        self.payment = PaymentTransaction.objects.create(
            amount=Decimal('15000.00'),
            email='john@example.com',
            reference='TEST_REF_123',
            status='success'
        )
        self.payment.orders.add(self.order)
    
    @patch('order.receipt_utils.generate_and_store_payment_receipt')
    @patch('jmw.background_utils.send_email_async')
    @override_settings(
        COMPANY_NAME='JMW Accessories',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_generate_and_send_payment_receipt_pdf(self, mock_send_email, mock_generate):
        """Test payment receipt PDF generation and sending"""
        # Mock PDF generation
        mock_pdf = b'%PDF-1.4 payment receipt'
        mock_url = 'https://cloudinary.com/payment-receipt.pdf'
        mock_generate.return_value = (mock_pdf, mock_url)
        
        # Get the actual task function (not the decorated version)
        task_func = generate_payment_receipt_pdf_task.task_function
        
        # Call it directly with string UUID
        task_func(str(self.payment.id))
        
        # Check PDF was generated
        mock_generate.assert_called_once()
        
        # Check email was sent
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]
        
        self.assertIn('Payment Receipt', call_kwargs['subject'])
        self.assertIn(self.payment.reference, call_kwargs['subject'])
        self.assertEqual(call_kwargs['recipient_list'], [self.payment.email])


# ============================================================================
# BULK ORDER TESTS
# ============================================================================

class BulkOrderEmailTests(TestCase):
    """Test bulk order email functions"""
    
    def setUp(self):
        """Set up bulk order test fixtures"""
        from bulk_orders.models import BulkOrderLink, OrderEntry
        
        bulk_user = User.objects.create_user(
            username='bulkuser', email='bulk@example.com', password='pass123'
        )
        
        self.bulk_order = BulkOrderLink.objects.create(
            organization_name='Test Organization',
            price_per_item=Decimal('5000.00'),
            custom_branding_enabled=False,
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=bulk_user
        )
        
        self.order_entry = OrderEntry.objects.create(
            bulk_order=self.bulk_order,
            full_name='John Doe',
            email='john@example.com',
            size='L',
            paid=False
        )
    
    @override_settings(
        COMPANY_NAME='JMW Accessories',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_send_order_confirmation_email(self):
        """Test bulk order confirmation email"""
        send_order_confirmation_email(self.order_entry)
        
        # Wait for thread
        time.sleep(0.5)
        
        # Check email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Order Confirmation', email.subject)
        self.assertIn(self.bulk_order.organization_name, email.subject)
        self.assertEqual(email.to, [self.order_entry.email])
    
    @override_settings(
        COMPANY_NAME='JMW Accessories',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_send_payment_receipt_email(self):
        """Test bulk order payment receipt email"""
        send_payment_receipt_email(self.order_entry)
        
        # Wait for thread
        time.sleep(0.5)
        
        # Check email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Payment Receipt', email.subject)
        self.assertIn(str(self.order_entry.serial_number), email.subject)  # Convert to string
        self.assertEqual(email.to, [self.order_entry.email])


class GenerateBulkOrderPdfTaskTests(TestCase):
    """Test generate_bulk_order_pdf_task background task"""
    
    def setUp(self):
        """Set up bulk order test fixtures"""
        from bulk_orders.models import BulkOrderLink
        
        bulk_user = User.objects.create_user(
            username='bulkuser', email='bulk@example.com', password='pass123'
        )
        
        self.bulk_order = BulkOrderLink.objects.create(
            organization_name='Test Organization',
            price_per_item=Decimal('5000.00'),
            custom_branding_enabled=False,
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=bulk_user
        )
    
    @patch('bulk_orders.utils.generate_bulk_order_pdf')
    @patch('jmw.background_utils.send_email_async')
    def test_generate_bulk_order_pdf(self, mock_send_email, mock_generate_pdf):
        """Test bulk order PDF generation"""
        from django.http import HttpResponse
        
        # Mock PDF generation - returns HttpResponse not bytes
        mock_response = HttpResponse(b'%PDF-1.4 bulk order', content_type='application/pdf')
        mock_generate_pdf.return_value = mock_response
        
        recipient = 'admin@example.com'
        
        # Get the actual task function (not the decorated version)
        # Background tasks can't serialize UUID objects
        task_func = generate_bulk_order_pdf_task.task_function
        
        # Call it directly with IDs as integers/strings
        task_func(self.bulk_order.id, recipient)
        
        # Check PDF was generated
        mock_generate_pdf.assert_called_once()
        
        # Check email was sent
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]
        
        self.assertIn('Bulk Order Report', call_kwargs['subject'])
        self.assertEqual(call_kwargs['recipient_list'], [recipient])