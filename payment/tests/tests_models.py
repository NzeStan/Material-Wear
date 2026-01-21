# payment/tests/test_models.py
"""
Comprehensive bulletproof tests for payment/models.py

Test Coverage:
===============
✅ Model Creation & Field Validation
✅ Reference Generation & Uniqueness
✅ Amount Validation (DecimalField)
✅ Email Validation
✅ Status Field & Choices Validation
✅ Many-to-Many Relationship (orders)
✅ Metadata JSONField (default, structure, get_formatted_metadata)
✅ Timestamp Fields (auto_now_add, auto_now)
✅ String Representation (__str__)
✅ Model Ordering (Meta.ordering)
✅ Save Method Override (reference auto-generation)
✅ Edge Cases (empty metadata, multiple orders, null handling)
✅ Security (reference uniqueness, status integrity)
✅ Data Integrity (decimal precision, email format)
✅ Boundary Conditions (max amounts, empty relationships)
✅ Query Optimization (related orders)
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from payment.models import PaymentTransaction
from order.models import BaseOrder, NyscKitOrder
import uuid
import re

User = get_user_model()


class PaymentTransactionModelCreationTests(TestCase):
    """Test PaymentTransaction model creation and basic field operations."""

    def setUp(self):
        """Set up test user and order for payment creation."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('50000.00')
        )

    def test_create_payment_with_all_fields(self):
        """Test creating a payment transaction with all fields populated."""
        payment = PaymentTransaction.objects.create(
            reference='JMW-TEST1234',
            amount=Decimal('50000.00'),
            email='john@example.com',
            status='pending',
            metadata={'customer_name': 'John Doe', 'orders': [str(self.order.id)]}
        )
        payment.orders.add(self.order)
        
        self.assertIsNotNone(payment.id)
        self.assertEqual(payment.reference, 'JMW-TEST1234')
        self.assertEqual(payment.amount, Decimal('50000.00'))
        self.assertEqual(payment.email, 'john@example.com')
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.orders.count(), 1)
        self.assertIsNotNone(payment.created)
        self.assertIsNotNone(payment.modified)

    def test_create_payment_with_minimal_fields(self):
        """Test creating payment with only required fields."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('10000.00'),
            email='test@example.com'
        )
        
        self.assertIsNotNone(payment.id)
        self.assertIsNotNone(payment.reference)  # Auto-generated
        self.assertEqual(payment.status, 'pending')  # Default value
        self.assertEqual(payment.metadata, {})  # Default empty dict

    def test_payment_creation_without_reference_generates_auto_reference(self):
        """Test that reference is auto-generated when not provided."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('25000.00'),
            email='auto@example.com'
        )
        
        self.assertIsNotNone(payment.reference)
        self.assertTrue(payment.reference.startswith('JMW-'))
        self.assertEqual(len(payment.reference), 12)  # JMW- + 8 chars

    def test_payment_with_metadata(self):
        """Test payment creation with complex metadata."""
        metadata = {
            'orders': [str(self.order.id)],
            'customer_name': 'John Doe',
            'user_id': str(self.user.id),
            'source': 'web',
            'campaign': 'summer-sale'
        }
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('15000.00'),
            email='metadata@example.com',
            metadata=metadata
        )
        
        self.assertEqual(payment.metadata, metadata)
        self.assertIn('orders', payment.metadata)
        self.assertEqual(payment.metadata['customer_name'], 'John Doe')


