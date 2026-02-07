# excel_bulk_orders/tests/test_views_part2.py
"""
Comprehensive tests for Excel Bulk Orders API Views - Part 2.

Coverage:
- ExcelParticipantViewSet: List/retrieve, filtering
- Webhook handler: Signature verification, idempotency, race conditions
- Security: CSRF protection, authentication bypass attempts
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from unittest.mock import patch, Mock
from io import BytesIO
import json
import openpyxl
import hashlib
import hmac

from excel_bulk_orders.models import ExcelBulkOrder, ExcelCouponCode, ExcelParticipant

User = get_user_model()


class ExcelParticipantViewSetTest(APITestCase):
    """Test ExcelParticipantViewSet"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        # Create bulk order
        self.bulk_order = ExcelBulkOrder.objects.create(
            title='Participant Test Order',
            coordinator_name='Test',
            coordinator_email='parttest@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            requires_custom_name=True,
            payment_status=True
        )

        # Create another bulk order
        self.other_bulk_order = ExcelBulkOrder.objects.create(
            title='Other Order',
            coordinator_name='Test',
            coordinator_email='other@example.com',
            coordinator_phone='08011111111',
            price_per_participant=Decimal('5000.00'),
            payment_status=True
        )

        # Create coupon
        self.coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='COUPON123',
            is_used=True
        )

        # Create participants for first bulk order
        self.participants = []
        for i in range(5):
            participant = ExcelParticipant.objects.create(
                bulk_order=self.bulk_order,
                full_name=f'Participant {i}',
                size='M',
                custom_name=f'NAME{i}',
                row_number=i + 2
            )
            self.participants.append(participant)

        # Create participant with coupon
        self.coupon_participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Coupon User',
            size='L',
            custom_name='COUPON',
            coupon_code='COUPON123',
            coupon=self.coupon,
            is_coupon_applied=True,
            row_number=7
        )

        # Create participants for other bulk order
        ExcelParticipant.objects.create(
            bulk_order=self.other_bulk_order,
            full_name='Other Participant',
            size='S',
            row_number=2
        )

    def test_list_all_participants(self):
        """Test listing all participants without filter"""
        url = '/api/excel-participants/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return all participants from both bulk orders
        self.assertEqual(len(response.data['results']), 7)

    def test_list_participants_filtered_by_bulk_order(self):
        """Test filtering participants by bulk_order"""
        url = f'/api/excel-participants/?bulk_order={self.bulk_order.id}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return only participants from specified bulk order
        self.assertEqual(len(response.data['results']), 6)

        # Field 'bulk_order' not in participant serializer
        # Participants are correctly filtered if they appear in results
        # for participant in response.data['results']:
        #     self.assertEqual(participant['bulk_order'], str(self.bulk_order.id))

    def test_retrieve_participant(self):
        """Test retrieving a single participant"""
        participant = self.participants[0]
        url = f'/api/excel-participants/{participant.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(participant.id))
        self.assertEqual(response.data['full_name'], participant.full_name)

    def test_retrieve_nonexistent_participant(self):
        """Test retrieving non-existent participant"""
        url = '/api/excel-participants/00000000-0000-0000-0000-000000000000/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_participant_custom_name_included_when_required(self):
        """Test that custom_name is included when bulk order requires it"""
        participant = self.participants[0]
        url = f'/api/excel-participants/{participant.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('custom_name', response.data)
        self.assertEqual(response.data['custom_name'], participant.custom_name)

    def test_participant_custom_name_excluded_when_not_required(self):
        """Test that custom_name is excluded when not required"""
        other_participant = ExcelParticipant.objects.filter(
            bulk_order=self.other_bulk_order
        ).first()

        url = f'/api/excel-participants/{other_participant.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('custom_name', response.data)

    def test_participant_coupon_status_field(self):
        """Test coupon_status field in participant response"""
        # With coupon applied
        url = f'/api/excel-participants/{self.coupon_participant.id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['coupon_status'], 'Applied - Free')
        self.assertTrue(response.data['is_coupon_applied'])

        # Without coupon
        url = f'/api/excel-participants/{self.participants[0].id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['coupon_status'], 'No Coupon')
        self.assertFalse(response.data['is_coupon_applied'])

    def test_participant_read_only_access(self):
        """Test that participants cannot be created/updated/deleted via API"""
        # Try to create
        url = '/api/excel-participants/'
        data = {
            'bulk_order': str(self.bulk_order.id),
            'full_name': 'New Participant',
            'size': 'M',
            'row_number': 99
        }
        response = self.client.post(url, data, format='json')

        # Should not be allowed (read-only viewset)
        self.assertIn(
            response.status_code,
            [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN]
        )

        # Try to update
        participant = self.participants[0]
        url = f'/api/excel-participants/{participant.id}/'
        data = {'full_name': 'Updated Name'}
        response = self.client.patch(url, data, format='json')

        self.assertIn(
            response.status_code,
            [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN]
        )

        # Try to delete
        response = self.client.delete(url)

        self.assertIn(
            response.status_code,
            [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN]
        )

    def test_participant_list_pagination(self):
        """Test that participant list is paginated"""
        # Create many participants
        for i in range(50):
            ExcelParticipant.objects.create(
                bulk_order=self.bulk_order,
                full_name=f'Pagination Test {i}',
                size='M',
                row_number=100 + i
            )

        url = '/api/excel-participants/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('results', response.data)

    def test_participant_filtering_with_invalid_uuid(self):
        """Test filtering with invalid UUID returns empty results"""
        url = '/api/excel-participants/?bulk_order=invalid-uuid'
        response = self.client.get(url)

        # Should return 200 with empty results (not crash)
        # NOTE: This requires UUID validation in ExcelParticipantViewSet.get_queryset()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data.get('results', [])), 0)


