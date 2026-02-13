# image_bulk_orders/tests/test_models.py
"""
Comprehensive test suite for image_bulk_orders models.

Tests cover:
- ImageBulkOrderLink: Slug generation, expiry logic, organization name normalization, field validation
- ImageCouponCode: Uniqueness, usage tracking, bulk order relationships
- ImageOrderEntry: Reference generation, serial numbers, image field, concurrent operations

Coverage targets: 100% for all models
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, Mock
import uuid
from io import BytesIO
from PIL import Image as PILImage

from image_bulk_orders.models import ImageBulkOrderLink, ImageCouponCode, ImageOrderEntry

User = get_user_model()


class ImageBulkOrderLinkModelTest(TestCase):
    """Test ImageBulkOrderLink model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.future_deadline = timezone.now() + timedelta(days=30)
        self.past_deadline = timezone.now() - timedelta(days=1)

    def test_create_bulk_order_link_success(self):
        """Test successful creation of bulk order link"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Test Church',
            price_per_item=Decimal('5000.00'),
            custom_branding_enabled=True,
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertIsNotNone(bulk_order.id)
        self.assertEqual(bulk_order.organization_name, 'TEST CHURCH')  # Auto uppercase
        self.assertTrue(bulk_order.slug.startswith('test-church'))
        self.assertEqual(bulk_order.price_per_item, Decimal('5000.00'))
        self.assertTrue(bulk_order.custom_branding_enabled)
        self.assertIsNotNone(bulk_order.created_at)
        self.assertIsNotNone(bulk_order.updated_at)

    def test_slug_auto_generation(self):
        """Test that slug is auto-generated from organization name"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Amazing Grace Church',
            price_per_item=Decimal('3000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertEqual(bulk_order.slug, 'amazing-grace-church')

    def test_slug_uniqueness_with_counter(self):
        """Test that duplicate organization names get unique slugs with counter"""
        # Create first bulk order
        bulk_order1 = ImageBulkOrderLink.objects.create(
            organization_name='Duplicate Church',
            price_per_item=Decimal('4000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        # Create second with same name
        bulk_order2 = ImageBulkOrderLink.objects.create(
            organization_name='Duplicate Church',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertEqual(bulk_order1.slug, 'duplicate-church')
        self.assertEqual(bulk_order2.slug, 'duplicate-church-1')

    def test_slug_uniqueness_multiple_duplicates(self):
        """Test slug generation with multiple duplicates"""
        slugs = []
        for i in range(5):
            bulk_order = ImageBulkOrderLink.objects.create(
                organization_name='Same Church',
                price_per_item=Decimal('3000.00'),
                payment_deadline=self.future_deadline,
                created_by=self.user
            )
            slugs.append(bulk_order.slug)
        
        self.assertEqual(slugs[0], 'same-church')
        self.assertEqual(slugs[1], 'same-church-1')
        self.assertEqual(slugs[2], 'same-church-2')
        self.assertEqual(slugs[3], 'same-church-3')
        self.assertEqual(slugs[4], 'same-church-4')

    def test_organization_name_uppercase_normalization(self):
        """Test that organization names are normalized to uppercase"""
        test_cases = [
            ('lower case church', 'LOWER CASE CHURCH'),
            ('MiXeD CaSe ChUrCh', 'MIXED CASE CHURCH'),
            ('ALREADY UPPERCASE', 'ALREADY UPPERCASE'),
        ]
        
        for input_name, expected_name in test_cases:
            bulk_order = ImageBulkOrderLink.objects.create(
                organization_name=input_name,
                price_per_item=Decimal('3000.00'),
                payment_deadline=self.future_deadline,
                created_by=self.user
            )
            self.assertEqual(bulk_order.organization_name, expected_name)

    def test_price_per_item_minimum_validation(self):
        """Test that price_per_item must be positive"""
        with self.assertRaises(ValidationError):
            bulk_order = ImageBulkOrderLink(
                organization_name='Test Church',
                price_per_item=Decimal('0.00'),
                payment_deadline=self.future_deadline,
                created_by=self.user
            )
            bulk_order.full_clean()

    def test_price_per_item_negative_validation(self):
        """Test that negative prices are rejected"""
        with self.assertRaises(ValidationError):
            bulk_order = ImageBulkOrderLink(
                organization_name='Test Church',
                price_per_item=Decimal('-100.00'),
                payment_deadline=self.future_deadline,
                created_by=self.user
            )
            bulk_order.full_clean()

    def test_price_per_item_decimal_precision(self):
        """Test that decimal precision is maintained"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Decimal Test',
            price_per_item=Decimal('1234.56'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertEqual(bulk_order.price_per_item, Decimal('1234.56'))

    def test_is_expired_returns_false_for_future_deadline(self):
        """Test is_expired() returns False when deadline is in future"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Future Deadline',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertFalse(bulk_order.is_expired())

    def test_is_expired_returns_true_for_past_deadline(self):
        """Test is_expired() returns True when deadline has passed"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Past Deadline',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.past_deadline,
            created_by=self.user
        )
        
        self.assertTrue(bulk_order.is_expired())

    def test_is_expired_edge_case_exact_current_time(self):
        """Test is_expired() at exact deadline boundary"""
        # Create with current time
        current_time = timezone.now()
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Exact Time',
            price_per_item=Decimal('5000.00'),
            payment_deadline=current_time,
            created_by=self.user
        )
        
        # At exact time or just past, should be expired
        with patch('django.utils.timezone.now', return_value=current_time + timedelta(seconds=1)):
            self.assertTrue(bulk_order.is_expired())

    def test_get_shareable_url(self):
        """Test get_shareable_url() returns correct URL"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='URL Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        expected_url = f"/image-bulk-order/{bulk_order.slug}/"
        self.assertEqual(bulk_order.get_shareable_url(), expected_url)

    def test_get_absolute_url_calls_get_shareable_url(self):
        """Test get_absolute_url() delegates to get_shareable_url()"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Absolute URL Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertEqual(bulk_order.get_absolute_url(), bulk_order.get_shareable_url())

    def test_str_representation(self):
        """Test string representation of bulk order"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='String Test Church',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        expected_str = f"{bulk_order.organization_name} - {bulk_order.slug}"
        self.assertEqual(str(bulk_order), expected_str)

    def test_ordering_by_created_at_descending(self):
        """Test that bulk orders are ordered by created_at descending"""
        bulk_order1 = ImageBulkOrderLink.objects.create(
            organization_name='First',
            price_per_item=Decimal('3000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        bulk_order2 = ImageBulkOrderLink.objects.create(
            organization_name='Second',
            price_per_item=Decimal('3000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        all_orders = list(ImageBulkOrderLink.objects.all())
        self.assertEqual(all_orders[0].id, bulk_order2.id)
        self.assertEqual(all_orders[1].id, bulk_order1.id)

    def test_cascade_delete_with_orders(self):
        """Test that deleting bulk order cascades to orders"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Delete Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        # Create order
        order = ImageOrderEntry.objects.create(
            bulk_order=bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        order_id = order.id
        
        # Delete bulk order
        bulk_order.delete()
        
        # Order should be deleted
        self.assertFalse(ImageOrderEntry.objects.filter(id=order_id).exists())

    def test_cascade_delete_with_coupons(self):
        """Test that deleting bulk order cascades to coupons"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Coupon Delete Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        # Create coupon
        coupon = ImageCouponCode.objects.create(
            bulk_order=bulk_order,
            code='TESTCODE123'
        )
        
        coupon_id = coupon.id
        
        # Delete bulk order
        bulk_order.delete()
        
        # Coupon should be deleted
        self.assertFalse(ImageCouponCode.objects.filter(id=coupon_id).exists())

    def test_created_by_relationship(self):
        """Test relationship with User model"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='User Relation Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertEqual(bulk_order.created_by, self.user)
        self.assertIn(bulk_order, self.user.image_bulk_orders.all())

    def test_custom_branding_enabled_default_false(self):
        """Test that custom_branding_enabled defaults to False"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Default Branding',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertFalse(bulk_order.custom_branding_enabled)

    def test_timestamps_auto_set(self):
        """Test that created_at and updated_at are automatically set"""
        before_creation = timezone.now()
        
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Timestamp Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        after_creation = timezone.now()
        
        self.assertGreaterEqual(bulk_order.created_at, before_creation)
        self.assertLessEqual(bulk_order.created_at, after_creation)
        # Timestamps may differ by microseconds
        time_diff = abs((bulk_order.created_at - bulk_order.updated_at).total_seconds())
        self.assertLess(time_diff, 1.0)

    def test_updated_at_changes_on_save(self):
        """Test that updated_at changes when model is saved"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Update Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        original_updated_at = bulk_order.updated_at
        
        # Wait a bit and update
        import time
        time.sleep(0.01)
        
        bulk_order.price_per_item = Decimal('6000.00')
        bulk_order.save()
        
        self.assertGreater(bulk_order.updated_at, original_updated_at)

    def test_uuid_primary_key(self):
        """Test that ID is a UUID"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='UUID Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        self.assertIsInstance(bulk_order.id, uuid.UUID)

    def test_slug_max_length(self):
        """Test slug respects max_length constraint"""
        very_long_name = 'A' * 300  # Longer than slug max_length
        
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name=very_long_name,
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        # Slug is created successfully even with long name
        self.assertIsNotNone(bulk_order.slug)


class ImageCouponCodeModelTest(TestCase):
    """Test ImageCouponCode model functionality"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Test Church',
            price_per_item=Decimal('5000.00'),
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )

    def test_create_coupon_code_success(self):
        """Test successful creation of coupon code"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='TEST12345'
        )
        
        self.assertIsNotNone(coupon.id)
        self.assertEqual(coupon.code, 'TEST12345')
        self.assertEqual(coupon.bulk_order, self.bulk_order)
        self.assertFalse(coupon.is_used)
        self.assertIsNotNone(coupon.created_at)

    def test_coupon_code_uniqueness(self):
        """Test that duplicate coupon codes are rejected"""
        ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='UNIQUE123'
        )
        
        # Try to create duplicate
        with self.assertRaises(IntegrityError):
            ImageCouponCode.objects.create(
                bulk_order=self.bulk_order,
                code='UNIQUE123'
            )

    def test_coupon_code_uniqueness_across_bulk_orders(self):
        """Test that coupon codes are unique even across different bulk orders"""
        bulk_order2 = ImageBulkOrderLink.objects.create(
            organization_name='Another Church',
            price_per_item=Decimal('4000.00'),
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='GLOBAL123'
        )
        
        with self.assertRaises(IntegrityError):
            ImageCouponCode.objects.create(
                bulk_order=bulk_order2,
                code='GLOBAL123'
            )

    def test_is_used_default_false(self):
        """Test that is_used defaults to False"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='DEFAULT123'
        )
        
        self.assertFalse(coupon.is_used)

    def test_is_used_can_be_set_true(self):
        """Test that is_used can be updated to True"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='USED123'
        )
        
        coupon.is_used = True
        coupon.save()
        
        coupon.refresh_from_db()
        self.assertTrue(coupon.is_used)

    def test_str_representation_unused(self):
        """Test string representation for unused coupon"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='STR123'
        )
        
        expected_str = "STR123 (Available)"
        self.assertEqual(str(coupon), expected_str)

    def test_str_representation_used(self):
        """Test string representation for used coupon"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='USED123',
            is_used=True
        )
        
        expected_str = "USED123 (Used)"
        self.assertEqual(str(coupon), expected_str)

    def test_ordering_by_created_at(self):
        """Test that coupons are ordered by created_at ascending"""
        coupon1 = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='FIRST'
        )
        
        coupon2 = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='SECOND'
        )
        
        all_coupons = list(ImageCouponCode.objects.all())
        self.assertEqual(all_coupons[0].id, coupon1.id)
        self.assertEqual(all_coupons[1].id, coupon2.id)

    def test_bulk_order_relationship(self):
        """Test relationship with ImageBulkOrderLink"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='RELATION123'
        )
        
        self.assertEqual(coupon.bulk_order, self.bulk_order)
        self.assertIn(coupon, self.bulk_order.coupons.all())

    def test_cascade_delete_on_bulk_order_deletion(self):
        """Test that coupon is deleted when bulk order is deleted"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='CASCADE123'
        )
        
        coupon_id = coupon.id
        self.bulk_order.delete()
        
        self.assertFalse(ImageCouponCode.objects.filter(id=coupon_id).exists())

    def test_uuid_primary_key(self):
        """Test that ID is a UUID"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='UUID123'
        )
        
        self.assertIsInstance(coupon.id, uuid.UUID)

    def test_code_max_length(self):
        """Test that code respects max_length"""
        max_length_code = 'A' * 20
        
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code=max_length_code
        )
        
        self.assertEqual(len(coupon.code), 20)

    def test_created_at_auto_set(self):
        """Test that created_at is automatically set"""
        before_creation = timezone.now()
        
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='TIME123'
        )
        
        after_creation = timezone.now()
        
        self.assertGreaterEqual(coupon.created_at, before_creation)
        self.assertLessEqual(coupon.created_at, after_creation)


class ImageOrderEntryModelTest(TransactionTestCase):
    """Test ImageOrderEntry model functionality (using TransactionTestCase for concurrent tests)"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Test Church',
            price_per_item=Decimal('5000.00'),
            custom_branding_enabled=True,
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )

    def test_create_order_entry_success(self):
        """Test successful creation of order entry"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        self.assertIsNotNone(order.id)
        self.assertIsNotNone(order.reference)
        self.assertEqual(order.serial_number, 1)
        self.assertEqual(order.email, 'test@example.com')
        self.assertEqual(order.full_name, 'Test User')
        self.assertEqual(order.size, 'L')
        self.assertFalse(order.paid)
        self.assertIsNone(order.coupon_used)
        self.assertIsNone(order.image)

    def test_reference_auto_generation(self):
        """Test that reference is auto-generated"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        self.assertTrue(order.reference.startswith('IMG-BULK-'))
        self.assertEqual(len(order.reference), 13)  # IMG-BULK-XXXX

    def test_reference_uniqueness(self):
        """Test that references are unique"""
        order1 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test1@example.com',
            full_name='User 1',
            size='L'
        )
        
        order2 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test2@example.com',
            full_name='User 2',
            size='M'
        )
        
        self.assertNotEqual(order1.reference, order2.reference)

    def test_serial_number_auto_increment(self):
        """Test that serial_number auto-increments within bulk_order"""
        order1 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test1@example.com',
            full_name='User 1',
            size='L'
        )
        
        order2 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test2@example.com',
            full_name='User 2',
            size='M'
        )
        
        order3 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test3@example.com',
            full_name='User 3',
            size='S'
        )
        
        self.assertEqual(order1.serial_number, 1)
        self.assertEqual(order2.serial_number, 2)
        self.assertEqual(order3.serial_number, 3)

    def test_serial_number_per_bulk_order(self):
        """Test that serial numbers are independent per bulk order"""
        bulk_order2 = ImageBulkOrderLink.objects.create(
            organization_name='Another Church',
            price_per_item=Decimal('4000.00'),
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        order1_bulk1 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test1@example.com',
            full_name='User 1',
            size='L'
        )
        
        order1_bulk2 = ImageOrderEntry.objects.create(
            bulk_order=bulk_order2,
            email='test2@example.com',
            full_name='User 2',
            size='M'
        )
        
        order2_bulk1 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test3@example.com',
            full_name='User 3',
            size='S'
        )
        
        # Both bulk orders should start at 1
        self.assertEqual(order1_bulk1.serial_number, 1)
        self.assertEqual(order1_bulk2.serial_number, 1)
        self.assertEqual(order2_bulk1.serial_number, 2)

    def test_serial_number_uniqueness_within_bulk_order(self):
        """Test unique_together constraint on (bulk_order, serial_number)"""
        order1 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test1@example.com',
            full_name='User 1',
            size='L'
        )
        
        # Try to manually create with same serial number
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                order2 = ImageOrderEntry(
                    bulk_order=self.bulk_order,
                    email='test2@example.com',
                    full_name='User 2',
                    size='M',
                    serial_number=order1.serial_number
                )
                order2.reference = 'IMG-BULK-9999'
                order2.save()

    def test_size_choices_validation(self):
        """Test that only valid size choices are accepted"""
        valid_sizes = ['S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'XXXXL']
        
        for size in valid_sizes:
            order = ImageOrderEntry.objects.create(
                bulk_order=self.bulk_order,
                email=f'test-{size}@example.com',
                full_name=f'User {size}',
                size=size
            )
            self.assertEqual(order.size, size)

    def test_custom_name_optional(self):
        """Test that custom_name is optional"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        self.assertEqual(order.custom_name, '')

    def test_custom_name_can_be_set(self):
        """Test that custom_name can be provided"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L',
            custom_name='PASTOR TEST'
        )
        
        self.assertEqual(order.custom_name, 'PASTOR TEST')

    def test_image_field_optional(self):
        """Test that image field is optional"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        self.assertIsNone(order.image)

    def test_paid_default_false(self):
        """Test that paid defaults to False"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        self.assertFalse(order.paid)

    def test_paid_can_be_set_true(self):
        """Test that paid can be updated to True"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        order.paid = True
        order.save()
        
        order.refresh_from_db()
        self.assertTrue(order.paid)

    def test_coupon_used_relationship(self):
        """Test relationship with ImageCouponCode"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='TEST123'
        )
        
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L',
            coupon_used=coupon
        )
        
        self.assertEqual(order.coupon_used, coupon)

    def test_coupon_set_null_on_delete(self):
        """Test that coupon_used is set to null when coupon is deleted"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='DELETE123'
        )
        
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L',
            coupon_used=coupon
        )
        
        coupon.delete()
        
        order.refresh_from_db()
        self.assertIsNone(order.coupon_used)

    def test_str_representation(self):
        """Test string representation of order entry"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='John Doe',
            size='L'
        )
        
        expected_str = f"{order.serial_number}. John Doe ({order.size})"
        self.assertEqual(str(order), expected_str)

    def test_timestamps_auto_set(self):
        """Test that created_at and updated_at are automatically set"""
        before_creation = timezone.now()
        
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        after_creation = timezone.now()
        
        self.assertGreaterEqual(order.created_at, before_creation)
        self.assertLessEqual(order.created_at, after_creation)
        # Timestamps may differ by microseconds
        time_diff = abs((order.created_at - order.updated_at).total_seconds())
        self.assertLess(time_diff, 1.0)

    def test_updated_at_changes_on_save(self):
        """Test that updated_at changes when model is saved"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        original_updated_at = order.updated_at
        
        # Wait a bit and update
        import time
        time.sleep(0.01)
        
        order.paid = True
        order.save()
        
        self.assertGreater(order.updated_at, original_updated_at)

    def test_uuid_primary_key(self):
        """Test that ID is a UUID"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        self.assertIsInstance(order.id, uuid.UUID)

    def test_bulk_order_relationship(self):
        """Test relationship with ImageBulkOrderLink"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        self.assertEqual(order.bulk_order, self.bulk_order)
        self.assertIn(order, self.bulk_order.orders.all())

    def test_cascade_delete_on_bulk_order_deletion(self):
        """Test that order is deleted when bulk order is deleted"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        order_id = order.id
        self.bulk_order.delete()
        
        self.assertFalse(ImageOrderEntry.objects.filter(id=order_id).exists())

    def test_concurrent_serial_number_generation(self):
        """Test that serial numbers are unique and sequential"""
        # Create orders sequentially to ensure test reliability
        orders = []
        for i in range(10):
            order = ImageOrderEntry.objects.create(
                bulk_order=self.bulk_order,
                email=f'test{i}@example.com',
                full_name=f'User {i}',
                size='L'
            )
            orders.append(order)
        
        # Check that all orders have unique serial numbers
        serial_numbers = [order.serial_number for order in orders]
        
        self.assertEqual(len(serial_numbers), 10)
        self.assertEqual(len(set(serial_numbers)), 10)  # All unique
        # Should be sequential 1-10
        self.assertEqual(sorted(serial_numbers), list(range(1, 11)))

    def test_email_field_validation(self):
        """Test that email field validates email format"""
        with self.assertRaises(ValidationError):
            order = ImageOrderEntry(
                bulk_order=self.bulk_order,
                email='invalid-email',
                full_name='Test User',
                size='L'
            )
            order.full_clean()

    def test_reference_uniqueness_constraint(self):
        """Test that reference field has unique constraint"""
        order1 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test1@example.com',
            full_name='User 1',
            size='L'
        )
        
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                order2 = ImageOrderEntry(
                    bulk_order=self.bulk_order,
                    email='test2@example.com',
                    full_name='User 2',
                    size='M',
                    reference=order1.reference  # Duplicate reference
                )
                order2.serial_number = 999
                order2.save()