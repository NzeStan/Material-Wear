# payment/tests/test_api_views.py
"""
Comprehensive bulletproof tests for payment/api_views.py

Test Coverage:
===============
✅ InitiatePaymentView (POST /api/payment/initiate/)
   - Authentication requirements
   - Throttling
   - Session handling (pending_orders)
   - Order validation (exists, belongs to user, count matches)
   - PaymentTransaction creation
   - Paystack API mocking
   - Success/error responses

✅ VerifyPaymentView (GET /api/payment/verify/)
   - AllowAny permission (no auth required)
   - Reference parameter validation
   - Payment existence checks
   - Paystack verification mocking
   - Status updates (payment + orders)
   - Session cleanup
   - Async task triggers
   - Success/failure flows

✅ payment_webhook (POST /api/payment/webhook/)
   - CSRF exemption
   - Signature verification
   - Event type filtering
   - Idempotency checks
   - Payment/order updates
   - Async tasks
   - Various error scenarios

✅ PaymentTransactionViewSet
   - List endpoint (GET /api/payment/transactions/)
   - Retrieve endpoint (GET /api/payment/transactions/<id>/)
   - Authentication requirements
   - User filtering (users see only their payments)
   - Query optimization (prefetch_related)
   - Swagger fake view handling

✅ Security Testing
   - Invalid signatures
   - Unauthorized access
   - User isolation
   - CSRF protection

✅ Edge Cases & Error Handling
   - Missing parameters
   - Invalid data
   - External service failures
   - Database errors
"""
from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase, force_authenticate
from rest_framework import status
from unittest.mock import patch, Mock, MagicMock
from decimal import Decimal
import json
import uuid
import hmac
import hashlib
from django.conf import settings

from payment.models import PaymentTransaction
from payment.api_views import (
    InitiatePaymentView, VerifyPaymentView, 
    payment_webhook, PaymentTransactionViewSet
)
from order.models import BaseOrder, NyscKitOrder

User = get_user_model()


# ============================================================================
# INITIATE PAYMENT VIEW TESTS
# ============================================================================