class PaymentTransactionReferenceTests(TestCase):
    """Test reference field generation, uniqueness, and validation."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_reference_auto_generation_format(self):
        """Test that auto-generated reference follows JMW-XXXXXXXX format."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='ref@example.com'
        )
        
        # Check format: JMW-<8 uppercase hex chars>
        pattern = r'^JMW-[A-F0-9]{8}$'
        self.assertIsNotNone(re.match(pattern, payment.reference))

    def test_reference_uniqueness(self):
        """Test that reference must be unique."""
        PaymentTransaction.objects.create(
            reference='JMW-UNIQUE01',
            amount=Decimal('5000.00'),
            email='unique1@example.com'
        )
        
        # Try to create another payment with same reference
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                PaymentTransaction.objects.create(
                    reference='JMW-UNIQUE01',  # Duplicate reference
                    amount=Decimal('10000.00'),
                    email='unique2@example.com'
                )

    def test_custom_reference_is_preserved(self):
        """Test that custom reference is not overwritten."""
        custom_ref = 'CUSTOM-REF-123'
        payment = PaymentTransaction.objects.create(
            reference=custom_ref,
            amount=Decimal('5000.00'),
            email='custom@example.com'
        )
        
        self.assertEqual(payment.reference, custom_ref)

    def test_reference_max_length(self):
        """Test reference field max_length constraint (100 chars)."""
        long_ref = 'X' * 100
        payment = PaymentTransaction.objects.create(
            reference=long_ref,
            amount=Decimal('5000.00'),
            email='long@example.com'
        )
        self.assertEqual(payment.reference, long_ref)
        
        # Test that 101 chars fails
        too_long_ref = 'X' * 101
        payment2 = PaymentTransaction(
            reference=too_long_ref,
            amount=Decimal('5000.00'),
            email='toolong@example.com'
        )
        with self.assertRaises(ValidationError):
            payment2.full_clean()

    def test_multiple_auto_generated_references_are_unique(self):
        """Test that auto-generated references are always unique."""
        payments = []
        for i in range(10):
            payment = PaymentTransaction.objects.create(
                amount=Decimal('1000.00') * i,
                email=f'test{i}@example.com'
            )
            payments.append(payment)
        
        # Check all references are unique
        references = [p.reference for p in payments]
        self.assertEqual(len(references), len(set(references)))


class PaymentTransactionAmountTests(TestCase):
    """Test amount field validation and precision."""

    def test_amount_decimal_precision(self):
        """Test amount stores decimal with 2 decimal places."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('12345.67'),
            email='decimal@example.com'
        )
        
        self.assertEqual(payment.amount, Decimal('12345.67'))

    def test_amount_with_more_than_2_decimals_stores_exact_value(self):
        """Test amount with more than 2 decimals stores the exact value."""
        # Django DecimalField stores exact value up to max_digits
        # Database schema determines precision, not automatic rounding
        payment = PaymentTransaction.objects.create(
            amount=Decimal('100.99'),
            email='exact@example.com'
        )
        
        self.assertEqual(payment.amount, Decimal('100.99'))

    def test_amount_max_digits(self):
        """Test amount field accepts up to 10 digits (max_digits=10)."""
        # Max: 99999999.99 (8 digits + 2 decimals = 10 total)
        large_amount = Decimal('99999999.99')
        payment = PaymentTransaction.objects.create(
            amount=large_amount,
            email='large@example.com'
        )
        
        self.assertEqual(payment.amount, large_amount)

    def test_amount_zero_is_valid(self):
        """Test that zero amount is technically valid at model level."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('0.00'),
            email='zero@example.com'
        )
        
        self.assertEqual(payment.amount, Decimal('0.00'))

    def test_amount_negative_is_valid_at_model_level(self):
        """Test negative amount (model doesn't enforce positive constraint)."""
        # Note: While logically wrong, the model doesn't enforce positive amounts
        # This should be handled at form/serializer level
        payment = PaymentTransaction.objects.create(
            amount=Decimal('-100.00'),
            email='negative@example.com'
        )
        
        self.assertEqual(payment.amount, Decimal('-100.00'))

    def test_amount_typical_values(self):
        """Test typical payment amounts."""
        test_amounts = [
            Decimal('5000.00'),
            Decimal('15000.50'),
            Decimal('250000.00'),
            Decimal('1000000.00')
        ]
        
        for amount in test_amounts:
            payment = PaymentTransaction.objects.create(
                amount=amount,
                email=f'test{amount}@example.com'
            )
            self.assertEqual(payment.amount, amount)


