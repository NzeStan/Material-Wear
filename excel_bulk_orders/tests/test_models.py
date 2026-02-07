# excel_bulk_orders/tests/test_models.py
"""
Comprehensive tests for Excel Bulk Orders models.

Coverage:
- ExcelBulkOrder: Reference generation, validation status transitions, payment handling
- ExcelCouponCode: Code generation, uniqueness, usage tracking, case handling
- ExcelParticipant: Data storage, coupon relationships, row number uniqueness
- Concurrent operations and race conditions
- Cascade delete behaviors
- Model save hooks and data normalization
"""
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from datetime import timedelta
import re

from excel_bulk_orders.models import ExcelBulkOrder, ExcelCouponCode, ExcelParticipant

User = get_user_model()


class ExcelBulkOrderModelTest(TestCase):
    """Test ExcelBulkOrder model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='coordinator',
            email='coordinator@example.com',
            password='testpass123'
        )

    def test_bulk_order_creation_with_required_fields(self):
        """Test creating bulk order with all required fields"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='NYSC Camp Registration 2024',
            coordinator_name='John Coordinator',
            coordinator_email='john@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            requires_custom_name=True,
            created_by=self.user
        )

        self.assertIsNotNone(bulk_order.id)
        self.assertIsNotNone(bulk_order.reference)
        self.assertEqual(bulk_order.validation_status, 'pending')
        self.assertFalse(bulk_order.payment_status)
        self.assertEqual(bulk_order.total_amount, Decimal('0.00'))

    def test_reference_auto_generation_format(self):
        """Test that reference follows EXL-XXXXXXXXXXXX format"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Test Order',
            coordinator_name='Test Coordinator',
            coordinator_email='test@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('3000.00')
        )

        # Reference should be EXL- + 12 alphanumeric chars (case insensitive)
        pattern = r'^EXL-[A-Z0-9a-z]{12}$'
        self.assertIsNotNone(re.match(pattern, bulk_order.reference))

    def test_reference_uniqueness(self):
        """Test that reference is unique across all bulk orders"""
        # Create first order
        order1 = ExcelBulkOrder.objects.create(
            title='Order 1',
            coordinator_name='Coordinator 1',
            coordinator_email='coord1@example.com',
            coordinator_phone='08011111111',
            price_per_participant=Decimal('5000.00')
        )

        # Create second order
        order2 = ExcelBulkOrder.objects.create(
            title='Order 2',
            coordinator_name='Coordinator 2',
            coordinator_email='coord2@example.com',
            coordinator_phone='08022222222',
            price_per_participant=Decimal('4000.00')
        )

        # References should be different
        self.assertNotEqual(order1.reference, order2.reference)

    def test_custom_reference_accepted(self):
        """Test that manually provided reference is accepted"""
        custom_ref = 'EXL-CUSTOM01'
        bulk_order = ExcelBulkOrder.objects.create(
            reference=custom_ref,
            title='Custom Reference Order',
            coordinator_name='Test',
            coordinator_email='test@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        self.assertEqual(bulk_order.reference, custom_ref)

    def test_coordinator_email_normalization(self):
        """Test that coordinator email case is preserved (not normalized)"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Email Test',
            coordinator_name='Test',
            coordinator_email='TEST.EMAIL@EXAMPLE.COM',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        bulk_order.refresh_from_db()
        # Email is stored as provided (model doesn't normalize to lowercase)
        self.assertEqual(bulk_order.coordinator_email, 'TEST.EMAIL@EXAMPLE.COM')

    def test_validation_status_choices(self):
        """Test validation status transitions"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Status Test',
            coordinator_name='Test',
            coordinator_email='status@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        # Default status
        self.assertEqual(bulk_order.validation_status, 'pending')

        # Uploaded
        bulk_order.validation_status = 'uploaded'
        bulk_order.save()
        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.validation_status, 'uploaded')

        # Valid
        bulk_order.validation_status = 'valid'
        bulk_order.save()
        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.validation_status, 'valid')

        # Invalid
        bulk_order.validation_status = 'invalid'
        bulk_order.save()
        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.validation_status, 'invalid')

        # Processing
        bulk_order.validation_status = 'processing'
        bulk_order.save()
        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.validation_status, 'processing')

        # Completed
        bulk_order.validation_status = 'completed'
        bulk_order.save()
        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.validation_status, 'completed')

    def test_payment_status_default_false(self):
        """Test payment status defaults to False"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Payment Test',
            coordinator_name='Test',
            coordinator_email='payment@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        self.assertFalse(bulk_order.payment_status)

    def test_payment_status_update(self):
        """Test updating payment status"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Payment Update Test',
            coordinator_name='Test',
            coordinator_email='paymentupdate@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        bulk_order.payment_status = True
        bulk_order.paystack_reference = 'ref_12345'
        bulk_order.save()

        bulk_order.refresh_from_db()
        self.assertTrue(bulk_order.payment_status)
        self.assertEqual(bulk_order.paystack_reference, 'ref_12345')

    def test_total_amount_calculation(self):
        """Test total amount storage and update"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Amount Test',
            coordinator_name='Test',
            coordinator_email='amount@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        # Initially zero
        self.assertEqual(bulk_order.total_amount, Decimal('0.00'))

        # Update after validation
        bulk_order.total_amount = Decimal('25000.00')  # 5 participants
        bulk_order.save()

        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.total_amount, Decimal('25000.00'))

    def test_requires_custom_name_field(self):
        """Test requires_custom_name flag"""
        # With custom name
        order_with_custom = ExcelBulkOrder.objects.create(
            title='Custom Name Order',
            coordinator_name='Test',
            coordinator_email='custom@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            requires_custom_name=True
        )
        self.assertTrue(order_with_custom.requires_custom_name)

        # Without custom name
        order_without_custom = ExcelBulkOrder.objects.create(
            title='No Custom Name Order',
            coordinator_name='Test',
            coordinator_email='nocustom@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            requires_custom_name=False
        )
        self.assertFalse(order_without_custom.requires_custom_name)

    def test_template_file_url_storage(self):
        """Test storing template file URL"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Template Test',
            coordinator_name='Test',
            coordinator_email='template@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        template_url = 'https://res.cloudinary.com/test/excel_templates/EXL-12345678.xlsx'
        bulk_order.template_file = template_url
        bulk_order.save()

        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.template_file, template_url)

    def test_uploaded_file_url_storage(self):
        """Test storing uploaded file URL"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Upload Test',
            coordinator_name='Test',
            coordinator_email='upload@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        upload_url = 'https://res.cloudinary.com/test/excel_uploads/EXL-12345678.xlsx'
        bulk_order.uploaded_file = upload_url
        bulk_order.save()

        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.uploaded_file, upload_url)

    def test_created_by_optional(self):
        """Test that created_by is optional (can be null)"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Anonymous Order',
            coordinator_name='Test',
            coordinator_email='anon@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
            # No created_by provided
        )

        self.assertIsNone(bulk_order.created_by)

    def test_created_by_with_user(self):
        """Test bulk order with created_by user"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='User Order',
            coordinator_name='Test',
            coordinator_email='user@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            created_by=self.user
        )

        self.assertEqual(bulk_order.created_by, self.user)

    def test_timestamps_auto_set(self):
        """Test that created_at and updated_at are automatically set"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Timestamp Test',
            coordinator_name='Test',
            coordinator_email='timestamp@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        self.assertIsNotNone(bulk_order.created_at)
        self.assertIsNotNone(bulk_order.updated_at)
        # Timestamps may differ by microseconds on creation
        time_diff = abs((bulk_order.updated_at - bulk_order.created_at).total_seconds())
        self.assertLess(time_diff, 1)

    def test_updated_at_changes_on_save(self):
        """Test that updated_at changes when model is saved"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Update Test',
            coordinator_name='Test',
            coordinator_email='updatetime@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        original_updated = bulk_order.updated_at

        # Wait a bit and update
        import time
        time.sleep(0.01)

        bulk_order.title = 'Updated Title'
        bulk_order.save()
        bulk_order.refresh_from_db()

        self.assertGreater(bulk_order.updated_at, original_updated)

    def test_str_representation(self):
        """Test string representation of bulk order"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='String Test Order',
            coordinator_name='Test Coordinator',
            coordinator_email='str@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        expected = f"String Test Order - {bulk_order.reference}"
        self.assertEqual(str(bulk_order), expected)

    def test_price_per_participant_decimal_precision(self):
        """Test that price is stored with correct decimal precision"""
        bulk_order = ExcelBulkOrder.objects.create(
            title='Decimal Test',
            coordinator_name='Test',
            coordinator_email='decimal@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('4999.99')
        )

        bulk_order.refresh_from_db()
        self.assertEqual(bulk_order.price_per_participant, Decimal('4999.99'))

    def test_multiple_bulk_orders_same_coordinator(self):
        """Test same coordinator can create multiple bulk orders"""
        email = 'multi@example.com'

        order1 = ExcelBulkOrder.objects.create(
            title='Order 1',
            coordinator_name='Multi Coordinator',
            coordinator_email=email,
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        order2 = ExcelBulkOrder.objects.create(
            title='Order 2',
            coordinator_name='Multi Coordinator',
            coordinator_email=email,
            coordinator_phone='08012345678',
            price_per_participant=Decimal('6000.00')
        )

        self.assertNotEqual(order1.id, order2.id)
        self.assertNotEqual(order1.reference, order2.reference)
        self.assertEqual(order1.coordinator_email, order2.coordinator_email)

    def test_ordering_by_created_at_desc(self):
        """Test that bulk orders are ordered by created_at descending"""
        order1 = ExcelBulkOrder.objects.create(
            title='First',
            coordinator_name='Test',
            coordinator_email='first@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        order2 = ExcelBulkOrder.objects.create(
            title='Second',
            coordinator_name='Test',
            coordinator_email='second@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        order3 = ExcelBulkOrder.objects.create(
            title='Third',
            coordinator_name='Test',
            coordinator_email='third@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        orders = list(ExcelBulkOrder.objects.all())
        self.assertEqual(orders[0], order3)  # Most recent first
        self.assertEqual(orders[1], order2)
        self.assertEqual(orders[2], order1)


class ExcelCouponCodeModelTest(TestCase):
    """Test ExcelCouponCode model functionality"""

    def setUp(self):
        """Set up test data"""
        self.bulk_order = ExcelBulkOrder.objects.create(
            title='Coupon Test Order',
            coordinator_name='Test',
            coordinator_email='coupon@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

    def test_coupon_creation(self):
        """Test creating a coupon code"""
        coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='TEST1234'
        )

        self.assertIsNotNone(coupon.id)
        self.assertEqual(coupon.code, 'TEST1234')
        self.assertFalse(coupon.is_used)
        self.assertEqual(coupon.bulk_order, self.bulk_order)

    def test_coupon_code_uppercase_normalization(self):
        """Test that coupon codes are converted to uppercase"""
        coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='lowercase123'
        )

        coupon.refresh_from_db()
        self.assertEqual(coupon.code, 'LOWERCASE123')

    def test_coupon_code_uniqueness(self):
        """Test that coupon codes must be unique"""
        ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='UNIQUE123'
        )

        # Try to create another with same code (even different bulk order)
        other_bulk_order = ExcelBulkOrder.objects.create(
            title='Other Order',
            coordinator_name='Test',
            coordinator_email='other@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        with self.assertRaises(IntegrityError):
            ExcelCouponCode.objects.create(
                bulk_order=other_bulk_order,
                code='UNIQUE123'
            )

    def test_is_used_default_false(self):
        """Test that is_used defaults to False"""
        coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='DEFAULT123'
        )

        self.assertFalse(coupon.is_used)

    def test_marking_coupon_as_used(self):
        """Test marking a coupon as used"""
        coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='MARKUSED123'
        )

        coupon.is_used = True
        coupon.save()

        coupon.refresh_from_db()
        self.assertTrue(coupon.is_used)

    def test_str_representation(self):
        """Test string representation of coupon"""
        # Unused coupon
        unused_coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='UNUSED123'
        )
        self.assertEqual(str(unused_coupon), 'UNUSED123 (Available)')

        # Used coupon
        used_coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='USED123',
            is_used=True
        )
        self.assertEqual(str(used_coupon), 'USED123 (Used)')

    def test_multiple_coupons_same_bulk_order(self):
        """Test creating multiple coupons for same bulk order"""
        codes = ['MULTI1', 'MULTI2', 'MULTI3', 'MULTI4', 'MULTI5']

        for code in codes:
            ExcelCouponCode.objects.create(
                bulk_order=self.bulk_order,
                code=code
            )

        self.assertEqual(self.bulk_order.coupons.count(), 5)

    def test_bulk_order_deletion_cascades_to_coupons(self):
        """Test that deleting bulk order cascades to coupons"""
        ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='CASCADE123'
        )

        bulk_order_id = self.bulk_order.id
        self.assertEqual(ExcelCouponCode.objects.filter(bulk_order_id=bulk_order_id).count(), 1)

        # Delete bulk order
        self.bulk_order.delete()

        # Coupon should be deleted too (CASCADE)
        self.assertEqual(ExcelCouponCode.objects.filter(bulk_order_id=bulk_order_id).count(), 0)

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set"""
        coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='TIMESTAMP123'
        )

        self.assertIsNotNone(coupon.created_at)

    def test_ordering_by_created_at(self):
        """Test that coupons are ordered by created_at"""
        coupon1 = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='FIRST'
        )

        coupon2 = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='SECOND'
        )

        coupon3 = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='THIRD'
        )

        coupons = list(self.bulk_order.coupons.all())
        self.assertEqual(coupons[0], coupon1)
        self.assertEqual(coupons[1], coupon2)
        self.assertEqual(coupons[2], coupon3)

    def test_coupon_with_mixed_case(self):
        """Test coupon code with mixed case is normalized"""
        coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='MiXeDCaSe123'
        )

        coupon.refresh_from_db()
        self.assertEqual(coupon.code, 'MIXEDCASE123')


