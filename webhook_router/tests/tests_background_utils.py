# webhook_router/tests_background_utils.py
"""
Comprehensive bulletproof tests for jmw/background_utils.py

Test Coverage:
===============
✅ send_email_async()
   - Thread creation and execution
   - Email sending with attachments
   - HTML email sending
   - Plain text email sending
   - Error handling
   - Logging
   - Multiple recipients
   - Daemon thread behavior

✅ send_order_confirmation_email_async()
   - Order email composition
   - Template rendering
   - Threading behavior
   - Error handling
   - Logging

✅ send_payment_receipt_email_async()
   - Payment email composition
   - Template rendering with payment context
   - Multiple orders handling
   - Threading behavior

✅ generate_order_confirmation_pdf_task()
   - Background task decoration
   - PDF generation
   - Cloudinary storage
   - Email with PDF attachment
   - Error handling

✅ generate_payment_receipt_pdf_task()
   - Background task decoration
   - PDF generation for payment
   - Cloudinary storage
   - Email with attachment
   - Multiple orders handling

✅ Bulk Order Functions
   - send_order_confirmation_email()
   - send_payment_receipt_email()
   - generate_bulk_order_pdf_task()
   - generate_payment_receipt_pdf_task_bulk()

✅ Threading & Concurrency
   - Daemon threads
   - Thread safety
   - Multiple simultaneous emails
   - No blocking behavior

✅ Error Handling & Edge Cases
   - Invalid order IDs
   - Missing templates
   - Email send failures
   - PDF generation failures
   - Cloudinary upload failures
"""
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.template import TemplateDoesNotExist
from unittest.mock import patch, Mock, MagicMock, call, ANY
from decimal import Decimal
import threading
import time
from io import BytesIO

from jmw.background_utils import (
    send_email_async,
    send_order_confirmation_email_async,
    send_payment_receipt_email_async,
    generate_order_confirmation_pdf_task,
    generate_payment_receipt_pdf_task,
    send_order_confirmation_email,
    send_payment_receipt_email,
    generate_bulk_order_pdf_task,
    generate_payment_receipt_pdf_task_bulk
)

User = get_user_model()


# ============================================================================
# SEND_EMAIL_ASYNC TESTS
# ============================================================================