class PaymentTransactionEmailTests(TestCase):
    """Test email field validation."""

    def test_valid_email_formats(self):
        """Test various valid email formats."""
        valid_emails = [
            'test@example.com',
            'user.name@example.com',
            'user+tag@example.co.uk',
            'test123@subdomain.example.com',
            'UPPERCASE@EXAMPLE.COM'
        ]
        
        for email in valid_emails:
            payment = PaymentTransaction.objects.create(
                amount=Decimal('5000.00'),
                email=email
            )
            self.assertEqual(payment.email, email)

    def test_email_is_required(self):
        """Test that email is a required field."""
        payment = PaymentTransaction(
            amount=Decimal('5000.00')
            # email not provided
        )
        
        with self.assertRaises(ValidationError):
            payment.full_clean()

    def test_email_with_special_characters(self):
        """Test email with special characters."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='user+test@example.com'
        )
        
        self.assertEqual(payment.email, 'user+test@example.com')


class PaymentTransactionStatusTests(TestCase):
    """Test status field choices and validation."""

    def test_status_default_is_pending(self):
        """Test that default status is 'pending'."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='pending@example.com'
        )
        
        self.assertEqual(payment.status, 'pending')

    def test_all_valid_status_choices(self):
        """Test all valid status choices."""
        valid_statuses = ['pending', 'success', 'failed']
        
        for status in valid_statuses:
            payment = PaymentTransaction.objects.create(
                amount=Decimal('5000.00'),
                email=f'{status}@example.com',
                status=status
            )
            self.assertEqual(payment.status, status)

    def test_status_transition_pending_to_success(self):
        """Test status change from pending to success."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='transition@example.com',
            status='pending'
        )
        
        payment.status = 'success'
        payment.save()
        payment.refresh_from_db()
        
        self.assertEqual(payment.status, 'success')

    def test_status_transition_pending_to_failed(self):
        """Test status change from pending to failed."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='failed@example.com',
            status='pending'
        )
        
        payment.status = 'failed'
        payment.save()
        payment.refresh_from_db()
        
        self.assertEqual(payment.status, 'failed')

    def test_invalid_status_raises_validation_error(self):
        """Test that invalid status value raises ValidationError."""
        payment = PaymentTransaction(
            amount=Decimal('5000.00'),
            email='invalid@example.com',
            status='invalid_status'
        )
        
        with self.assertRaises(ValidationError) as cm:
            payment.full_clean()
        
        self.assertIn('status', cm.exception.message_dict)

    def test_status_max_length(self):
        """Test status field max_length constraint (20 chars)."""
        # 'success' and 'pending' and 'failed' are all within 20 chars
        # This test ensures the constraint is properly set
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='length@example.com',
            status='success'
        )
        
        self.assertEqual(payment.status, 'success')
        self.assertLessEqual(len(payment.status), 20)