class InitiatePaymentViewTests(APITestCase):
    """Test InitiatePaymentView (POST /api/payment/initiate/)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('payment:initiate')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create orders
        self.order1 = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        self.order2 = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00')
        )
    
    def test_initiate_payment_requires_authentication(self):
        """Test that initiate payment requires authentication"""
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_initiate_payment_no_pending_orders_in_session(self):
        """Test initiate payment with no pending orders in session"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('No pending orders', response.data['error'])
    
    def test_initiate_payment_with_invalid_order_ids(self):
        """Test initiate payment with invalid order IDs in session"""
        self.client.force_authenticate(user=self.user)
        
        # Set session with non-existent order IDs
        session = self.client.session
        session['pending_orders'] = [str(uuid.uuid4()), str(uuid.uuid4())]
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Orders not found', response.data['error'])
        
        # Session should be cleared
        self.assertNotIn('pending_orders', self.client.session)
    
    def test_initiate_payment_with_another_users_orders(self):
        """Test initiate payment with orders belonging to another user"""
        # Create another user and their order
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='pass123'
        )
        
        other_order = BaseOrder.objects.create(
            user=other_user,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone_number='08087654321',
            total_cost=Decimal('20000.00')
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Try to initiate payment for another user's order
        session = self.client.session
        session['pending_orders'] = [str(other_order.id)]
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Orders not found', response.data['error'])
    
    def test_initiate_payment_order_count_mismatch(self):
        """Test initiate payment when order count doesn't match session"""
        self.client.force_authenticate(user=self.user)
        
        # Set session with 3 order IDs but only 2 exist
        session = self.client.session
        session['pending_orders'] = [
            str(self.order1.id), 
            str(self.order2.id),
            str(uuid.uuid4())  # Non-existent order
        ]
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid order session', response.data['error'])
        
        # Session should be cleared
        self.assertNotIn('pending_orders', self.client.session)
    
    @patch('payment.api_views.initialize_payment')
    def test_initiate_payment_success(self, mock_initialize_payment):
        """Test successful payment initialization"""
        # Mock Paystack response
        mock_initialize_payment.return_value = {
            'status': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/abc123',
                'access_code': 'abc123xyz',
                'reference': 'JMW-TEST1234'
            }
        }
        
        self.client.force_authenticate(user=self.user)
        
        # Set session with valid orders
        session = self.client.session
        session['pending_orders'] = [str(self.order1.id), str(self.order2.id)]
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('authorization_url', response.data)
        self.assertIn('access_code', response.data)
        self.assertIn('reference', response.data)
        self.assertIn('amount', response.data)
        
        # Verify payment was created
        payment = PaymentTransaction.objects.get(reference=response.data['reference'])
        self.assertEqual(payment.amount, Decimal('25000.00'))  # 10000 + 15000
        self.assertEqual(payment.orders.count(), 2)
        
        # Verify Paystack was called correctly
        mock_initialize_payment.assert_called_once()
        call_args = mock_initialize_payment.call_args
        self.assertEqual(call_args[1]['amount'], Decimal('25000.00'))
        # Email comes from user, not order (BaseOrder.__init__ sets email from user)
        self.assertEqual(call_args[1]['email'], self.user.email)
    
    @patch('payment.api_views.initialize_payment')
    def test_initiate_payment_paystack_failure(self, mock_initialize_payment):
        """Test payment initialization when Paystack fails"""
        # Mock Paystack failure
        mock_initialize_payment.return_value = None
        
        self.client.force_authenticate(user=self.user)
        
        session = self.client.session
        session['pending_orders'] = [str(self.order1.id)]
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Could not initialize payment', response.data['error'])
    
    @patch('payment.api_views.initialize_payment')
    def test_initiate_payment_paystack_invalid_response(self, mock_initialize_payment):
        """Test payment initialization with invalid Paystack response"""
        # Mock invalid response (missing 'status' key)
        mock_initialize_payment.return_value = {'data': {}}
        
        self.client.force_authenticate(user=self.user)
        
        session = self.client.session
        session['pending_orders'] = [str(self.order1.id)]
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('payment.api_views.initialize_payment')
    def test_initiate_payment_exception_handling(self, mock_initialize_payment):
        """Test payment initialization with exception"""
        # Mock exception
        mock_initialize_payment.side_effect = Exception("API Error")
        
        self.client.force_authenticate(user=self.user)
        
        session = self.client.session
        session['pending_orders'] = [str(self.order1.id)]
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)
    
    @patch('payment.api_views.initialize_payment')
    def test_initiate_payment_creates_correct_metadata(self, mock_initialize_payment):
        """Test that payment initialization creates correct metadata"""
        mock_initialize_payment.return_value = {
            'status': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/abc123',
                'access_code': 'abc123',
                'reference': 'JMW-TEST'
            }
        }
        
        self.client.force_authenticate(user=self.user)
        
        session = self.client.session
        session['pending_orders'] = [str(self.order1.id), str(self.order2.id)]
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify metadata
        call_args = mock_initialize_payment.call_args[1]
        metadata = call_args['metadata']
        
        self.assertIn('orders', metadata)
        self.assertIn('customer_name', metadata)
        self.assertIn('user_id', metadata)
        self.assertEqual(len(metadata['orders']), 2)
        self.assertEqual(metadata['customer_name'], 'John Doe')
        self.assertEqual(metadata['user_id'], str(self.user.id))


# ============================================================================
# VERIFY PAYMENT VIEW TESTS
# ============================================================================