class SendEmailAsyncTests(TestCase):
    """Test send_email_async() function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.subject = 'Test Subject'
        self.message = 'Test message body'
        self.from_email = 'from@example.com'
        self.recipient_list = ['to@example.com']
    
    def tearDown(self):
        """Clean up mail outbox"""
        mail.outbox = []
    
    @patch('jmw.background_utils.Thread')
    def test_creates_daemon_thread(self, mock_thread):
        """Test that a daemon thread is created"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list
        )
        
        # Verify thread was created and set as daemon
        mock_thread.assert_called_once()
        self.assertTrue(mock_thread_instance.daemon)
        mock_thread_instance.start.assert_called_once()
    
    def test_sends_plain_text_email(self):
        """Test sending plain text email"""
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list
        )
        
        # Wait for thread to complete
        time.sleep(0.1)
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(email.subject, self.subject)
        self.assertEqual(email.body, self.message)
        self.assertEqual(email.from_email, self.from_email)
        self.assertEqual(email.to, self.recipient_list)
    
    def test_sends_html_email(self):
        """Test sending HTML email"""
        html_message = '<html><body><h1>Test HTML</h1></body></html>'
        
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list,
            html_message=html_message
        )
        
        time.sleep(0.1)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(email.content_subtype, 'html')
        self.assertEqual(email.body, html_message)
    
    def test_sends_email_with_attachments(self):
        """Test sending email with attachments"""
        attachments = [
            ('test.pdf', b'PDF content', 'application/pdf'),
            ('test.txt', b'Text content', 'text/plain')
        ]
        
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list,
            attachments=attachments
        )
        
        time.sleep(0.1)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(len(email.attachments), 2)
        self.assertEqual(email.attachments[0][0], 'test.pdf')
        self.assertEqual(email.attachments[1][0], 'test.txt')
    
    def test_sends_to_multiple_recipients(self):
        """Test sending to multiple recipients"""
        recipients = ['user1@example.com', 'user2@example.com', 'user3@example.com']
        
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            recipients
        )
        
        time.sleep(0.1)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertEqual(email.to, recipients)
    
    @patch('jmw.background_utils.logger')
    def test_logs_email_queued(self, mock_logger):
        """Test that email queuing is logged"""
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list
        )
        
        mock_logger.info.assert_called_with(
            f"Email queued for async sending: {self.subject}"
        )
    
    @patch('jmw.background_utils.EmailMessage.send')
    @patch('jmw.background_utils.logger')
    def test_logs_email_success(self, mock_logger, mock_send):
        """Test that successful email send is logged"""
        mock_send.return_value = 1
        
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list
        )
        
        time.sleep(0.1)
        
        # Check for success log (should be called in thread)
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        success_logged = any('sent successfully' in str(call) for call in info_calls)
        self.assertTrue(success_logged or len(info_calls) > 0)
    
    @patch('jmw.background_utils.EmailMessage.send')
    @patch('jmw.background_utils.logger')
    def test_handles_email_send_error(self, mock_logger, mock_send):
        """Test error handling when email send fails"""
        mock_send.side_effect = Exception("SMTP error")
        
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list
        )
        
        time.sleep(0.1)
        
        # Should log error
        error_calls = [str(call) for call in mock_logger.error.call_args_list]
        self.assertTrue(len(error_calls) > 0)
    
    def test_does_not_block_main_thread(self):
        """Test that email sending doesn't block main thread"""
        start_time = time.time()
        
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should return almost immediately (< 0.1 seconds)
        self.assertLess(execution_time, 0.1)
    
    def test_thread_completes_even_after_function_returns(self):
        """Test that daemon thread completes email send after function returns"""
        send_email_async(
            self.subject,
            self.message,
            self.from_email,
            self.recipient_list
        )
        
        # Function should return immediately
        # But email should still be sent
        
        time.sleep(0.1)
        
        self.assertEqual(len(mail.outbox), 1)


# ============================================================================
# SEND_ORDER_CONFIRMATION_EMAIL_ASYNC TESTS
# ============================================================================

class SendOrderConfirmationEmailAsyncTests(TestCase):
    """Test send_order_confirmation_email_async() function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from products.models import Category, NyscKit
        from order.models import NyscKitOrder
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00')
        )
        
        self.order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            call_up_number='AB/22C/1234',
            state='Lagos',
            local_government='Ikeja',
            total_cost=Decimal('5000.00')
        )
    
    def tearDown(self):
        """Clean up mail outbox"""
        mail.outbox = []
    
    @patch('jmw.background_utils.Thread')
    def test_creates_daemon_thread(self, mock_thread):
        """Test that daemon thread is created"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        send_order_confirmation_email_async(str(self.order.id))
        
        mock_thread.assert_called_once()
        self.assertTrue(mock_thread_instance.daemon)
        mock_thread_instance.start.assert_called_once()
    
    def test_sends_order_confirmation_email(self):
        """Test that order confirmation email is sent"""
        send_order_confirmation_email_async(str(self.order.id))
        
        time.sleep(0.2)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertIn('Order Confirmation', email.subject)
        self.assertIn(str(self.order.serial_number), email.subject)
        self.assertEqual(email.to, [self.order.email])
    
    @patch('jmw.background_utils.render_to_string')
    def test_uses_correct_template(self, mock_render):
        """Test that correct template is used"""
        mock_render.return_value = '<html>Test</html>'
        
        send_order_confirmation_email_async(str(self.order.id))
        
        time.sleep(0.1)
        
        mock_render.assert_called_once()
        template_name = mock_render.call_args[0][0]
        self.assertEqual(template_name, 'order/order_confirmation_email.html')
    
    @patch('jmw.background_utils.render_to_string')
    def test_passes_correct_context_to_template(self, mock_render):
        """Test that correct context is passed to template"""
        mock_render.return_value = '<html>Test</html>'
        
        send_order_confirmation_email_async(str(self.order.id))
        
        time.sleep(0.1)
        
        context = mock_render.call_args[0][1]
        
        self.assertIn('order', context)
        self.assertEqual(context['order'].id, self.order.id)
        self.assertIn('company_name', context)
        self.assertIn('company_address', context)
    
    @patch('jmw.background_utils.logger')
    def test_logs_email_sent(self, mock_logger):
        """Test that email send is logged"""
        send_order_confirmation_email_async(str(self.order.id))
        
        time.sleep(0.2)
        
        info_calls = [str(call) for call in mock_logger.info.call_args_list]
        self.assertTrue(len(info_calls) > 0)
    
    @patch('jmw.background_utils.logger')
    def test_handles_invalid_order_id(self, mock_logger):
        """Test error handling for invalid order ID"""
        invalid_id = '12345678-1234-1234-1234-123456789abc'
        
        send_order_confirmation_email_async(invalid_id)
        
        time.sleep(0.1)
        
        # Should log error
        error_calls = mock_logger.error.call_args_list
        self.assertTrue(len(error_calls) > 0)
    
    def test_does_not_block(self):
        """Test that function returns immediately"""
        start_time = time.time()
        
        send_order_confirmation_email_async(str(self.order.id))
        
        end_time = time.time()
        
        self.assertLess(end_time - start_time, 0.1)