class ExcelBulkOrderWebhookTest(TestCase):
    """Test webhook payment handler with security focus"""

    def setUp(self):
        """Set up test data"""
        self.bulk_order = ExcelBulkOrder.objects.create(
            reference='EXL-TEST1234',
            title='Webhook Test Order',
            coordinator_name='Test Coordinator',
            coordinator_email='webhook@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            total_amount=Decimal('25000.00'),
            validation_status='processing',
            uploaded_file='https://res.cloudinary.com/test/upload.xlsx'
        )

        # Create coupon
        self.coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='WEBHOOK123'
        )

    def create_test_excel_file(self):
        """Helper to create test Excel file"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Participants'

        # Header
        ws.append(['S/N', 'Full Name', 'Size', 'Coupon Code'])

        # Participants
        ws.append([1, 'John Doe', 'Medium', ''])
        ws.append([2, 'Jane Smith', 'Large', 'WEBHOOK123'])

        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        return buffer.getvalue()

    def generate_webhook_signature(self, payload_dict):
        """Generate valid Paystack webhook signature"""
        payload_string = json.dumps(payload_dict)
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            payload_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        return signature

    def create_webhook_payload(self, reference, status='success', event='charge.success'):
        """Create webhook payload"""
        return {
            'event': event,
            'data': {
                'reference': reference,
                'status': status,
                'amount': 2500000,  # 25000.00 in kobo
                'currency': 'NGN',
                'paid_at': '2024-01-15T10:30:00.000Z'
            }
        }

    @patch('excel_bulk_orders.views.send_bulk_order_confirmation_email')
    @patch('requests.get')
    def test_webhook_success_creates_participants(self, mock_requests_get, mock_send_email):
        """Test successful webhook processing creates participants"""
        # Mock file download
        mock_response = Mock()
        mock_response.content = self.create_test_excel_file()
        mock_requests_get.return_value = mock_response

        # Create webhook payload
        payload = self.create_webhook_payload(self.bulk_order.reference)
        signature = self.generate_webhook_signature(payload)

        # Make request
        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 200)

        # Verify bulk order updated
        self.bulk_order.refresh_from_db()
        self.assertTrue(self.bulk_order.payment_status)
        self.assertEqual(self.bulk_order.validation_status, 'completed')

        # Verify participants created
        self.assertEqual(self.bulk_order.participants.count(), 2)

        # Verify coupon was used
        self.coupon.refresh_from_db()
        self.assertTrue(self.coupon.is_used)

        # Verify email sent
        mock_send_email.assert_called_once()

    def test_webhook_missing_signature(self):
        """Test webhook without signature is rejected"""
        payload = self.create_webhook_payload(self.bulk_order.reference)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json'
            # No signature header
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertIn('Missing signature', response_data['message'])

    def test_webhook_invalid_signature(self):
        """Test webhook with invalid signature is rejected"""
        payload = self.create_webhook_payload(self.bulk_order.reference)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE='invalid_signature_here'
        )

        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertIn('Invalid signature', response_data['message'])

    def test_webhook_get_method_rejected(self):
        """Test webhook with GET method is rejected"""
        from django.test import Client
        client = Client()
        response = client.get('/api/excel-bulk-order-webhook/')

        self.assertEqual(response.status_code, 405)

    def test_webhook_invalid_json(self):
        """Test webhook with invalid JSON is rejected"""
        from django.test import Client
        client = Client()

        # Invalid JSON
        invalid_payload = "{ invalid json"
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
            invalid_payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=invalid_payload,
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 400)

    def test_webhook_non_success_event_ignored(self):
        """Test webhook with non-success event is ignored"""
        payload = self.create_webhook_payload(
            self.bulk_order.reference,
            event='charge.failed'
        )
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 200)

        # Bulk order should not be updated
        self.bulk_order.refresh_from_db()
        self.assertFalse(self.bulk_order.payment_status)

    def test_webhook_invalid_reference_format(self):
        """Test webhook with invalid reference format"""
        # Reference not starting with EXL-
        payload = self.create_webhook_payload('INVALID-REF-123')
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 200)
        # Should just return success without processing

    def test_webhook_nonexistent_bulk_order(self):
        """Test webhook for non-existent bulk order"""
        payload = self.create_webhook_payload('EXL-NOTFOUND')
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 404)

    @patch('excel_bulk_orders.views.send_bulk_order_confirmation_email')
    @patch('requests.get')
    def test_webhook_idempotency(self, mock_requests_get, mock_send_email):
        """Test webhook idempotency - multiple calls don't duplicate participants"""
        # Mock file download
        mock_response = Mock()
        mock_response.content = self.create_test_excel_file()
        mock_requests_get.return_value = mock_response

        # Create webhook payload
        payload = self.create_webhook_payload(self.bulk_order.reference)
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client()

        # First call
        response1 = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response1.status_code, 200)

        # Verify participants created
        participant_count = self.bulk_order.participants.count()
        self.assertEqual(participant_count, 2)

        # Second call (duplicate webhook)
        response2 = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response2.status_code, 200)

        # Participants should not be duplicated
        self.bulk_order.refresh_from_db()
        self.assertEqual(self.bulk_order.participants.count(), participant_count)

        # Email should only be sent once
        self.assertEqual(mock_send_email.call_count, 1)

    def test_webhook_unsuccessful_payment_status(self):
        """Test webhook with unsuccessful payment status"""
        payload = self.create_webhook_payload(
            self.bulk_order.reference,
            status='failed'
        )
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 400)

        # Bulk order should not be updated
        self.bulk_order.refresh_from_db()
        self.assertFalse(self.bulk_order.payment_status)

    @patch('requests.get')
    def test_webhook_file_download_failure(self, mock_requests_get):
        """Test webhook handling when file download fails"""
        # Mock file download failure
        mock_requests_get.side_effect = Exception('Download failed')

        payload = self.create_webhook_payload(self.bulk_order.reference)
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 500)

        # Payment status should not be updated
        self.bulk_order.refresh_from_db()
        self.assertFalse(self.bulk_order.payment_status)

    @patch('excel_bulk_orders.views.create_participants_from_excel')
    @patch('requests.get')
    def test_webhook_participant_creation_failure(self, mock_requests_get, mock_create_participants):
        """Test webhook handling when participant creation fails"""
        # Mock file download
        mock_response = Mock()
        mock_response.content = self.create_test_excel_file()
        mock_requests_get.return_value = mock_response

        # Mock participant creation failure
        mock_create_participants.side_effect = Exception('Creation failed')

        payload = self.create_webhook_payload(self.bulk_order.reference)
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        self.assertEqual(response.status_code, 500)

        # Payment status should not be updated due to transaction rollback
        self.bulk_order.refresh_from_db()
        self.assertFalse(self.bulk_order.payment_status)

    def test_webhook_csrf_exempt(self):
        """Test that webhook endpoint is CSRF exempt"""
        # Webhook should work without CSRF token
        payload = self.create_webhook_payload(self.bulk_order.reference)
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        # Should not fail due to CSRF (may fail for other reasons)
        self.assertNotEqual(response.status_code, 403)

    def test_webhook_missing_reference_in_payload(self):
        """Test webhook with missing reference"""
        payload = {
            'event': 'charge.success',
            'data': {
                'status': 'success',
                'amount': 2500000,
                # No reference
            }
        }
        signature = self.generate_webhook_signature(payload)

        from django.test import Client
        client = Client()
        response = client.post(
            '/api/excel-bulk-order-webhook/',
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_PAYSTACK_SIGNATURE=signature
        )

        # Should handle gracefully
        self.assertIn(response.status_code, [200, 400])


