# excel_bulk_orders/tests/test_email_utils.py
"""
Comprehensive tests for Excel Bulk Orders email utilities.

Coverage:
- send_bulk_order_confirmation_email: Email sending, template rendering, context data
- Email formatting and styling
- Error handling
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from unittest.mock import patch, Mock, call
from django.utils import timezone

from excel_bulk_orders.models import ExcelBulkOrder
from excel_bulk_orders.email_utils import send_bulk_order_confirmation_email

User = get_user_model()


class SendBulkOrderConfirmationEmailTest(TestCase):
    """Test send_bulk_order_confirmation_email function"""

    def setUp(self):
        """Set up test data"""
        self.bulk_order = ExcelBulkOrder.objects.create(
            reference='EXL-EMAIL123',
            title='Email Test Order',
            coordinator_name='Test Coordinator',
            coordinator_email='coordinator@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            total_amount=Decimal('25000.00'),
            payment_status=True
        )

    @patch('excel_bulk_orders.email_utils.send_email_async')
    @patch('excel_bulk_orders.email_utils.render_to_string')
    def test_send_confirmation_email_success(self, mock_render, mock_send):
        """Test successful email sending"""
        mock_render.return_value = '<html>Email content</html>'

        # Send email
        send_bulk_order_confirmation_email(self.bulk_order, participants_count=5)

        # Verify render_to_string was called
        mock_render.assert_called_once()

        # Verify email was sent
        mock_send.assert_called_once()

        # Check email parameters
        call_kwargs = mock_send.call_args[1]
        self.assertIn('subject', call_kwargs)
        self.assertIn('message', call_kwargs)
        self.assertIn('html_message', call_kwargs)
        self.assertIn('recipient_list', call_kwargs)

        # Check recipient
        self.assertEqual(
            call_kwargs['recipient_list'],
            [self.bulk_order.coordinator_email]
        )

    @patch('excel_bulk_orders.email_utils.send_email_async')
    @patch('excel_bulk_orders.email_utils.render_to_string')
    def test_email_context_data(self, mock_render, mock_send):
        """Test that email context contains correct data"""
        mock_render.return_value = '<html>Email content</html>'

        send_bulk_order_confirmation_email(self.bulk_order, participants_count=5)

        # Get the context passed to render_to_string
        call_args = mock_render.call_args
        context = call_args[0][1]  # Second argument is context

        # Verify context data
        self.assertEqual(context['bulk_order'], self.bulk_order)
        self.assertEqual(context['coordinator_name'], self.bulk_order.coordinator_name)
        self.assertEqual(context['participants_count'], 5)
        self.assertIn('amount_paid', context)
        self.assertIn('payment_date', context)

    @patch('excel_bulk_orders.email_utils.send_email_async')
    @patch('excel_bulk_orders.email_utils.render_to_string')
    def test_email_subject_format(self, mock_render, mock_send):
        """Test email subject format"""
        mock_render.return_value = '<html>Email content</html>'

        send_bulk_order_confirmation_email(self.bulk_order, participants_count=5)

        call_kwargs = mock_send.call_args[1]
        subject = call_kwargs['subject']

        # Subject should contain title and reference
        self.assertIn(self.bulk_order.title, subject)
        self.assertIn(self.bulk_order.reference, subject)

    @patch('excel_bulk_orders.email_utils.send_email_async')
    @patch('excel_bulk_orders.email_utils.render_to_string')
    def test_email_with_zero_participants(self, mock_render, mock_send):
        """Test email sending with zero participants"""
        mock_render.return_value = '<html>Email content</html>'

        send_bulk_order_confirmation_email(self.bulk_order, participants_count=0)

        # Should still send email
        mock_send.assert_called_once()

    @patch('excel_bulk_orders.email_utils.send_email_async')
    @patch('excel_bulk_orders.email_utils.render_to_string')
    def test_email_template_rendering_failure(self, mock_render, mock_send):
        """Test handling of template rendering failure"""
        mock_render.side_effect = Exception('Template error')

        # Should not raise exception
        try:
            send_bulk_order_confirmation_email(self.bulk_order, participants_count=5)
        except Exception:
            self.fail('Should handle template rendering failure gracefully')

        # Email should not be sent if template fails
        mock_send.assert_not_called()

    @patch('excel_bulk_orders.email_utils.send_email_async')
    @patch('excel_bulk_orders.email_utils.render_to_string')
    def test_email_sending_failure(self, mock_render, mock_send):
        """Test handling of email sending failure"""
        mock_render.return_value = '<html>Email content</html>'
        mock_send.side_effect = Exception('Email sending failed')

        # Should not raise exception
        try:
            send_bulk_order_confirmation_email(self.bulk_order, participants_count=5)
        except Exception:
            self.fail('Should handle email sending failure gracefully')

    @patch('excel_bulk_orders.email_utils.send_email_async')
    @patch('excel_bulk_orders.email_utils.render_to_string')
    def test_plain_text_fallback_included(self, mock_render, mock_send):
        """Test that plain text fallback is included"""
        mock_render.return_value = '<html>Email content</html>'

        send_bulk_order_confirmation_email(self.bulk_order, participants_count=5)

        call_kwargs = mock_send.call_args[1]

        # Both message and html_message should be present
        self.assertIn('message', call_kwargs)
        self.assertIn('html_message', call_kwargs)
        self.assertIsNotNone(call_kwargs['message'])
        self.assertIsNotNone(call_kwargs['html_message'])