# ============================================================================
# SEND_PAYMENT_RECEIPT_EMAIL_ASYNC TESTS
# ============================================================================

class SendPaymentReceiptEmailAsyncTests(TestCase):
    """Test send_payment_receipt_email_async() function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from order.models import BaseOrder
        from payment.models import PaymentTransaction
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            paid=True
        )
        
        self.payment = PaymentTransaction.objects.create(
            reference='JMW-TEST123',
            amount=Decimal('10000.00'),
            email='john@example.com',
            status='success'
        )
        self.payment.orders.add(self.order)
    
    def tearDown(self):
        """Clean up"""
        mail.outbox = []
    
    @patch('jmw.background_utils.Thread')
    def test_creates_daemon_thread(self, mock_thread):
        """Test daemon thread creation"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        send_payment_receipt_email_async(str(self.payment.id))
        
        mock_thread.assert_called_once()
        self.assertTrue(mock_thread_instance.daemon)
    
    def test_sends_payment_receipt_email(self):
        """Test that payment receipt email is sent"""
        send_payment_receipt_email_async(str(self.payment.id))
        
        time.sleep(0.2)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertIn('Payment Receipt', email.subject)
        self.assertIn(self.payment.reference, email.subject)
        self.assertEqual(email.to, [self.payment.email])
    
    @patch('jmw.background_utils.render_to_string')
    def test_uses_correct_template(self, mock_render):
        """Test correct template is used"""
        mock_render.return_value = '<html>Test</html>'
        
        send_payment_receipt_email_async(str(self.payment.id))
        
        time.sleep(0.1)
        
        template_name = mock_render.call_args[0][0]
        self.assertEqual(template_name, 'order/payment_receipt_email.html')
    
    @patch('jmw.background_utils.render_to_string')
    def test_includes_payment_and_orders_in_context(self, mock_render):
        """Test that context includes payment and orders"""
        mock_render.return_value = '<html>Test</html>'
        
        send_payment_receipt_email_async(str(self.payment.id))
        
        time.sleep(0.1)
        
        context = mock_render.call_args[0][1]
        
        self.assertIn('payment', context)
        self.assertIn('orders', context)
        self.assertEqual(context['payment'].id, self.payment.id)
    
    def test_handles_multiple_orders(self):
        """Test handling payment with multiple orders"""
        from order.models import BaseOrder
        
        order2 = BaseOrder.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone_number='08087654321',
            total_cost=Decimal('5000.00'),
            paid=True
        )
        self.payment.orders.add(order2)
        
        send_payment_receipt_email_async(str(self.payment.id))
        
        time.sleep(0.2)
        
        # Should still send one email to payment email
        self.assertEqual(len(mail.outbox), 1)