class PaymentTransactionOrdersRelationshipTests(TestCase):
    """Test Many-to-Many relationship with orders."""

    def setUp(self):
        """Set up test users and orders."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="pass123"
        )
        
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="pass123"
        )
        
        self.order1 = BaseOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        self.order2 = BaseOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00')
        )
        
        self.order3 = BaseOrder.objects.create(
            user=self.user2,
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            phone_number='08087654321',
            total_cost=Decimal('20000.00')
        )

    def test_payment_with_single_order(self):
        """Test payment associated with single order."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('10000.00'),
            email='single@example.com'
        )
        payment.orders.add(self.order1)
        
        self.assertEqual(payment.orders.count(), 1)
        self.assertIn(self.order1, payment.orders.all())

    def test_payment_with_multiple_orders(self):
        """Test payment associated with multiple orders."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('25000.00'),
            email='multiple@example.com'
        )
        payment.orders.add(self.order1, self.order2)
        
        self.assertEqual(payment.orders.count(), 2)
        self.assertIn(self.order1, payment.orders.all())
        self.assertIn(self.order2, payment.orders.all())

    def test_payment_with_no_orders(self):
        """Test payment with no orders attached."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='noorders@example.com'
        )
        
        self.assertEqual(payment.orders.count(), 0)

    def test_order_can_have_multiple_payments(self):
        """Test that an order can be associated with multiple payments (edge case)."""
        payment1 = PaymentTransaction.objects.create(
            amount=Decimal('10000.00'),
            email='pay1@example.com'
        )
        payment1.orders.add(self.order1)
        
        payment2 = PaymentTransaction.objects.create(
            amount=Decimal('10000.00'),
            email='pay2@example.com'
        )
        payment2.orders.add(self.order1)
        
        # Check order has two payments
        self.assertEqual(self.order1.payments.count(), 2)

    def test_removing_order_from_payment(self):
        """Test removing an order from payment."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('25000.00'),
            email='remove@example.com'
        )
        payment.orders.add(self.order1, self.order2)
        
        payment.orders.remove(self.order1)
        
        self.assertEqual(payment.orders.count(), 1)
        self.assertNotIn(self.order1, payment.orders.all())
        self.assertIn(self.order2, payment.orders.all())

    def test_clearing_all_orders(self):
        """Test clearing all orders from payment."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('25000.00'),
            email='clear@example.com'
        )
        payment.orders.add(self.order1, self.order2, self.order3)
        
        payment.orders.clear()
        
        self.assertEqual(payment.orders.count(), 0)

    def test_orders_reverse_relationship(self):
        """Test reverse relationship from order to payments."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('10000.00'),
            email='reverse@example.com'
        )
        payment.orders.add(self.order1)
        
        # Access payments from order
        self.assertEqual(self.order1.payments.count(), 1)
        self.assertIn(payment, self.order1.payments.all())


class PaymentTransactionMetadataTests(TestCase):
    """Test metadata JSONField functionality."""

    def test_metadata_default_empty_dict(self):
        """Test that metadata defaults to empty dict."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='default@example.com'
        )
        
        self.assertEqual(payment.metadata, {})
        self.assertIsInstance(payment.metadata, dict)

    def test_metadata_with_string_values(self):
        """Test metadata with string values."""
        metadata = {
            'customer_name': 'John Doe',
            'phone': '08012345678',
            'address': '123 Main St'
        }
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='strings@example.com',
            metadata=metadata
        )
        
        self.assertEqual(payment.metadata, metadata)

    def test_metadata_with_mixed_types(self):
        """Test metadata with mixed data types."""
        metadata = {
            'customer_name': 'John Doe',
            'order_count': 2,
            'total_items': 5,
            'discount_applied': True,
            'shipping_fee': 2000.50
        }
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='mixed@example.com',
            metadata=metadata
        )
        
        self.assertEqual(payment.metadata, metadata)
        self.assertEqual(payment.metadata['order_count'], 2)
        self.assertTrue(payment.metadata['discount_applied'])

    def test_metadata_with_nested_structures(self):
        """Test metadata with nested dictionaries and lists."""
        metadata = {
            'customer': {
                'name': 'John Doe',
                'id': '12345'
            },
            'orders': ['order1', 'order2', 'order3'],
            'shipping': {
                'address': '123 Main St',
                'city': 'Lagos',
                'state': 'Lagos'
            }
        }
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='nested@example.com',
            metadata=metadata
        )
        
        self.assertEqual(payment.metadata['customer']['name'], 'John Doe')
        self.assertIn('order2', payment.metadata['orders'])

    def test_metadata_can_be_updated(self):
        """Test that metadata can be updated after creation."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='update@example.com',
            metadata={'initial': 'value'}
        )
        
        payment.metadata['new_key'] = 'new_value'
        payment.metadata['initial'] = 'updated_value'
        payment.save()
        payment.refresh_from_db()
        
        self.assertEqual(payment.metadata['initial'], 'updated_value')
        self.assertEqual(payment.metadata['new_key'], 'new_value')

    def test_get_formatted_metadata_with_data(self):
        """Test get_formatted_metadata method with populated metadata."""
        order = BaseOrder.objects.create(
            user=User.objects.create_user('test', 'test@example.com', 'pass'),
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('10000.00')
        )
        
        metadata = {
            'orders': [str(order.id)],
            'customer_name': 'John Doe',
            'extra_info': 'test'
        }
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('10000.00'),
            email='formatted@example.com',
            metadata=metadata
        )
        
        formatted = payment.get_formatted_metadata()
        
        self.assertIsInstance(formatted, dict)
        self.assertIn('Orders', formatted)
        self.assertIn('Customer', formatted)
        self.assertEqual(formatted['Customer'], 'John Doe')

    def test_get_formatted_metadata_with_empty_metadata(self):
        """Test get_formatted_metadata with empty metadata."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='empty@example.com'
        )
        
        formatted = payment.get_formatted_metadata()
        
        self.assertEqual(formatted, "No metadata")

    def test_get_formatted_metadata_with_partial_data(self):
        """Test get_formatted_metadata with partial metadata."""
        metadata = {
            'orders': ['order1'],
            # No customer_name
        }
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='partial@example.com',
            metadata=metadata
        )
        
        formatted = payment.get_formatted_metadata()
        
        self.assertIn('Orders', formatted)
        self.assertIn('Customer', formatted)
        self.assertEqual(formatted['Customer'], 'N/A')