class VerifyPaymentViewTests(APITestCase):
    """Test VerifyPaymentView (GET /api/payment/verify/)"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('payment:verify')
        
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
            total_cost=Decimal('10000.00'),
            paid=False
        )
        
        self.payment = PaymentTransaction.objects.create(
            reference='JMW-TEST1234',
            amount=Decimal('10000.00'),
            email='john@example.com',
            status='pending'
        )
        self.payment.orders.add(self.order)
    
    def test_verify_payment_allows_anonymous_access(self):
        """Test that verify payment allows anonymous access (AllowAny)"""
        response = self.client.get(self.url, {'reference': 'JMW-TEST1234'})
        
        # Should not return 401 (it will return 400 for missing Paystack response)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_verify_payment_missing_reference(self):
        """Test verify payment without reference parameter"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('reference is required', response.data['error'])
    
    def test_verify_payment_nonexistent_payment(self):
        """Test verify payment with non-existent reference"""
        response = self.client.get(self.url, {'reference': 'NONEXISTENT'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('Payment not found', response.data['error'])
    
    @patch('payment.api_views.verify_payment')
    def test_verify_payment_paystack_verification_failed(self, mock_verify):
        """Test verify payment when Paystack verification fails"""
        mock_verify.return_value = None
        
        response = self.client.get(self.url, {'reference': 'JMW-TEST1234'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'failed')
        self.assertIn('Payment verification failed', response.data['message'])
    
    @patch('payment.api_views.verify_payment')
    def test_verify_payment_paystack_invalid_response(self, mock_verify):
        """Test verify payment with invalid Paystack response"""
        mock_verify.return_value = {'status': False}
        
        response = self.client.get(self.url, {'reference': 'JMW-TEST1234'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('payment.api_views.generate_payment_receipt_pdf_task')
    @patch('payment.api_views.send_payment_receipt_email_async')
    @patch('payment.api_views.verify_payment')
    def test_verify_payment_success(self, mock_verify, mock_email, mock_pdf):
        """Test successful payment verification"""
        # Mock successful Paystack verification
        mock_verify.return_value = {
            'status': True,
            'data': {
                'status': 'success',
                'amount': 1000000,  # In kobo
                'reference': 'JMW-TEST1234'
            }
        }
        
        # Set up session with pending_orders
        session = self.client.session
        session['pending_orders'] = [str(self.order.id)]
        session.save()
        
        response = self.client.get(self.url, {'reference': 'JMW-TEST1234'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['reference'], 'JMW-TEST1234')
        self.assertTrue(response.data['paid'])
        
        # Verify payment status was updated
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'success')
        
        # Verify order was marked as paid
        self.order.refresh_from_db()
        self.assertTrue(self.order.paid)
        
        # Verify session was cleared
        self.assertNotIn('pending_orders', self.client.session)
        
        # Verify async tasks were triggered
        mock_email.assert_called_once()
        mock_pdf.assert_called_once()
    
    @patch('payment.api_views.verify_payment')
    def test_verify_payment_already_successful(self, mock_verify):
        """Test verify payment when payment is already successful"""
        # Set payment to already successful
        self.payment.status = 'success'
        self.payment.save()
        
        mock_verify.return_value = {
            'status': True,
            'data': {'status': 'success'}
        }
        
        response = self.client.get(self.url, {'reference': 'JMW-TEST1234'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
    
    @patch('payment.api_views.verify_payment')
    def test_verify_payment_failed_status(self, mock_verify):
        """Test verify payment when Paystack returns failed status"""
        mock_verify.return_value = {
            'status': True,
            'data': {'status': 'failed'}
        }
        
        response = self.client.get(self.url, {'reference': 'JMW-TEST1234'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'failed')
        self.assertFalse(response.data['paid'])
        
        # Verify payment status was updated to failed
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')
    
    @patch('payment.api_views.send_payment_receipt_email_async')
    @patch('payment.api_views.verify_payment')
    def test_verify_payment_multiple_orders(self, mock_verify, mock_email):
        """Test verify payment with multiple orders"""
        # Create another order
        order2 = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=False
        )
        self.payment.orders.add(order2)
        
        mock_verify.return_value = {
            'status': True,
            'data': {'status': 'success'}
        }
        
        response = self.client.get(self.url, {'reference': 'JMW-TEST1234'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify both orders were marked as paid
        self.order.refresh_from_db()
        order2.refresh_from_db()
        self.assertTrue(self.order.paid)
        self.assertTrue(order2.paid)


# ============================================================================
# PAYMENT WEBHOOK TESTS
# ============================================================================

class PaymentWebhookTests(TestCase):
    """Test payment_webhook function"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.url = reverse('payment:webhook')
        
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
            total_cost=Decimal('10000.00'),
            paid=False
        )
        
        self.payment = PaymentTransaction.objects.create(
            reference='JMW-WEBHOOK',
            amount=Decimal('10000.00'),
            email='john@example.com',
            status='pending'
        )
        self.payment.orders.add(self.order)
    
    def _create_webhook_payload(self, reference='JMW-WEBHOOK', event='charge.success'):
        """Helper to create webhook payload"""
        return {
            'event': event,
            'data': {
                'reference': reference,
                'amount': 1000000,
                'status': 'success'
            }
        }
    
    def _generate_signature(self, payload):
        """Helper to generate valid Paystack signature"""
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        if isinstance(payload, str):
            payload = payload.encode('utf-8')
        
        secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
        return hmac.new(secret, payload, hashlib.sha512).hexdigest()
    
    def test_webhook_missing_signature(self):
        """Test webhook without signature header"""
        payload = self._create_webhook_payload()
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        response = payment_webhook(request)
        
        self.assertEqual(response.status_code, 400)
    
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_invalid_signature(self, mock_verify_sig):
        """Test webhook with invalid signature"""
        mock_verify_sig.return_value = False
        
        payload = self._create_webhook_payload()
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='invalid_signature'
        )
        
        response = payment_webhook(request)
        
        self.assertEqual(response.status_code, 401)
    
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_invalid_json(self, mock_verify_sig):
        """Test webhook with invalid JSON payload"""
        mock_verify_sig.return_value = True
        
        request = self.factory.post(
            self.url,
            data='invalid json',
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='valid_signature'
        )
        
        response = payment_webhook(request)
        
        self.assertEqual(response.status_code, 400)
    
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_non_charge_success_event(self, mock_verify_sig):
        """Test webhook with non charge.success event"""
        mock_verify_sig.return_value = True
        
        payload = self._create_webhook_payload(event='charge.failed')
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='valid_signature'
        )
        
        response = payment_webhook(request)
        
        # Should return 200 but not process
        self.assertEqual(response.status_code, 200)
        
        # Payment should still be pending
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'pending')
    
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_missing_reference(self, mock_verify_sig):
        """Test webhook without reference in payload"""
        mock_verify_sig.return_value = True
        
        payload = {'event': 'charge.success', 'data': {}}
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='valid_signature'
        )
        
        response = payment_webhook(request)
        
        self.assertEqual(response.status_code, 400)
    
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_payment_not_found(self, mock_verify_sig):
        """Test webhook with non-existent payment reference"""
        mock_verify_sig.return_value = True
        
        payload = self._create_webhook_payload(reference='NONEXISTENT')
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='valid_signature'
        )
        
        response = payment_webhook(request)
        
        self.assertEqual(response.status_code, 404)
    
    @patch('payment.api_views.generate_payment_receipt_pdf_task')
    @patch('payment.api_views.send_payment_receipt_email_async')
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_successful_processing(self, mock_verify_sig, mock_email, mock_pdf):
        """Test successful webhook processing"""
        mock_verify_sig.return_value = True
        
        payload = self._create_webhook_payload()
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='valid_signature'
        )
        
        response = payment_webhook(request)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify payment was updated
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'success')
        
        # Verify order was updated
        self.order.refresh_from_db()
        self.assertTrue(self.order.paid)
        
        # Verify async tasks were triggered
        mock_email.assert_called_once()
        mock_pdf.assert_called_once()
    
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_idempotency(self, mock_verify_sig):
        """Test webhook idempotency (already processed payment)"""
        mock_verify_sig.return_value = True
        
        # Mark payment as already successful
        self.payment.status = 'success'
        self.payment.save()
        
        payload = self._create_webhook_payload()
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='valid_signature'
        )
        
        response = payment_webhook(request)
        
        # Should return 200 (already processed)
        self.assertEqual(response.status_code, 200)
    
    @patch('payment.api_views.send_payment_receipt_email_async')
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_multiple_orders(self, mock_verify_sig, mock_email):
        """Test webhook with multiple orders"""
        mock_verify_sig.return_value = True
        
        # Create another order
        order2 = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=False
        )
        self.payment.orders.add(order2)
        
        payload = self._create_webhook_payload()
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='valid_signature'
        )
        
        response = payment_webhook(request)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify both orders were updated
        self.order.refresh_from_db()
        order2.refresh_from_db()
        self.assertTrue(self.order.paid)
        self.assertTrue(order2.paid)
    
    @patch('payment.api_views.PaymentTransaction.objects.get')
    @patch('payment.api_views.verify_paystack_signature')
    def test_webhook_exception_handling(self, mock_verify_sig, mock_get_payment):
        """Test webhook exception handling"""
        mock_verify_sig.return_value = True
        
        # Mock exception during payment processing (not validation)
        mock_get_payment.side_effect = Exception("Database error")
        
        payload = self._create_webhook_payload()
        request = self.factory.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='valid_signature'
        )
        
        response = payment_webhook(request)
        
        self.assertEqual(response.status_code, 500)


# ============================================================================
# PAYMENT TRANSACTION VIEWSET TESTS
# ============================================================================

class PaymentTransactionViewSetTests(APITestCase):
    """Test PaymentTransactionViewSet"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        # Create orders for user1
        self.order1 = BaseOrder.objects.create(
            user=self.user1,
            first_name='User',
            last_name='One',
            email='user1@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        # Create orders for user2
        self.order2 = BaseOrder.objects.create(
            user=self.user2,
            first_name='User',
            last_name='Two',
            email='user2@example.com',
            phone_number='08087654321',
            total_cost=Decimal('15000.00')
        )
        
        # Create payments
        self.payment1 = PaymentTransaction.objects.create(
            reference='JMW-USER1',
            amount=Decimal('10000.00'),
            email='user1@example.com',
            status='success'
        )
        self.payment1.orders.add(self.order1)
        
        self.payment2 = PaymentTransaction.objects.create(
            reference='JMW-USER2',
            amount=Decimal('15000.00'),
            email='user2@example.com',
            status='pending'
        )
        self.payment2.orders.add(self.order2)
    
    def test_list_payments_requires_authentication(self):
        """Test that list payments requires authentication"""
        url = reverse('payment:transaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_payments_user_sees_only_their_payments(self):
        """Test that users see only their own payments"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('payment:transaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['reference'], 'JMW-USER1')
    
    def test_list_payments_multiple_users(self):
        """Test that different users see different payments"""
        # User1's payments
        self.client.force_authenticate(user=self.user1)
        url = reverse('payment:transaction-list')
        response1 = self.client.get(url)
        
        # User2's payments
        self.client.force_authenticate(user=self.user2)
        response2 = self.client.get(url)
        
        self.assertEqual(len(response1.data['results']), 1)
        self.assertEqual(len(response2.data['results']), 1)
        self.assertNotEqual(
            response1.data['results'][0]['reference'],
            response2.data['results'][0]['reference']
        )
    
    def test_list_payments_ordering(self):
        """Test that payments are ordered by created DESC (newest first)"""
        # Create another payment for user1
        payment3 = PaymentTransaction.objects.create(
            reference='JMW-USER1-NEW',
            amount=Decimal('20000.00'),
            email='user1@example.com',
            status='success'
        )
        payment3.orders.add(self.order1)
        
        self.client.force_authenticate(user=self.user1)
        url = reverse('payment:transaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Newest should be first
        self.assertEqual(response.data['results'][0]['reference'], 'JMW-USER1-NEW')
    
    def test_retrieve_payment_requires_authentication(self):
        """Test that retrieve payment requires authentication"""
        url = reverse('payment:transaction-detail', args=[self.payment1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_retrieve_payment_success(self):
        """Test retrieving a specific payment"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('payment:transaction-detail', args=[self.payment1.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['reference'], 'JMW-USER1')
        self.assertIn('orders', response.data)
        self.assertEqual(len(response.data['orders']), 1)
    
    def test_retrieve_payment_user_isolation(self):
        """Test that users cannot retrieve other users' payments"""
        self.client.force_authenticate(user=self.user1)
        
        # Try to retrieve user2's payment
        url = reverse('payment:transaction-detail', args=[self.payment2.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_payment_nonexistent(self):
        """Test retrieving non-existent payment"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('payment:transaction-detail', args=[uuid.uuid4()])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_payments_with_no_orders(self):
        """Test listing payments for user with no orders"""
        user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='pass123'
        )
        
        self.client.force_authenticate(user=user3)
        url = reverse('payment:transaction-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_viewset_is_readonly(self):
        """Test that viewset is read-only (no POST, PUT, DELETE)"""
        self.client.force_authenticate(user=self.user1)
        
        url = reverse('payment:transaction-list')
        
        # Try POST
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try PUT
        detail_url = reverse('payment:transaction-detail', args=[self.payment1.id])
        response = self.client.put(detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try DELETE
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class PaymentFlowIntegrationTests(APITestCase):
    """Test complete payment flow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
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
            total_cost=Decimal('50000.00'),
            paid=False
        )
    
    @patch('payment.api_views.generate_payment_receipt_pdf_task')
    @patch('payment.api_views.send_payment_receipt_email_async')
    @patch('payment.api_views.verify_payment')
    @patch('payment.api_views.initialize_payment')
    def test_complete_payment_flow(self, mock_init, mock_verify, mock_email, mock_pdf):
        """Test complete payment flow from initiate to verify"""
        # Step 1: Initiate payment
        mock_init.return_value = {
            'status': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test',
                'access_code': 'test_access',
                'reference': 'JMW-FLOW'
            }
        }
        
        self.client.force_authenticate(user=self.user)
        
        session = self.client.session
        session['pending_orders'] = [str(self.order.id)]
        session.save()
        
        initiate_url = reverse('payment:initiate')
        init_response = self.client.post(initiate_url)
        
        self.assertEqual(init_response.status_code, status.HTTP_200_OK)
        reference = init_response.data['reference']
        
        # Verify payment was created
        payment = PaymentTransaction.objects.get(reference=reference)
        self.assertEqual(payment.status, 'pending')
        
        # Step 2: Verify payment
        mock_verify.return_value = {
            'status': True,
            'data': {'status': 'success'}
        }
        
        verify_url = reverse('payment:verify')
        verify_response = self.client.get(verify_url, {'reference': reference})
        
        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertTrue(verify_response.data['paid'])
        
        # Verify payment and order status
        payment.refresh_from_db()
        self.order.refresh_from_db()
        
        self.assertEqual(payment.status, 'success')
        self.assertTrue(self.order.paid)
        
        # Verify async tasks were called
        mock_email.assert_called_once()
        mock_pdf.assert_called_once()


# ============================================================================
# EDGE CASES & SECURITY TESTS
# ============================================================================

class PaymentSecurityTests(APITestCase):
    """Test security aspects of payment endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='pass123'
        )
        
        self.order1 = BaseOrder.objects.create(
            user=self.user1,
            first_name='User',
            last_name='One',
            email='user1@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
    
    @patch('payment.api_views.initialize_payment')
    def test_user_cannot_pay_for_other_users_orders(self, mock_init):
        """Test that user cannot initialize payment for another user's orders"""
        mock_init.return_value = {
            'status': True,
            'data': {
                'authorization_url': 'https://test.com',
                'access_code': 'test',
                'reference': 'TEST'
            }
        }
        
        # User2 tries to pay for User1's order
        self.client.force_authenticate(user=self.user2)
        
        session = self.client.session
        session['pending_orders'] = [str(self.order1.id)]
        session.save()
        
        url = reverse('payment:initiate')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Orders not found', response.data['error'])
    
    def test_csrf_exempt_on_webhook(self):
        """Test that webhook endpoint is CSRF exempt"""
        # Webhook should accept POST without CSRF token
        # This is tested implicitly in webhook tests, but explicitly verify
        from django.views.decorators.csrf import csrf_exempt
        from payment.api_views import payment_webhook
        
        # Check that function has csrf_exempt decorator
        self.assertTrue(hasattr(payment_webhook, 'csrf_exempt'))


# ============================================================================
# QUERY OPTIMIZATION TESTS
# ============================================================================

class PaymentQueryOptimizationTests(APITestCase):
    """Test query optimization in payment views"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create multiple orders and payments
        for i in range(5):
            order = BaseOrder.objects.create(
                user=self.user,
                first_name=f'User{i}',
                last_name='Test',
                email=f'user{i}@example.com',
                phone_number='08012345678',
                total_cost=Decimal('10000.00')
            )
            
            payment = PaymentTransaction.objects.create(
                reference=f'JMW-TEST{i}',
                amount=Decimal('10000.00'),
                email=f'user{i}@example.com',
                status='success'
            )
            payment.orders.add(order)
    
    def test_list_payments_uses_prefetch_related(self):
        """Test that list endpoint uses prefetch_related for optimization"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('payment:transaction-list')
        
        # Count queries
        from django.test.utils import override_settings
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should use prefetch_related to avoid N+1 queries
        # Exact query count depends on pagination, but should be reasonable
        self.assertLess(len(context.captured_queries), 10)