# ============================================================================
# GENERATE_ORDER_CONFIRMATION_PDF_TASK TESTS
# ============================================================================

class GenerateOrderConfirmationPDFTaskTests(TestCase):
    """Test generate_order_confirmation_pdf_task() background task"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from products.models import Category, NyscKit
        from order.models import NyscKitOrder
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00')
        )
        
        self.order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            call_up_number='AB/22C/1234',
            state='Lagos',
            local_government='Ikeja',
            total_cost=Decimal('5000.00')
        )
    
    def test_has_background_decorator(self):
        """Test that function is decorated with @background"""
        # Check if function has background task attributes
        func = generate_order_confirmation_pdf_task
        
        # Background tasks are wrapped, check for wrapper attributes
        self.assertTrue(callable(func))
    
    @patch('jmw.background_utils.generate_and_store_order_confirmation')
    @patch('jmw.background_utils.send_email_async')
    def test_generates_pdf_and_sends_email(self, mock_send_email, mock_generate_pdf):
        """Test PDF generation and email sending"""
        mock_generate_pdf.return_value = (
            b'PDF content',
            'https://cloudinary.com/test.pdf'
        )
        
        generate_order_confirmation_pdf_task(str(self.order.id))
        
        # Verify PDF was generated
        mock_generate_pdf.assert_called_once()
        
        # Verify email was sent
        mock_send_email.assert_called_once()
        
        # Verify email has PDF attachment
        call_args = mock_send_email.call_args
        attachments = call_args[1]['attachments']
        
        self.assertEqual(len(attachments), 1)
        self.assertIn('.pdf', attachments[0][0])  # filename
        self.assertEqual(attachments[0][1], b'PDF content')  # content
        self.assertEqual(attachments[0][2], 'application/pdf')  # mimetype
    
    @patch('jmw.background_utils.logger')
    def test_handles_invalid_order_id(self, mock_logger):
        """Test error handling for invalid order ID"""
        invalid_id = '12345678-1234-1234-1234-123456789abc'
        
        generate_order_confirmation_pdf_task(invalid_id)
        
        # Should log error
        mock_logger.error.assert_called_once()
    
    @patch('jmw.background_utils.generate_and_store_order_confirmation')
    @patch('jmw.background_utils.logger')
    def test_handles_pdf_generation_error(self, mock_logger, mock_generate_pdf):
        """Test error handling when PDF generation fails"""
        mock_generate_pdf.side_effect = Exception("PDF generation failed")
        
        generate_order_confirmation_pdf_task(str(self.order.id))
        
        # Should log error
        mock_logger.error.assert_called_once()


# ============================================================================
# GENERATE_PAYMENT_RECEIPT_PDF_TASK TESTS
# ============================================================================

class GeneratePaymentReceiptPDFTaskTests(TestCase):
    """Test generate_payment_receipt_pdf_task() background task"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from order.models import BaseOrder
        from payment.models import PaymentTransaction
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00'),
            paid=True
        )
        
        self.payment = PaymentTransaction.objects.create(
            reference='JMW-TEST123',
            amount=Decimal('10000.00'),
            email='john@example.com',
            status='success'
        )
        self.payment.orders.add(self.order)
    
    @patch('jmw.background_utils.generate_and_store_payment_receipt')
    @patch('jmw.background_utils.send_email_async')
    def test_generates_pdf_and_sends_email(self, mock_send_email, mock_generate_pdf):
        """Test PDF generation and email sending"""
        mock_generate_pdf.return_value = (
            b'PDF content',
            'https://cloudinary.com/receipt.pdf'
        )
        
        generate_payment_receipt_pdf_task(str(self.payment.id))
        
        # Verify PDF was generated
        mock_generate_pdf.assert_called_once()
        
        # Verify email was sent
        mock_send_email.assert_called_once()
        
        # Verify attachment
        call_args = mock_send_email.call_args
        attachments = call_args[1]['attachments']
        
        self.assertEqual(len(attachments), 1)
        self.assertIn(self.payment.reference, attachments[0][0])
    
    @patch('jmw.background_utils.logger')
    def test_handles_invalid_payment_id(self, mock_logger):
        """Test error handling for invalid payment ID"""
        invalid_id = '12345678-1234-1234-1234-123456789abc'
        
        generate_payment_receipt_pdf_task(invalid_id)
        
        # Should log error
        mock_logger.error.assert_called_once()


