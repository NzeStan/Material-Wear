# payment/tests/test_serializers.py
"""
Comprehensive bulletproof tests for payment/serializers.py

Test Coverage:
===============
✅ PaymentTransactionSerializer
   - Field presence and types
   - Read-only fields enforcement
   - Serialization (model -> dict)
   - Nested orders serialization
   - Custom method: get_order_count()
   - Multiple orders handling
   - No orders handling

✅ InitiatePaymentSerializer
   - Empty serializer validation
   - No required fields
   - Accepts any data

✅ PaymentResponseSerializer
   - Field validation
   - URL validation
   - Decimal field validation
   - Required fields
   - Data types

✅ VerifyPaymentSerializer
   - Reference field validation
   - Required field check
   - String validation

✅ PaymentStatusSerializer
   - All field types
   - Required fields
   - Boolean field
   - Decimal precision

✅ WebhookSerializer
   - Event field validation
   - Data dict field
   - Required fields
   - Help text presence

✅ Edge Cases
   - Empty data
   - Invalid data types
   - Missing required fields
   - Extra fields
   - Boundary values
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from decimal import Decimal
import uuid

from payment.serializers import (
    PaymentTransactionSerializer,
    InitiatePaymentSerializer,
    PaymentResponseSerializer,
    VerifyPaymentSerializer,
    PaymentStatusSerializer,
    WebhookSerializer
)
from payment.models import PaymentTransaction
from order.models import BaseOrder, NyscKitOrder

User = get_user_model()


# ============================================================================
# PAYMENT TRANSACTION SERIALIZER TESTS
# ============================================================================

class PaymentTransactionSerializerTests(TestCase):
    """Test PaymentTransactionSerializer"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
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
        
        self.payment = PaymentTransaction.objects.create(
            reference='JMW-TEST1234',
            amount=Decimal('25000.00'),
            email='john@example.com',
            status='success'
        )
        self.payment.orders.add(self.order1, self.order2)
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        serializer = PaymentTransactionSerializer(self.payment)
        
        expected_fields = {
            'id', 'reference', 'amount', 'email', 'status',
            'created', 'modified', 'orders', 'order_count'
        }
        
        self.assertEqual(set(serializer.data.keys()), expected_fields)
    
    def test_serializer_field_types(self):
        """Test serializer field types are correct"""
        serializer = PaymentTransactionSerializer(self.payment)
        data = serializer.data
        
        # ID field (integer AutoField, not UUID)
        self.assertIsInstance(data['id'], int)
        
        # String fields
        self.assertIsInstance(data['reference'], str)
        self.assertIsInstance(data['email'], str)
        self.assertIsInstance(data['status'], str)
        
        # Decimal field (serialized as string)
        self.assertEqual(data['amount'], '25000.00')
        
        # DateTime fields (ISO format strings)
        self.assertIsInstance(data['created'], str)
        self.assertIsInstance(data['modified'], str)
        
        # Related field (list)
        self.assertIsInstance(data['orders'], list)
        
        # SerializerMethodField
        self.assertIsInstance(data['order_count'], int)
    
    def test_serializer_read_only_fields(self):
        """Test that read-only fields cannot be written"""
        data = {
            'id': uuid.uuid4(),
            'reference': 'CUSTOM-REF',
            'created': '2024-01-01T00:00:00Z',
            'modified': '2024-01-02T00:00:00Z',
            'amount': '50000.00',
            'email': 'new@example.com',
            'status': 'pending'
        }
        
        serializer = PaymentTransactionSerializer(
            self.payment,
            data=data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        serializer.save()
        
        self.payment.refresh_from_db()
        
        # Read-only fields should not change
        self.assertNotEqual(str(self.payment.id), str(data['id']))
        self.assertEqual(self.payment.reference, 'JMW-TEST1234')  # Original
        
        # Writable fields should change
        self.assertEqual(self.payment.amount, Decimal('50000.00'))
        self.assertEqual(self.payment.email, 'new@example.com')
        self.assertEqual(self.payment.status, 'pending')
    
    def test_get_order_count_method(self):
        """Test get_order_count custom method"""
        serializer = PaymentTransactionSerializer(self.payment)
        
        self.assertEqual(serializer.data['order_count'], 2)
    
    def test_get_order_count_with_no_orders(self):
        """Test get_order_count with no orders"""
        payment = PaymentTransaction.objects.create(
            reference='JMW-NOORDERS',
            amount=Decimal('5000.00'),
            email='noorders@example.com',
            status='pending'
        )
        
        serializer = PaymentTransactionSerializer(payment)
        
        self.assertEqual(serializer.data['order_count'], 0)
    
    def test_orders_nested_serialization(self):
        """Test that orders are serialized with BaseOrderSerializer"""
        serializer = PaymentTransactionSerializer(self.payment)
        
        orders = serializer.data['orders']
        
        self.assertEqual(len(orders), 2)
        
        # Check first order has expected fields
        first_order = orders[0]
        self.assertIn('id', first_order)
        self.assertIn('serial_number', first_order)
        self.assertIn('first_name', first_order)
        self.assertIn('total_cost', first_order)
    
    def test_serializer_with_single_order(self):
        """Test serializer with single order"""
        payment = PaymentTransaction.objects.create(
            reference='JMW-SINGLE',
            amount=Decimal('10000.00'),
            email='single@example.com',
            status='pending'
        )
        payment.orders.add(self.order1)
        
        serializer = PaymentTransactionSerializer(payment)
        
        self.assertEqual(serializer.data['order_count'], 1)
        self.assertEqual(len(serializer.data['orders']), 1)
    
    def test_serializer_with_different_status_values(self):
        """Test serializer with different status values"""
        statuses = ['pending', 'success', 'failed']
        
        for status_value in statuses:
            payment = PaymentTransaction.objects.create(
                reference=f'JMW-{status_value.upper()}',
                amount=Decimal('5000.00'),
                email=f'{status_value}@example.com',
                status=status_value
            )
            
            serializer = PaymentTransactionSerializer(payment)
            
            self.assertEqual(serializer.data['status'], status_value)
    
    def test_serializer_preserves_decimal_precision(self):
        """Test that decimal amounts preserve precision"""
        payment = PaymentTransaction.objects.create(
            reference='JMW-DECIMAL',
            amount=Decimal('12345.67'),
            email='decimal@example.com'
        )
        
        serializer = PaymentTransactionSerializer(payment)
        
        self.assertEqual(serializer.data['amount'], '12345.67')
    
    def test_serializer_with_metadata(self):
        """Test serializer with payment containing metadata"""
        payment = PaymentTransaction.objects.create(
            reference='JMW-META',
            amount=Decimal('5000.00'),
            email='meta@example.com',
            metadata={'customer_name': 'Test User', 'orders': ['123', '456']}
        )
        
        serializer = PaymentTransactionSerializer(payment)
        
        # Metadata is not in serializer fields, but payment should have it
        self.assertNotIn('metadata', serializer.data)
        self.assertEqual(payment.metadata['customer_name'], 'Test User')
    
    def test_serializer_list_serialization(self):
        """Test serializing multiple payments"""
        payment2 = PaymentTransaction.objects.create(
            reference='JMW-SECOND',
            amount=Decimal('15000.00'),
            email='second@example.com',
            status='pending'
        )
        
        payments = [self.payment, payment2]
        serializer = PaymentTransactionSerializer(payments, many=True)
        
        self.assertEqual(len(serializer.data), 2)
        self.assertEqual(serializer.data[0]['reference'], 'JMW-TEST1234')
        self.assertEqual(serializer.data[1]['reference'], 'JMW-SECOND')


# ============================================================================
# INITIATE PAYMENT SERIALIZER TESTS
# ============================================================================

class InitiatePaymentSerializerTests(TestCase):
    """Test InitiatePaymentSerializer"""
    
    def test_serializer_is_empty(self):
        """Test that InitiatePaymentSerializer has no fields"""
        serializer = InitiatePaymentSerializer()
        
        # Should have no fields (uses session data)
        self.assertEqual(len(serializer.fields), 0)
    
    def test_serializer_accepts_empty_data(self):
        """Test serializer validates with empty data"""
        serializer = InitiatePaymentSerializer(data={})
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data, {})
    
    def test_serializer_accepts_any_data(self):
        """Test serializer accepts any data (ignores it)"""
        data = {
            'some_field': 'some_value',
            'another_field': 123
        }
        
        serializer = InitiatePaymentSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        # Data is ignored since there are no fields
        self.assertEqual(serializer.validated_data, {})
    
    def test_serializer_no_errors(self):
        """Test serializer never raises validation errors"""
        serializer = InitiatePaymentSerializer(data={'anything': 'goes'})
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.errors, {})