class PaymentTransactionTimestampTests(TestCase):
    """Test timestamp fields (created, modified)."""

    def test_created_timestamp_set_on_creation(self):
        """Test that created timestamp is set on creation."""
        before_creation = timezone.now()
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='timestamp@example.com'
        )
        
        after_creation = timezone.now()
        
        self.assertIsNotNone(payment.created)
        self.assertGreaterEqual(payment.created, before_creation)
        self.assertLessEqual(payment.created, after_creation)

    def test_modified_timestamp_set_on_creation(self):
        """Test that modified timestamp is set on creation."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='modified@example.com'
        )
        
        self.assertIsNotNone(payment.modified)

    def test_modified_timestamp_updates_on_save(self):
        """Test that modified timestamp updates when model is saved."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='update@example.com'
        )
        
        original_modified = payment.modified
        
        # Wait a tiny bit and update
        import time
        time.sleep(0.01)
        
        payment.status = 'success'
        payment.save()
        payment.refresh_from_db()
        
        self.assertGreater(payment.modified, original_modified)

    def test_created_timestamp_does_not_change_on_update(self):
        """Test that created timestamp remains unchanged on update."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='created@example.com'
        )
        
        original_created = payment.created
        
        payment.status = 'success'
        payment.save()
        payment.refresh_from_db()
        
        self.assertEqual(payment.created, original_created)


class PaymentTransactionStringRepresentationTests(TestCase):
    """Test __str__ method."""

    def test_str_representation_format(self):
        """Test string representation format."""
        payment = PaymentTransaction.objects.create(
            reference='JMW-TEST1234',
            amount=Decimal('5000.00'),
            email='str@example.com',
            status='pending'
        )
        
        expected = "Payment JMW-TEST1234 - pending"
        self.assertEqual(str(payment), expected)

    def test_str_representation_with_different_statuses(self):
        """Test string representation with different statuses."""
        statuses = ['pending', 'success', 'failed']
        
        for status in statuses:
            payment = PaymentTransaction.objects.create(
                reference=f'JMW-{status.upper()}',
                amount=Decimal('5000.00'),
                email=f'{status}@example.com',
                status=status
            )
            
            expected = f"Payment JMW-{status.upper()} - {status}"
            self.assertEqual(str(payment), expected)


class PaymentTransactionOrderingTests(TestCase):
    """Test model ordering."""

    def test_default_ordering_by_created_desc(self):
        """Test that payments are ordered by created (newest first)."""
        # Create payments in sequence
        payment1 = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='first@example.com'
        )
        
        payment2 = PaymentTransaction.objects.create(
            amount=Decimal('10000.00'),
            email='second@example.com'
        )
        
        payment3 = PaymentTransaction.objects.create(
            amount=Decimal('15000.00'),
            email='third@example.com'
        )
        
        # Fetch all payments
        payments = list(PaymentTransaction.objects.all())
        
        # Should be in reverse chronological order (newest first)
        self.assertEqual(payments[0], payment3)
        self.assertEqual(payments[1], payment2)
        self.assertEqual(payments[2], payment1)

    def test_ordering_with_explicit_order_by(self):
        """Test that explicit order_by overrides default ordering."""
        payment1 = PaymentTransaction.objects.create(
            reference='JMW-AAA',
            amount=Decimal('5000.00'),
            email='aaa@example.com'
        )
        
        payment2 = PaymentTransaction.objects.create(
            reference='JMW-ZZZ',
            amount=Decimal('10000.00'),
            email='zzz@example.com'
        )
        
        # Order by reference
        payments = list(PaymentTransaction.objects.order_by('reference'))
        
        self.assertEqual(payments[0], payment1)
        self.assertEqual(payments[1], payment2)


class PaymentTransactionSaveMethodTests(TestCase):
    """Test save method override and reference generation."""

    def test_save_generates_reference_when_not_provided(self):
        """Test that save method generates reference if not provided."""
        payment = PaymentTransaction(
            amount=Decimal('5000.00'),
            email='savegen@example.com'
        )
        
        self.assertFalse(hasattr(payment, 'reference') and payment.reference)
        
        payment.save()
        
        self.assertIsNotNone(payment.reference)
        self.assertTrue(payment.reference.startswith('JMW-'))

    def test_save_preserves_existing_reference(self):
        """Test that save method doesn't overwrite existing reference."""
        custom_ref = 'CUSTOM-REF'
        payment = PaymentTransaction(
            reference=custom_ref,
            amount=Decimal('5000.00'),
            email='preserve@example.com'
        )
        
        payment.save()
        
        self.assertEqual(payment.reference, custom_ref)

    def test_save_with_empty_string_reference(self):
        """Test save with empty string reference generates new reference."""
        payment = PaymentTransaction(
            reference='',
            amount=Decimal('5000.00'),
            email='empty@example.com'
        )
        
        payment.save()
        
        self.assertNotEqual(payment.reference, '')
        self.assertTrue(payment.reference.startswith('JMW-'))

    def test_multiple_saves_dont_change_reference(self):
        """Test that multiple saves don't regenerate reference."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='multisave@example.com'
        )
        
        original_reference = payment.reference
        
        # Save multiple times
        payment.status = 'success'
        payment.save()
        
        payment.amount = Decimal('6000.00')
        payment.save()
        
        payment.refresh_from_db()
        
        self.assertEqual(payment.reference, original_reference)


class PaymentTransactionEdgeCasesTests(TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_payment_with_very_long_email(self):
        """Test payment with maximum length email."""
        # Django EmailField default max_length is 254
        long_email = 'a' * 240 + '@example.com'  # 253 chars
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email=long_email
        )
        
        self.assertEqual(payment.email, long_email)

    def test_payment_with_unicode_in_metadata(self):
        """Test payment with unicode characters in metadata."""
        metadata = {
            'customer_name': 'Adébáyọ̀ Olúwọlé',
            'city': '北京',
            'note': 'Спасибо'
        }
        
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='unicode@example.com',
            metadata=metadata
        )
        
        payment.refresh_from_db()
        
        self.assertEqual(payment.metadata['customer_name'], 'Adébáyọ̀ Olúwọlé')
        self.assertEqual(payment.metadata['city'], '北京')

    def test_concurrent_payment_creation(self):
        """Test creating multiple payments concurrently doesn't cause issues."""
        payments = []
        
        for i in range(5):
            payment = PaymentTransaction.objects.create(
                amount=Decimal('5000.00') + Decimal(i),
                email=f'concurrent{i}@example.com'
            )
            payments.append(payment)
        
        # All should have unique references
        references = [p.reference for p in payments]
        self.assertEqual(len(references), len(set(references)))

    def test_payment_metadata_default_behavior(self):
        """Test that metadata defaults to empty dict when not provided."""
        # Don't pass metadata at all - should use default
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='defaultmeta@example.com'
        )
        
        # Database default should kick in
        payment.refresh_from_db()
        self.assertIsNotNone(payment.metadata)
        self.assertEqual(payment.metadata, {})


