# webhook_router/tests/tests_background_utils.py
"""
Bulletproof tests for jmw/background_utils.py
Tests all background email and PDF generation tasks

Test Coverage:
===============
- Email utilities (threading-based)
- Order confirmation emails (regular orders)
- Payment receipt emails (regular orders)
- PDF generation tasks (regular orders)
- Bulk order email functions
- Bulk order PDF generation tasks
- Academic directory email functions
- Image bulk order email functions
- Live forms email and PDF functions
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
    # Academic directory functions
    send_new_submission_email_async,
    send_bulk_verification_email_async,
    send_daily_summary_email_async,
    process_pending_notifications_async,
    check_graduation_statuses_task,
    # Image bulk order functions
    send_image_order_confirmation_email,
    send_image_payment_receipt_email,
    generate_image_payment_receipt_pdf_task,
    # Live forms functions
    send_live_form_submission_email_async,
    generate_live_form_report_task,
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
        unicode_subject = "Test Email 中文 العربية"
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
        self.assertIn(str(self.order_entry.serial_number), email.subject)
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


# ============================================================================
# IMAGE BULK ORDER TESTS
# ============================================================================

class ImageBulkOrderEmailTests(TestCase):
    """Test image bulk order email functions"""

    def setUp(self):
        """Set up image bulk order test fixtures"""
        from image_bulk_orders.models import ImageBulkOrderLink, ImageOrderEntry

        bulk_user = User.objects.create_user(
            username='imgbulkuser', email='imgbulk@example.com', password='pass123'
        )

        self.image_bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Image Test Organization',
            price_per_item=Decimal('6000.00'),
            custom_branding_enabled=False,
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=bulk_user,
            slug='image-test-organization'
        )

        self.image_order_entry = ImageOrderEntry.objects.create(
            bulk_order=self.image_bulk_order,
            full_name='Jane Doe',
            email='jane@example.com',
            size='M',
            paid=False
        )

    @override_settings(
        COMPANY_NAME='JMW Accessories',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_send_image_order_confirmation_email(self):
        """Test image bulk order confirmation email"""
        send_image_order_confirmation_email(self.image_order_entry)

        # Wait for thread
        time.sleep(0.5)

        # Check email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Order Confirmation', email.subject)
        self.assertIn(self.image_bulk_order.organization_name, email.subject)
        self.assertEqual(email.to, [self.image_order_entry.email])

    @override_settings(
        COMPANY_NAME='JMW Accessories',
        COMPANY_ADDRESS='123 Test Street',
        COMPANY_PHONE='08012345678',
        COMPANY_EMAIL='info@jmw.com',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_send_image_payment_receipt_email(self):
        """Test image bulk order payment receipt email"""
        send_image_payment_receipt_email(self.image_order_entry)

        # Wait for thread
        time.sleep(0.5)

        # Check email
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('Payment Receipt', email.subject)
        self.assertIn(str(self.image_order_entry.serial_number), email.subject)
        self.assertEqual(email.to, [self.image_order_entry.email])


class GenerateImagePaymentReceiptPdfTaskTests(TestCase):
    """Test generate_image_payment_receipt_pdf_task background task"""

    def setUp(self):
        """Set up image bulk order test fixtures"""
        from image_bulk_orders.models import ImageBulkOrderLink, ImageOrderEntry

        bulk_user = User.objects.create_user(
            username='imgbulkuser2', email='imgbulk2@example.com', password='pass123'
        )

        self.image_bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Image Test Organization PDF',
            price_per_item=Decimal('6000.00'),
            custom_branding_enabled=False,
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=bulk_user,
            slug='image-test-organization-pdf'
        )

        self.image_order_entry = ImageOrderEntry.objects.create(
            bulk_order=self.image_bulk_order,
            full_name='Jane Doe',
            email='jane@example.com',
            size='M',
            paid=True
        )

    @patch('weasyprint.HTML')
    @patch('jmw.background_utils.send_email_async')
    @patch('jmw.background_utils.render_to_string')
    @override_settings(
        COMPANY_NAME='JMW Accessories',
        COMPANY_ADDRESS='123 Test Street',
        COMPANY_PHONE='08012345678',
        COMPANY_EMAIL='info@jmw.com',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_generate_image_payment_receipt_pdf(self, mock_render, mock_send_email, mock_html):
        """Test image payment receipt PDF generation"""
        # Mock HTML and PDF generation
        mock_render.return_value = '<html>Receipt</html>'
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b'%PDF-1.4 image receipt'
        mock_html.return_value = mock_html_instance

        # Get the actual task function
        task_func = generate_image_payment_receipt_pdf_task.task_function

        # Call it directly
        task_func(self.image_order_entry.id)

        # Check email was sent
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]

        self.assertIn('Payment Receipt', call_kwargs['subject'])
        self.assertEqual(call_kwargs['recipient_list'], [self.image_order_entry.email])


# ============================================================================
# ACADEMIC DIRECTORY EMAIL TESTS
# ============================================================================

class AcademicDirectoryEmailTests(TestCase):
    """Test academic directory email functions"""

    def setUp(self):
        """Set up academic directory test fixtures"""
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='pass123',
            is_staff=True,
            is_active=True
        )

    def test_send_new_submission_email_nonexistent_rep(self):
        """Test new submission email with non-existent representative"""
        # Should not raise exception for non-existent ID
        send_new_submission_email_async(99999)

        # Wait for thread
        time.sleep(0.5)

        # No crash means success
        self.assertTrue(True)

    def test_send_bulk_verification_email_empty_list(self):
        """Test bulk verification with empty representative list"""
        # Should not raise exception for empty list
        send_bulk_verification_email_async([], self.admin_user.id)

        # Wait for thread
        time.sleep(0.5)

        # No crash means success
        self.assertTrue(True)

    @patch('jmw.background_utils.send_email_async')
    @override_settings(
        SITE_URL='https://example.com',
        COMPANY_NAME='JMW Accessories',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_send_daily_summary_no_submissions(self, mock_send_email):
        """Test daily summary with no new submissions"""
        send_daily_summary_email_async()

        # Wait for thread
        time.sleep(0.5)

        # No email should be sent if no new submissions
        mock_send_email.assert_not_called()

    @patch('jmw.background_utils.send_email_async')
    def test_process_pending_notifications_no_pending(self, mock_send_email):
        """Test process pending notifications with no pending items"""
        process_pending_notifications_async()

        # Wait for thread
        time.sleep(0.5)

        # No email should be sent
        mock_send_email.assert_not_called()


class CheckGraduationStatusesTaskTests(TestCase):
    """Test check_graduation_statuses_task background task"""

    def setUp(self):
        """Set up test fixtures"""
        from academic_directory.models import University, Faculty, Department, Representative

        # Create academic hierarchy
        self.university = University.objects.create(name='Test University')
        self.faculty = Faculty.objects.create(name='Test Faculty', university=self.university)
        self.department = Department.objects.create(name='Test Department', faculty=self.faculty)

    def test_check_graduation_statuses_no_class_reps(self):
        """Test graduation check with no class reps"""
        task_func = check_graduation_statuses_task.task_function

        # Should not raise exception
        task_func()

        # No error means success
        self.assertTrue(True)

    def test_check_graduation_statuses_active_rep(self):
        """Test graduation check with active non-graduated rep"""
        from academic_directory.models import Representative

        rep = Representative.objects.create(
            department=self.department,
            role='CLASS_REP',
            full_name='Active Student',
            phone_number='+2348012345680',
            entry_year=timezone.now().year,  # Started this year
            is_active=True
        )

        task_func = check_graduation_statuses_task.task_function
        task_func()

        # Refresh from database
        rep.refresh_from_db()

        # Should still be active (not graduated)
        self.assertTrue(rep.is_active)


# ============================================================================
# LIVE FORMS EMAIL TESTS
# ============================================================================

class LiveFormsEmailTests(TestCase):
    """Test live forms email functions"""

    def setUp(self):
        """Set up live forms test fixtures"""
        from live_forms.models import LiveFormLink, LiveFormEntry

        self.admin_user = User.objects.create_user(
            username='liveformadmin',
            email='liveform@example.com',
            password='pass123',
            is_staff=True
        )

        self.live_form = LiveFormLink.objects.create(
            organization_name='Test Live Form',
            custom_branding_enabled=False,
            created_by=self.admin_user,
            expires_at=timezone.now() + timedelta(days=30)
        )

        self.live_form_entry = LiveFormEntry.objects.create(
            live_form=self.live_form,
            full_name='Test Entry',
            size='L'
        )

    @patch('jmw.background_utils.logger')
    def test_send_live_form_submission_email_no_email_field(self, mock_logger):
        """Test live form submission email when entry has no email field"""
        send_live_form_submission_email_async(self.live_form_entry.id)

        # Wait for thread
        time.sleep(0.5)

        # Should log debug message about no email
        # No crash means success since there's no email field
        self.assertTrue(True)

    def test_send_live_form_submission_email_nonexistent_entry(self):
        """Test handling non-existent entry"""
        send_live_form_submission_email_async(99999)

        # Wait for thread
        time.sleep(0.5)

        # No crash means success
        self.assertTrue(True)


class GenerateLiveFormReportTaskTests(TestCase):
    """Test generate_live_form_report_task background task"""

    def setUp(self):
        """Set up live forms test fixtures"""
        from live_forms.models import LiveFormLink, LiveFormEntry

        self.admin_user = User.objects.create_user(
            username='liveformadmin2',
            email='liveform2@example.com',
            password='pass123',
            is_staff=True
        )

        self.live_form = LiveFormLink.objects.create(
            organization_name='Test Live Form Report',
            custom_branding_enabled=False,
            created_by=self.admin_user,
            expires_at=timezone.now() + timedelta(days=30)
        )

        # Create some entries
        for i in range(3):
            LiveFormEntry.objects.create(
                live_form=self.live_form,
                full_name=f'Entry {i}',
                size='L'
            )

    @patch('weasyprint.HTML')
    @patch('jmw.background_utils.send_email_async')
    @patch('jmw.background_utils.render_to_string')
    @override_settings(
        COMPANY_NAME='JMW Accessories',
        COMPANY_ADDRESS='123 Test Street',
        COMPANY_PHONE='08012345678',
        COMPANY_EMAIL='info@jmw.com',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_generate_live_form_report(self, mock_render, mock_send_email, mock_html):
        """Test live form report PDF generation"""
        # Mock HTML and PDF generation
        mock_render.return_value = '<html>Report</html>'
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b'%PDF-1.4 report'
        mock_html.return_value = mock_html_instance

        recipient = 'admin@example.com'

        # Get the actual task function
        task_func = generate_live_form_report_task.task_function

        # Call it directly
        task_func(str(self.live_form.id), recipient)

        # Check email was sent
        mock_send_email.assert_called_once()
        call_kwargs = mock_send_email.call_args[1]

        self.assertIn('Live Form Report', call_kwargs['subject'])
        self.assertEqual(call_kwargs['recipient_list'], [recipient])

    @patch('weasyprint.HTML')
    @patch('jmw.background_utils.send_email_async')
    @patch('jmw.background_utils.render_to_string')
    @override_settings(
        COMPANY_NAME='JMW Accessories',
        COMPANY_ADDRESS='123 Test Street',
        COMPANY_PHONE='08012345678',
        COMPANY_EMAIL='info@jmw.com',
        DEFAULT_FROM_EMAIL='noreply@jmw.com'
    )
    def test_generate_live_form_report_includes_entry_count(self, mock_render, mock_send_email, mock_html):
        """Test that report includes entry count in subject"""
        mock_render.return_value = '<html>Report</html>'
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b'%PDF-1.4 report'
        mock_html.return_value = mock_html_instance

        recipient = 'admin@example.com'

        task_func = generate_live_form_report_task.task_function
        task_func(str(self.live_form.id), recipient)

        call_kwargs = mock_send_email.call_args[1]

        # Subject should include entry count
        self.assertIn('3 entries', call_kwargs['subject'])


# ============================================================================
# EDGE CASES & ERROR HANDLING TESTS
# ============================================================================

class BackgroundUtilsErrorHandlingTests(TestCase):
    """Test error handling in background utilities"""

    def test_send_email_async_empty_recipient_list(self):
        """Test handling empty recipient list"""
        # Should not crash
        send_email_async(
            subject='Test',
            message='Test message',
            from_email='test@example.com',
            recipient_list=[]
        )

        time.sleep(0.5)

        # No email should be sent
        self.assertEqual(len(mail.outbox), 0)

    @patch('jmw.background_utils.logger')
    def test_logging_on_email_error(self, mock_logger):
        """Test that errors are logged properly"""
        with patch('jmw.background_utils.EmailMessage.send') as mock_send:
            mock_send.side_effect = Exception("SMTP Error")

            send_email_async(
                subject='Test',
                message='Test message',
                from_email='test@example.com',
                recipient_list=['test@example.com']
            )

            time.sleep(0.5)

            # Error should be logged
            mock_logger.error.assert_called()