# ============================================================================
# PAYMENT RESPONSE SERIALIZER TESTS
# ============================================================================

class PaymentResponseSerializerTests(TestCase):
    """Test PaymentResponseSerializer"""
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = {
            'authorization_url': 'https://checkout.paystack.com/test123',
            'access_code': 'test_access_code',
            'reference': 'JMW-TEST1234',
            'amount': '25000.00'
        }
        
        serializer = PaymentResponseSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        
        expected_fields = {'authorization_url', 'access_code', 'reference', 'amount'}
        self.assertEqual(set(serializer.validated_data.keys()), expected_fields)
    
    def test_authorization_url_validation(self):
        """Test authorization_url must be valid URL"""
        # Valid URL
        data = {
            'authorization_url': 'https://checkout.paystack.com/test',
            'access_code': 'test',
            'reference': 'REF',
            'amount': '1000.00'
        }
        
        serializer = PaymentResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid URL
        data['authorization_url'] = 'not-a-url'
        serializer = PaymentResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('authorization_url', serializer.errors)
    
    def test_amount_decimal_validation(self):
        """Test amount field accepts valid decimals"""
        data = {
            'authorization_url': 'https://test.com',
            'access_code': 'test',
            'reference': 'REF',
            'amount': '12345.67'
        }
        
        serializer = PaymentResponseSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['amount'], Decimal('12345.67'))
    
    def test_amount_max_digits_validation(self):
        """Test amount respects max_digits constraint"""
        # Valid: 8 digits + 2 decimals = 10 total
        data = {
            'authorization_url': 'https://test.com',
            'access_code': 'test',
            'reference': 'REF',
            'amount': '99999999.99'
        }
        
        serializer = PaymentResponseSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid: More than 10 total digits
        data['amount'] = '999999999.99'  # 11 digits total
        serializer = PaymentResponseSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('amount', serializer.errors)
    
    def test_required_fields(self):
        """Test all fields are required"""
        required_fields = ['authorization_url', 'access_code', 'reference', 'amount']
        
        for field in required_fields:
            data = {
                'authorization_url': 'https://test.com',
                'access_code': 'test',
                'reference': 'REF',
                'amount': '1000.00'
            }
            
            # Remove one field
            del data[field]
            
            serializer = PaymentResponseSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)
    
    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored"""
        data = {
            'authorization_url': 'https://test.com',
            'access_code': 'test',
            'reference': 'REF',
            'amount': '1000.00',
            'extra_field': 'should_be_ignored'
        }
        
        serializer = PaymentResponseSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data)


# ============================================================================
# VERIFY PAYMENT SERIALIZER TESTS
# ============================================================================

class VerifyPaymentSerializerTests(TestCase):
    """Test VerifyPaymentSerializer"""
    
    def test_serializer_contains_reference_field(self):
        """Test serializer has reference field"""
        data = {'reference': 'JMW-TEST1234'}
        
        serializer = VerifyPaymentSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['reference'], 'JMW-TEST1234')
    
    def test_reference_is_required(self):
        """Test reference field is required"""
        serializer = VerifyPaymentSerializer(data={})
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('reference', serializer.errors)
    
    def test_reference_accepts_string(self):
        """Test reference accepts string values"""
        references = [
            'JMW-TEST1234',
            'CUSTOM-REF-123',
            'ref_with_underscores',
            'REF-WITH-DASHES'
        ]
        
        for ref in references:
            serializer = VerifyPaymentSerializer(data={'reference': ref})
            self.assertTrue(serializer.is_valid())
            self.assertEqual(serializer.validated_data['reference'], ref)
    
    def test_reference_rejects_invalid_types(self):
        """Test reference rejects invalid types (None, lists, dicts)"""
        # CharField in DRF coerces many types to strings (int, bool)
        # Only None and complex types like lists/dicts fail
        invalid_values = [None, [], {}]
        
        for value in invalid_values:
            serializer = VerifyPaymentSerializer(data={'reference': value})
            self.assertFalse(serializer.is_valid(), 
                           f"Serializer should reject {type(value).__name__}: {value}")
            self.assertIn('reference', serializer.errors)
    
    def test_reference_coerces_simple_types(self):
        """Test that CharField coerces integers to strings"""
        # DRF CharField coerces integers to strings
        # Note: Boolean coercion behavior varies by DRF version
        coercible_values = [123, 456]
        
        for value in coercible_values:
            serializer = VerifyPaymentSerializer(data={'reference': value})
            self.assertTrue(serializer.is_valid(),
                          f"Serializer should accept coercible {type(value).__name__}: {value}")
            # Value is coerced to string
            self.assertIsInstance(serializer.validated_data['reference'], str)
            self.assertEqual(serializer.validated_data['reference'], str(value))
    
    def test_extra_fields_ignored(self):
        """Test extra fields are ignored"""
        data = {
            'reference': 'JMW-TEST',
            'extra_field': 'ignored'
        }
        
        serializer = VerifyPaymentSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('extra_field', serializer.validated_data)


# ============================================================================
# PAYMENT STATUS SERIALIZER TESTS
# ============================================================================

class PaymentStatusSerializerTests(TestCase):
    """Test PaymentStatusSerializer"""
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains all expected fields"""
        data = {
            'reference': 'JMW-TEST1234',
            'status': 'success',
            'amount': '25000.00',
            'paid': True,
            'message': 'Payment successful'
        }
        
        serializer = PaymentStatusSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        
        expected_fields = {'reference', 'status', 'amount', 'paid', 'message'}
        self.assertEqual(set(serializer.validated_data.keys()), expected_fields)
    
    def test_all_fields_required(self):
        """Test all fields are required"""
        required_fields = ['reference', 'status', 'amount', 'paid', 'message']
        
        for field in required_fields:
            data = {
                'reference': 'REF',
                'status': 'success',
                'amount': '1000.00',
                'paid': True,
                'message': 'Success'
            }
            
            del data[field]
            
            serializer = PaymentStatusSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn(field, serializer.errors)
    
    def test_paid_boolean_field(self):
        """Test paid field accepts boolean values"""
        for paid_value in [True, False]:
            data = {
                'reference': 'REF',
                'status': 'success',
                'amount': '1000.00',
                'paid': paid_value,
                'message': 'Test'
            }
            
            serializer = PaymentStatusSerializer(data=data)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(serializer.validated_data['paid'], paid_value)
    
    def test_status_values(self):
        """Test various status values"""
        statuses = ['success', 'failed', 'pending', 'processing']
        
        for status_value in statuses:
            data = {
                'reference': 'REF',
                'status': status_value,
                'amount': '1000.00',
                'paid': True,
                'message': 'Test'
            }
            
            serializer = PaymentStatusSerializer(data=data)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(serializer.validated_data['status'], status_value)
    
    def test_amount_decimal_precision(self):
        """Test amount preserves decimal precision"""
        data = {
            'reference': 'REF',
            'status': 'success',
            'amount': '12345.67',
            'paid': True,
            'message': 'Success'
        }
        
        serializer = PaymentStatusSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['amount'], Decimal('12345.67'))
    
    def test_message_field_accepts_strings(self):
        """Test message field accepts various strings"""
        messages = [
            'Payment successful',
            'Payment failed',
            'An error occurred',
            'Transaction verification failed'
        ]
        
        for message in messages:
            data = {
                'reference': 'REF',
                'status': 'success',
                'amount': '1000.00',
                'paid': True,
                'message': message
            }
            
            serializer = PaymentStatusSerializer(data=data)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(serializer.validated_data['message'], message)