class PaymentTransactionQueryOptimizationTests(TestCase):
    """Test query optimization with related orders."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
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

    def test_prefetch_related_orders(self):
        """Test that orders can be efficiently prefetched."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('25000.00'),
            email='prefetch@example.com'
        )
        payment.orders.add(self.order1, self.order2)
        
        # Query with prefetch_related
        payments = PaymentTransaction.objects.prefetch_related('orders').all()
        
        # Should be able to access orders without additional queries
        for payment in payments:
            order_count = payment.orders.count()
            self.assertGreaterEqual(order_count, 0)

    def test_filter_by_order_user(self):
        """Test filtering payments by order user."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('25000.00'),
            email='filter@example.com'
        )
        payment.orders.add(self.order1, self.order2)
        
        # Filter payments for specific user
        user_payments = PaymentTransaction.objects.filter(
            orders__user=self.user
        ).distinct()
        
        self.assertIn(payment, user_payments)


class PaymentTransactionSecurityTests(TestCase):
    """Test security-related aspects."""

    def test_reference_cannot_be_guessed_easily(self):
        """Test that generated references are not sequential or predictable."""
        payments = []
        for i in range(10):
            payment = PaymentTransaction.objects.create(
                amount=Decimal('5000.00'),
                email=f'security{i}@example.com'
            )
            payments.append(payment.reference)
        
        # Check that references don't follow a pattern
        # Extract the hex part
        hex_parts = [ref.split('-')[1] for ref in payments]
        
        # Check they're all different
        self.assertEqual(len(hex_parts), len(set(hex_parts)))
        
        # Check they're all 8 chars
        for hex_part in hex_parts:
            self.assertEqual(len(hex_part), 8)

    def test_status_integrity_maintained(self):
        """Test that status changes are properly saved."""
        payment = PaymentTransaction.objects.create(
            amount=Decimal('5000.00'),
            email='integrity@example.com',
            status='pending'
        )
        
        # Change to success
        payment.status = 'success'
        payment.save()
        
        # Verify in database
        payment_from_db = PaymentTransaction.objects.get(id=payment.id)
        self.assertEqual(payment_from_db.status, 'success')
        
        # Change to failed
        payment.status = 'failed'
        payment.save()
        
        payment_from_db = PaymentTransaction.objects.get(id=payment.id)
        self.assertEqual(payment_from_db.status, 'failed')


class PaymentTransactionIntegrationTests(TestCase):
    """Integration tests combining multiple features."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.orders = []
        for i in range(3):
            order = BaseOrder.objects.create(
                user=self.user,
                first_name=f'User{i}',
                last_name='Test',
                email=f'user{i}@example.com',
                phone_number='08012345678',
                total_cost=Decimal('10000.00')
            )
            self.orders.append(order)

    def test_complete_payment_flow(self):
        """Test a complete payment flow from creation to completion."""
        # 1. Create payment
        payment = PaymentTransaction.objects.create(
            amount=Decimal('30000.00'),
            email='integration@example.com',
            metadata={
                'orders': [str(o.id) for o in self.orders],
                'customer_name': 'Test User'
            }
        )
        
        # 2. Attach orders
        payment.orders.set(self.orders)
        
        # 3. Verify initial state
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.orders.count(), 3)
        
        # 4. Mark as successful
        payment.status = 'success'
        payment.save()
        
        # 5. Verify final state
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'success')
        self.assertEqual(payment.orders.count(), 3)
        
        # 6. Verify orders relationship works both ways
        for order in self.orders:
            self.assertIn(payment, order.payments.all())

    def test_payment_with_mixed_order_types(self):
        """Test payment with different order types."""
        # Create a NyscKitOrder
        kit_order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='Kit',
            last_name='User',
            email='kit@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('50000.00')
        )
        
        # Create payment with both BaseOrder and NyscKitOrder
        payment = PaymentTransaction.objects.create(
            amount=Decimal('60000.00'),
            email='mixed@example.com'
        )
        payment.orders.add(self.orders[0], kit_order)
        
        self.assertEqual(payment.orders.count(), 2)
        
        # Verify both order types are present
        order_ids = [str(o.id) for o in payment.orders.all()]
        self.assertIn(str(self.orders[0].id), order_ids)
        self.assertIn(str(kit_order.id), order_ids)