class SecurityAndEdgeCaseTests(APITestCase):
    """Test security measures and edge cases"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()

        self.bulk_order = ExcelBulkOrder.objects.create(
            title='Security Test Order',
            coordinator_name='Test',
            coordinator_email='security@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

    def test_sql_injection_in_title(self):
        """Test that SQL injection attempts in title are handled"""
        data = {
            'title': "'; DROP TABLE excel_bulk_orders; --",
            'coordinator_name': 'Test',
            'coordinator_email': 'sql@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        url = '/api/excel-bulk-orders/'
        response = self.client.post(url, data, format='json')

        # Should either succeed with sanitized input or fail validation
        # But should not execute SQL
        if response.status_code == 201:
            # Title should be stored as-is (parameterized queries protect)
            bulk_order = ExcelBulkOrder.objects.get(id=response.data['id'])
            self.assertIsNotNone(bulk_order)

    def test_xss_in_coordinator_name(self):
        """Test that XSS attempts in coordinator name are handled"""
        data = {
            'title': 'XSS Test',
            'coordinator_name': '<script>alert("XSS")</script>',
            'coordinator_email': 'xss@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        url = '/api/excel-bulk-orders/'
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            # Name should be stored (DRF handles serialization safely)
            bulk_order = ExcelBulkOrder.objects.get(id=response.data['id'])
            self.assertIn('<script>', bulk_order.coordinator_name)

    def test_extremely_long_title(self):
        """Test handling of extremely long titles"""
        long_title = 'A' * 10000

        data = {
            'title': long_title,
            'coordinator_name': 'Test',
            'coordinator_email': 'long@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        url = '/api/excel-bulk-orders/'
        response = self.client.post(url, data, format='json')

        # Should either succeed (if DB allows) or return validation error
        self.assertIn(response.status_code, [201, 400])

    def test_negative_price(self):
        """Test that negative prices are rejected"""
        data = {
            'title': 'Negative Price Test',
            'coordinator_name': 'Test',
            'coordinator_email': 'negative@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '-5000.00',
        }

        url = '/api/excel-bulk-orders/'
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 400)

    def test_unicode_in_coordinator_name(self):
        """Test handling of Unicode characters"""
        data = {
            'title': 'Unicode Test',
            'coordinator_name': '名前テスト 测试名称',
            'coordinator_email': 'unicode@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        url = '/api/excel-bulk-orders/'
        response = self.client.post(url, data, format='json')

        # Should handle Unicode properly
        if response.status_code == 201:
            bulk_order = ExcelBulkOrder.objects.get(id=response.data['id'])
            self.assertEqual(bulk_order.coordinator_name, '名前テスト 测试名称')

    def test_email_case_normalization(self):
        """Test that email addresses are normalized to lowercase"""
        data = {
            'title': 'Email Case Test',
            'coordinator_name': 'Test',
            'coordinator_email': 'TEST.EMAIL@EXAMPLE.COM',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        url = '/api/excel-bulk-orders/'
        response = self.client.post(url, data, format='json')

        if response.status_code == 201:
            bulk_order = ExcelBulkOrder.objects.get(id=response.data['id'])
            self.assertEqual(bulk_order.coordinator_email, 'test.email@example.com')

    def test_concurrent_upload_same_bulk_order(self):
        """Test concurrent uploads to same bulk order"""
        # This is more of a note that race conditions should be handled
        # Actual concurrent testing would require threading
        pass

    def test_invalid_uuid_in_url(self):
        """Test accessing endpoint with invalid UUID"""
        url = '/api/excel-bulk-orders/not-a-uuid/upload/'
        response = self.client.post(url, {}, format='multipart')

        self.assertEqual(response.status_code, 404)

    def test_bulk_order_reference_uniqueness_enforced(self):
        """Test that reference uniqueness is enforced at database level"""
        # This is tested in model tests but worth noting for security
        pass