# ============================================================================
# WEBHOOK SERIALIZER TESTS
# ============================================================================

class WebhookSerializerTests(TestCase):
    """Test WebhookSerializer"""
    
    def test_serializer_contains_expected_fields(self):
        """Test serializer contains event and data fields"""
        data = {
            'event': 'charge.success',
            'data': {
                'reference': 'JMW-TEST',
                'amount': 1000000,
                'status': 'success'
            }
        }
        
        serializer = WebhookSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(set(serializer.validated_data.keys()), {'event', 'data'})
    
    def test_event_field_validation(self):
        """Test event field accepts string values"""
        events = [
            'charge.success',
            'charge.failed',
            'transfer.success',
            'subscription.create'
        ]
        
        for event in events:
            data = {
                'event': event,
                'data': {'test': 'value'}
            }
            
            serializer = WebhookSerializer(data=data)
            self.assertTrue(serializer.is_valid())
            self.assertEqual(serializer.validated_data['event'], event)
    
    def test_data_field_accepts_dict(self):
        """Test data field accepts dictionary"""
        test_data = {
            'reference': 'JMW-TEST',
            'amount': 1000000,
            'customer': {
                'email': 'test@example.com',
                'name': 'Test User'
            },
            'metadata': {
                'order_id': '123',
                'custom_field': 'value'
            }
        }
        
        data = {
            'event': 'charge.success',
            'data': test_data
        }
        
        serializer = WebhookSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['data'], test_data)
    
    def test_data_field_accepts_empty_dict(self):
        """Test data field accepts empty dictionary"""
        data = {
            'event': 'test.event',
            'data': {}
        }
        
        serializer = WebhookSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['data'], {})
    
    def test_both_fields_required(self):
        """Test both event and data are required"""
        # Missing event
        serializer = WebhookSerializer(data={'data': {}})
        self.assertFalse(serializer.is_valid())
        self.assertIn('event', serializer.errors)
        
        # Missing data
        serializer = WebhookSerializer(data={'event': 'test'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('data', serializer.errors)
    
    def test_data_field_rejects_non_dict(self):
        """Test data field rejects non-dictionary values"""
        invalid_values = ['string', 123, True, ['list']]
        
        for value in invalid_values:
            data = {
                'event': 'test',
                'data': value
            }
            
            serializer = WebhookSerializer(data=data)
            self.assertFalse(serializer.is_valid())
            self.assertIn('data', serializer.errors)
    
    def test_help_text_present(self):
        """Test that help_text is defined for fields"""
        serializer = WebhookSerializer()
        
        self.assertEqual(serializer.fields['event'].help_text, 'Event type')
        self.assertEqual(serializer.fields['data'].help_text, 'Event data')


# ============================================================================
# EDGE CASES & INTEGRATION TESTS
# ============================================================================

class SerializerEdgeCasesTests(TestCase):
    """Test edge cases and integration scenarios"""
    
    def test_payment_transaction_serializer_with_nysckit_order(self):
        """Test PaymentTransactionSerializer with NyscKitOrder"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        
        kit_order = NyscKitOrder.objects.create(
            user=user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('50000.00')
        )
        
        payment = PaymentTransaction.objects.create(
            reference='JMW-KIT',
            amount=Decimal('50000.00'),
            email='john@example.com',
            status='success'
        )
        payment.orders.add(kit_order)
        
        serializer = PaymentTransactionSerializer(payment)
        
        self.assertEqual(serializer.data['order_count'], 1)
        self.assertEqual(len(serializer.data['orders']), 1)
        
        # Check base order fields are present
        # Note: BaseOrderSerializer only includes base fields, not subclass-specific fields
        order_data = serializer.data['orders'][0]
        self.assertIn('id', order_data)
        self.assertIn('serial_number', order_data)
        self.assertIn('first_name', order_data)
        self.assertIn('total_cost', order_data)
        self.assertIn('paid', order_data)
    
    def test_payment_response_with_very_long_url(self):
        """Test PaymentResponseSerializer with very long URL"""
        long_url = 'https://checkout.paystack.com/' + 'a' * 500
        
        data = {
            'authorization_url': long_url,
            'access_code': 'test',
            'reference': 'REF',
            'amount': '1000.00'
        }
        
        serializer = PaymentResponseSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['authorization_url'], long_url)
    
    def test_payment_status_with_zero_amount(self):
        """Test PaymentStatusSerializer with zero amount"""
        data = {
            'reference': 'REF',
            'status': 'success',
            'amount': '0.00',
            'paid': True,
            'message': 'Free item'
        }
        
        serializer = PaymentStatusSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['amount'], Decimal('0.00'))
    
    def test_webhook_with_nested_data(self):
        """Test WebhookSerializer with deeply nested data"""
        data = {
            'event': 'charge.success',
            'data': {
                'reference': 'REF',
                'customer': {
                    'email': 'test@example.com',
                    'metadata': {
                        'custom_fields': [
                            {'name': 'field1', 'value': 'value1'},
                            {'name': 'field2', 'value': 'value2'}
                        ]
                    }
                }
            }
        }
        
        serializer = WebhookSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data['data']['customer']['email'],
            'test@example.com'
        )
    
    def test_verify_payment_with_empty_string(self):
        """Test VerifyPaymentSerializer rejects empty string"""
        serializer = VerifyPaymentSerializer(data={'reference': ''})
        
        # Empty string should fail validation
        self.assertFalse(serializer.is_valid())
        self.assertIn('reference', serializer.errors)
    
    def test_payment_response_with_special_characters_in_reference(self):
        """Test PaymentResponseSerializer with special characters"""
        data = {
            'authorization_url': 'https://test.com',
            'access_code': 'test_123',
            'reference': 'JMW-TEST_123-ABC',
            'amount': '1000.00'
        }
        
        serializer = PaymentResponseSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data['reference'],
            'JMW-TEST_123-ABC'
        )


# ============================================================================
# SERIALIZER REPRESENTATION TESTS
# ============================================================================

class SerializerRepresentationTests(TestCase):
    """Test serializer representation and output format"""
    
    def test_payment_transaction_serializer_representation(self):
        """Test that PaymentTransactionSerializer produces correct representation"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
        
        order = BaseOrder.objects.create(
            user=user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        payment = PaymentTransaction.objects.create(
            reference='JMW-REPR',
            amount=Decimal('10000.00'),
            email='john@example.com',
            status='pending'
        )
        payment.orders.add(order)
        
        serializer = PaymentTransactionSerializer(payment)
        
        # Check output is JSON-serializable
        import json
        json_output = json.dumps(serializer.data)
        self.assertIsInstance(json_output, str)
        
        # Parse back and verify
        parsed = json.loads(json_output)
        self.assertEqual(parsed['reference'], 'JMW-REPR')
        self.assertEqual(parsed['status'], 'pending')
    
    def test_serializer_with_none_values(self):
        """Test serializers handle None values appropriately"""
        # PaymentTransaction doesn't allow None for required fields,
        # but test serializer behavior with optional fields
        
        payment = PaymentTransaction.objects.create(
            reference='JMW-NONE',
            amount=Decimal('5000.00'),
            email='none@example.com'
        )
        
        serializer = PaymentTransactionSerializer(payment)
        
        # Should serialize without errors
        self.assertIsNotNone(serializer.data)
        self.assertEqual(serializer.data['reference'], 'JMW-NONE')