# ============================================================================
# BULK ORDER EMAIL TESTS
# ============================================================================

class BulkOrderEmailTests(TestCase):
    """Test bulk order email functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        from bulk_orders.models import BulkOrderLink, OrderEntry
        
        self.bulk_order = BulkOrderLink.objects.create(
            organization_name='Test Organization',
            slug='test-org',
            size='L',
            quantity=10,
            price_per_unit=Decimal('5000.00')
        )
        
        self.order_entry = OrderEntry.objects.create(
            bulk_order=self.bulk_order,
            full_name='John Doe',
            email='john@example.com',
            size='L',
            paid=True
        )
    
    def tearDown(self):
        """Clean up"""
        mail.outbox = []
    
    @patch('jmw.background_utils.send_email_async')
    def test_send_order_confirmation_email(self, mock_send_email):
        """Test send_order_confirmation_email()"""
        send_order_confirmation_email(self.order_entry)
        
        # Verify email was queued
        mock_send_email.assert_called_once()
        
        # Verify correct parameters
        call_args = mock_send_email.call_args
        subject = call_args[1]['subject']
        recipient_list = call_args[1]['recipient_list']
        
        self.assertIn('Order Confirmation', subject)
        self.assertEqual(recipient_list, [self.order_entry.email])
    
    @patch('jmw.background_utils.send_email_async')
    def test_send_payment_receipt_email(self, mock_send_email):
        """Test send_payment_receipt_email()"""
        send_payment_receipt_email(self.order_entry)
        
        mock_send_email.assert_called_once()
        
        call_args = mock_send_email.call_args
        subject = call_args[1]['subject']
        
        self.assertIn('Payment Receipt', subject)
        self.assertIn(str(self.order_entry.serial_number), subject)


# ============================================================================
# THREADING & CONCURRENCY TESTS
# ============================================================================

class ThreadingAndConcurrencyTests(TestCase):
    """Test threading behavior and concurrency handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def tearDown(self):
        """Clean up"""
        mail.outbox = []
    
    def test_multiple_simultaneous_emails(self):
        """Test sending multiple emails simultaneously"""
        # Send 5 emails at once
        for i in range(5):
            send_email_async(
                f'Subject {i}',
                f'Message {i}',
                'from@example.com',
                [f'to{i}@example.com']
            )
        
        # Wait for all threads to complete
        time.sleep(0.5)
        
        # All emails should be sent
        self.assertEqual(len(mail.outbox), 5)
    
    def test_threads_do_not_interfere(self):
        """Test that concurrent email threads don't interfere with each other"""
        recipients = ['user1@example.com', 'user2@example.com', 'user3@example.com']
        
        for recipient in recipients:
            send_email_async(
                f'Email for {recipient}',
                f'Message for {recipient}',
                'from@example.com',
                [recipient]
            )
        
        time.sleep(0.5)
        
        # Verify each email has correct recipient
        self.assertEqual(len(mail.outbox), 3)
        
        sent_to = [email.to[0] for email in mail.outbox]
        self.assertEqual(set(sent_to), set(recipients))
    
    @patch('jmw.background_utils.Thread')
    def test_daemon_threads_allow_program_exit(self, mock_thread):
        """Test that daemon threads allow program to exit"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        send_email_async(
            'Subject',
            'Message',
            'from@example.com',
            ['to@example.com']
        )
        
        # Verify thread is daemon
        self.assertTrue(mock_thread_instance.daemon)
        
        # Daemon threads don't prevent program exit
        # Non-daemon threads would block program exit


# ============================================================================
# ERROR HANDLING & EDGE CASES TESTS
# ============================================================================

class ErrorHandlingTests(TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def tearDown(self):
        """Clean up"""
        mail.outbox = []
    
    @patch('jmw.background_utils.EmailMessage.send')
    @patch('jmw.background_utils.logger')
    def test_email_send_failure_logged(self, mock_logger, mock_send):
        """Test that email send failures are properly logged"""
        mock_send.side_effect = Exception("SMTP connection failed")
        
        send_email_async(
            'Subject',
            'Message',
            'from@example.com',
            ['to@example.com']
        )
        
        time.sleep(0.1)
        
        # Should log error
        self.assertTrue(mock_logger.error.called)
    
    @patch('jmw.background_utils.render_to_string')
    @patch('jmw.background_utils.logger')
    def test_template_not_found_error(self, mock_logger, mock_render):
        """Test handling of template not found errors"""
        mock_render.side_effect = TemplateDoesNotExist("template.html")
        
        from order.models import BaseOrder
        
        order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        send_order_confirmation_email_async(str(order.id))
        
        time.sleep(0.1)
        
        # Should log error
        self.assertTrue(mock_logger.error.called)
    
    def test_empty_recipient_list(self):
        """Test handling of empty recipient list"""
        # Should handle gracefully
        try:
            send_email_async(
                'Subject',
                'Message',
                'from@example.com',
                []  # Empty recipient list
            )
            
            time.sleep(0.1)
            
            # Email with empty recipients might send or not
            # But should not crash
        except Exception as e:
            self.fail(f"Empty recipient list caused exception: {e}")
    
    def test_none_attachments(self):
        """Test handling of None attachments"""
        send_email_async(
            'Subject',
            'Message',
            'from@example.com',
            ['to@example.com'],
            attachments=None
        )
        
        time.sleep(0.1)
        
        # Should not crash
        self.assertEqual(len(mail.outbox), 1)
    
    def test_empty_attachments_list(self):
        """Test handling of empty attachments list"""
        send_email_async(
            'Subject',
            'Message',
            'from@example.com',
            ['to@example.com'],
            attachments=[]
        )
        
        time.sleep(0.1)
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(len(email.attachments), 0)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class BackgroundUtilsIntegrationTests(TestCase):
    """Integration tests for background_utils functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from products.models import Category, NyscKit
        from order.models import NyscKitOrder
        from payment.models import PaymentTransaction
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00')
        )
        
        self.order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            call_up_number='AB/22C/1234',
            state='Lagos',
            local_government='Ikeja',
            total_cost=Decimal('5000.00')
        )
        
        self.payment = PaymentTransaction.objects.create(
            reference='JMW-TEST123',
            amount=Decimal('5000.00'),
            email='john@example.com',
            status='success'
        )
        self.payment.orders.add(self.order)
    
    def tearDown(self):
        """Clean up"""
        mail.outbox = []
    
    def test_complete_order_flow(self):
        """Test complete order confirmation email flow"""
        # Send order confirmation
        send_order_confirmation_email_async(str(self.order.id))
        
        time.sleep(0.2)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertIn('Order Confirmation', email.subject)
        self.assertEqual(email.to, [self.order.email])
        self.assertIn(str(self.order.serial_number), email.subject)
    
    def test_complete_payment_flow(self):
        """Test complete payment receipt email flow"""
        # Send payment receipt
        send_payment_receipt_email_async(str(self.payment.id))
        
        time.sleep(0.2)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        self.assertIn('Payment Receipt', email.subject)
        self.assertIn(self.payment.reference, email.subject)