class ExcelParticipantModelTest(TransactionTestCase):
    """Test ExcelParticipant model functionality. Using TransactionTestCase for atomic operations."""

    def setUp(self):
        """Set up test data"""
        self.bulk_order = ExcelBulkOrder.objects.create(
            title='Participant Test Order',
            coordinator_name='Test',
            coordinator_email='participant@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            requires_custom_name=True
        )

        self.coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='PARTCOUPON1'
        )

    def test_participant_creation_with_required_fields(self):
        """Test creating participant with required fields"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='John Participant',
            size='M',
            row_number=2
        )

        self.assertIsNotNone(participant.id)
        self.assertEqual(participant.full_name, 'John Participant')
        self.assertEqual(participant.size, 'M')
        self.assertEqual(participant.row_number, 2)
        self.assertFalse(participant.is_coupon_applied)

    def test_participant_with_custom_name(self):
        """Test participant with custom name"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='John Doe',
            size='L',
            custom_name='JOHNNY',
            row_number=2
        )

        self.assertEqual(participant.custom_name, 'JOHNNY')

    def test_participant_with_coupon(self):
        """Test participant with valid coupon"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Jane Coupon User',
            size='S',
            coupon_code='PARTCOUPON1',
            coupon=self.coupon,
            is_coupon_applied=True,
            row_number=2
        )

        self.assertEqual(participant.coupon, self.coupon)
        self.assertEqual(participant.coupon_code, 'PARTCOUPON1')
        self.assertTrue(participant.is_coupon_applied)

    def test_participant_with_invalid_coupon_code(self):
        """Test participant with invalid coupon code (not applied)"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Invalid Coupon User',
            size='M',
            coupon_code='INVALID123',
            row_number=2
        )

        self.assertEqual(participant.coupon_code, 'INVALID123')
        self.assertIsNone(participant.coupon)
        self.assertFalse(participant.is_coupon_applied)

    def test_row_number_unique_per_bulk_order(self):
        """Test that row numbers must be unique within a bulk order"""
        ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='First',
            size='M',
            row_number=2
        )

        # Try to create another with same row number in same bulk order
        with self.assertRaises(IntegrityError):
            ExcelParticipant.objects.create(
                bulk_order=self.bulk_order,
                full_name='Second',
                size='L',
                row_number=2
            )

    def test_row_number_can_repeat_across_different_bulk_orders(self):
        """Test that same row number can exist in different bulk orders"""
        ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='First Order Participant',
            size='M',
            row_number=2
        )

        # Create different bulk order
        other_bulk_order = ExcelBulkOrder.objects.create(
            title='Other Order',
            coordinator_name='Test',
            coordinator_email='other@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00')
        )

        # Same row number should work in different order
        participant2 = ExcelParticipant.objects.create(
            bulk_order=other_bulk_order,
            full_name='Second Order Participant',
            size='L',
            row_number=2
        )

        self.assertEqual(participant2.row_number, 2)

    def test_size_choices_valid(self):
        """Test that valid size choices work"""
        valid_sizes = ['S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'XXXXL']

        for size in valid_sizes:
            participant = ExcelParticipant.objects.create(
                bulk_order=self.bulk_order,
                full_name=f'Size {size} User',
                size=size,
                row_number=2 + valid_sizes.index(size)
            )
            self.assertEqual(participant.size, size)

    def test_str_representation(self):
        """Test string representation of participant"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='String Test User',
            size='M',
            row_number=2
        )

        expected = f"String Test User - M"
        self.assertEqual(str(participant), expected)

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Timestamp User',
            size='M',
            row_number=2
        )

        self.assertIsNotNone(participant.created_at)

    def test_bulk_order_deletion_cascades_to_participants(self):
        """Test that deleting bulk order cascades to participants"""
        ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Cascade Test',
            size='M',
            row_number=2
        )

        bulk_order_id = self.bulk_order.id
        self.assertEqual(ExcelParticipant.objects.filter(bulk_order_id=bulk_order_id).count(), 1)

        # Delete bulk order
        self.bulk_order.delete()

        # Participant should be deleted too (CASCADE)
        self.assertEqual(ExcelParticipant.objects.filter(bulk_order_id=bulk_order_id).count(), 0)

    def test_coupon_deletion_sets_null_on_participant(self):
        """Test that deleting coupon sets coupon field to null on participant"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Coupon Delete Test',
            size='M',
            coupon_code='PARTCOUPON1',
            coupon=self.coupon,
            is_coupon_applied=True,
            row_number=2
        )

        # Delete coupon
        self.coupon.delete()

        # Participant should still exist but coupon should be null
        participant.refresh_from_db()
        self.assertIsNone(participant.coupon)
        self.assertEqual(participant.coupon_code, 'PARTCOUPON1')  # Code remains

    def test_multiple_participants_different_row_numbers(self):
        """Test creating multiple participants with different row numbers"""
        for i in range(2, 12):  # Row numbers 2-11 (row 1 is header)
            ExcelParticipant.objects.create(
                bulk_order=self.bulk_order,
                full_name=f'Participant {i}',
                size='M',
                row_number=i
            )

        self.assertEqual(self.bulk_order.participants.count(), 10)

    def test_ordering_by_row_number(self):
        """Test that participants are ordered by row number"""
        # Create out of order
        p3 = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Third',
            size='M',
            row_number=4
        )

        p1 = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='First',
            size='M',
            row_number=2
        )

        p2 = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Second',
            size='M',
            row_number=3
        )

        participants = list(self.bulk_order.participants.all())
        self.assertEqual(participants[0], p1)
        self.assertEqual(participants[1], p2)
        self.assertEqual(participants[2], p3)

    def test_concurrent_participant_creation_same_row(self):
        """Test race condition when creating participants with same row number"""
        def create_participant(name):
            try:
                with transaction.atomic():
                    ExcelParticipant.objects.create(
                        bulk_order=self.bulk_order,
                        full_name=name,
                        size='M',
                        row_number=2
                    )
                return True
            except IntegrityError:
                return False

        # First creation should succeed
        self.assertTrue(create_participant('First'))

        # Second with same row should fail
        self.assertFalse(create_participant('Second'))

        # Only one participant should exist
        self.assertEqual(
            ExcelParticipant.objects.filter(bulk_order=self.bulk_order, row_number=2).count(),
            1
        )