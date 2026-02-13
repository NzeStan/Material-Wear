# image_bulk_orders/tests/test_serializers.py
"""
Comprehensive test suite for image_bulk_orders serializers.

Tests cover:
- ImageBulkOrderLinkSummarySerializer: Field validation, method fields, expiry logic
- ImageCouponCodeSerializer: Read-only fields, related field serialization
- ImageOrderEntrySerializer: Coupon validation, image validation, custom_name conditional logic
- ImageBulkOrderLinkSerializer: Full CRUD serialization, nested relationships

Coverage targets: 100% for all serializers
"""
from django.test import TestCase
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, Mock, MagicMock
from io import BytesIO
from PIL import Image as PILImage
from rest_framework.test import APIRequestFactory

from image_bulk_orders.models import ImageBulkOrderLink, ImageCouponCode, ImageOrderEntry
from image_bulk_orders.serializers import (
    ImageBulkOrderLinkSummarySerializer,
    ImageCouponCodeSerializer,
    ImageOrderEntrySerializer,
    ImageBulkOrderLinkSerializer
)

User = get_user_model()


def create_test_image(format='PNG', size=(100, 100), color='red'):
    """Helper function to create test image file"""
    file = BytesIO()
    image = PILImage.new('RGB', size, color)
    image.save(file, format)
    file.seek(0)
    return SimpleUploadedFile(
        name=f'test_image.{format.lower()}',
        content=file.read(),
        content_type=f'image/{format.lower()}'
    )


class ImageBulkOrderLinkSummarySerializerTest(TestCase):
    """Test ImageBulkOrderLinkSummarySerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.future_deadline = timezone.now() + timedelta(days=30)
        self.past_deadline = timezone.now() - timedelta(days=1)

    def test_serialize_bulk_order_link(self):
        """Test basic serialization of bulk order link"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Test Church',
            price_per_item=Decimal('5000.00'),
            custom_branding_enabled=True,
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        serializer = ImageBulkOrderLinkSummarySerializer(bulk_order)
        data = serializer.data
        
        self.assertEqual(data['organization_name'], 'TEST CHURCH')
        self.assertEqual(data['slug'], bulk_order.slug)
        self.assertEqual(data['price_per_item'], '5000.00')
        self.assertTrue(data['custom_branding_enabled'])
        self.assertIn('payment_deadline', data)

    def test_is_expired_false_for_future_deadline(self):
        """Test is_expired returns False for future deadline"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Future Deadline',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        serializer = ImageBulkOrderLinkSummarySerializer(bulk_order)
        
        self.assertFalse(serializer.data['is_expired'])

    def test_is_expired_true_for_past_deadline(self):
        """Test is_expired returns True for past deadline"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Past Deadline',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.past_deadline,
            created_by=self.user
        )
        
        serializer = ImageBulkOrderLinkSummarySerializer(bulk_order)
        
        self.assertTrue(serializer.data['is_expired'])

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_shareable_url_with_request_context(self):
        """Test shareable_url with request context"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='URL Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        request = self.factory.get('/', HTTP_HOST='testserver')
        
        serializer = ImageBulkOrderLinkSummarySerializer(
            bulk_order,
            context={'request': request}
        )
        
        expected_url = f'http://testserver/image-bulk-order/{bulk_order.slug}/'
        self.assertEqual(serializer.data['shareable_url'], expected_url)

    def test_shareable_url_without_request_context(self):
        """Test shareable_url without request context"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='No Context',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        serializer = ImageBulkOrderLinkSummarySerializer(bulk_order)
        
        expected_url = f'/image-bulk-order/{bulk_order.slug}/'
        self.assertEqual(serializer.data['shareable_url'], expected_url)

    def test_only_expected_fields_present(self):
        """Test that only expected fields are included"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Field Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        serializer = ImageBulkOrderLinkSummarySerializer(bulk_order)
        expected_fields = {
            'id', 'slug', 'organization_name', 'price_per_item',
            'custom_branding_enabled', 'payment_deadline',
            'is_expired', 'shareable_url'
        }
        
        self.assertEqual(set(serializer.data.keys()), expected_fields)


class ImageCouponCodeSerializerTest(TestCase):
    """Test ImageCouponCodeSerializer"""

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

    def test_serialize_coupon_code(self):
        """Test basic serialization of coupon code"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='TEST12345'
        )
        
        serializer = ImageCouponCodeSerializer(coupon)
        data = serializer.data
        
        self.assertEqual(data['code'], 'TEST12345')
        self.assertFalse(data['is_used'])
        self.assertEqual(data['bulk_order_name'], 'TEST CHURCH')
        self.assertEqual(data['bulk_order_slug'], self.bulk_order.slug)
        self.assertIn('created_at', data)

    def test_bulk_order_name_from_source(self):
        """Test bulk_order_name comes from related field"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='RELATION123'
        )
        
        serializer = ImageCouponCodeSerializer(coupon)
        
        self.assertEqual(
            serializer.data['bulk_order_name'],
            self.bulk_order.organization_name
        )

    def test_read_only_fields(self):
        """Test that is_used and created_at are read-only"""
        serializer = ImageCouponCodeSerializer()
        
        self.assertIn('is_used', serializer.Meta.read_only_fields)
        self.assertIn('created_at', serializer.Meta.read_only_fields)

    def test_all_expected_fields_present(self):
        """Test that all expected fields are present"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='FIELDS123'
        )
        
        serializer = ImageCouponCodeSerializer(coupon)
        expected_fields = {
            'id', 'bulk_order', 'bulk_order_name', 'bulk_order_slug',
            'code', 'is_used', 'created_at'
        }
        
        self.assertEqual(set(serializer.data.keys()), expected_fields)


class ImageOrderEntrySerializerTest(TestCase):
    """Test ImageOrderEntrySerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
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
        
        self.bulk_order_no_branding = ImageBulkOrderLink.objects.create(
            organization_name='No Branding Church',
            price_per_item=Decimal('4000.00'),
            custom_branding_enabled=False,
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )

    def test_serialize_order_entry_without_image(self):
        """Test serialization of order entry without image"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        serializer = ImageOrderEntrySerializer(order)
        data = serializer.data
        
        self.assertEqual(data['email'], 'test@example.com')
        self.assertEqual(data['full_name'], 'Test User')
        self.assertEqual(data['size'], 'L')
        self.assertFalse(data['paid'])
        self.assertIsNone(data['image_url'])

    def test_image_url_method_field_with_image(self):
        """Test image_url returns correct URL when image exists"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        # Mock Cloudinary field
        order.image = Mock()
        order.image.url = 'https://res.cloudinary.com/test/image.jpg'
        
        serializer = ImageOrderEntrySerializer(order)
        
        self.assertEqual(serializer.data['image_url'], 'https://res.cloudinary.com/test/image.jpg')

    def test_image_url_method_field_without_image(self):
        """Test image_url returns None when no image"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        serializer = ImageOrderEntrySerializer(order)
        
        self.assertIsNone(serializer.data['image_url'])

    @patch('magic.from_buffer')
    def test_validate_image_valid_jpeg(self, mock_magic):
        """Test image validation with valid JPEG"""
        mock_magic.return_value = 'image/jpeg'
        
        image = create_test_image(format='JPEG')
        
        serializer = ImageOrderEntrySerializer()
        validated_image = serializer.validate_image(image)
        
        self.assertIsNotNone(validated_image)

    @patch('magic.from_buffer')
    def test_validate_image_valid_png(self, mock_magic):
        """Test image validation with valid PNG"""
        mock_magic.return_value = 'image/png'
        
        image = create_test_image(format='PNG')
        
        serializer = ImageOrderEntrySerializer()
        validated_image = serializer.validate_image(image)
        
        self.assertIsNotNone(validated_image)

    @patch('magic.from_buffer')
    def test_validate_image_valid_gif(self, mock_magic):
        """Test image validation with valid GIF"""
        mock_magic.return_value = 'image/gif'
        
        image = create_test_image(format='GIF')
        
        serializer = ImageOrderEntrySerializer()
        validated_image = serializer.validate_image(image)
        
        self.assertIsNotNone(validated_image)

    @patch('magic.from_buffer')
    def test_validate_image_valid_webp(self, mock_magic):
        """Test image validation with valid WebP"""
        mock_magic.return_value = 'image/webp'
        
        image = create_test_image(format='PNG')  # PIL doesn't support WebP natively
        
        serializer = ImageOrderEntrySerializer()
        validated_image = serializer.validate_image(image)
        
        self.assertIsNotNone(validated_image)

    @patch('magic.from_buffer')
    def test_validate_image_invalid_type(self, mock_magic):
        """Test image validation rejects invalid file types"""
        mock_magic.return_value = 'application/pdf'
        
        # Create fake PDF file
        fake_pdf = SimpleUploadedFile(
            'test.pdf',
            b'fake pdf content',
            content_type='application/pdf'
        )
        
        serializer = ImageOrderEntrySerializer()
        
        with self.assertRaises(Exception) as context:
            serializer.validate_image(fake_pdf)
        
        self.assertIn('Invalid image type', str(context.exception))

    def test_validate_image_exceeds_max_size(self):
        """Test image validation rejects files over 10MB"""
        # Create large image (over 10MB)
        large_file = SimpleUploadedFile(
            'large.jpg',
            b'x' * (11 * 1024 * 1024),  # 11MB
            content_type='image/jpeg'
        )
        
        serializer = ImageOrderEntrySerializer()
        
        with self.assertRaises(Exception) as context:
            serializer.validate_image(large_file)
        
        self.assertIn('exceeds maximum allowed size', str(context.exception))

    def test_validate_image_none_allowed(self):
        """Test that None is allowed for image field"""
        serializer = ImageOrderEntrySerializer()
        
        result = serializer.validate_image(None)
        
        self.assertIsNone(result)

    def test_validate_with_valid_coupon_code(self):
        """Test validation with valid coupon code"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='VALID123'
        )
        
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'size': 'L',
            'coupon_code': 'VALID123'
        }
        
        serializer = ImageOrderEntrySerializer(
            data=data,
            context={'bulk_order': self.bulk_order}
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['coupon_used'], coupon)
        self.assertTrue(serializer.validated_data['paid'])

    def test_validate_with_invalid_coupon_code(self):
        """Test validation rejects invalid coupon code"""
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'size': 'L',
            'coupon_code': 'INVALID999'
        }
        
        serializer = ImageOrderEntrySerializer(
            data=data,
            context={'bulk_order': self.bulk_order}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('coupon_code', serializer.errors)

    def test_validate_with_already_used_coupon(self):
        """Test validation rejects already used coupon"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='USED123',
            is_used=True
        )
        
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'size': 'L',
            'coupon_code': 'USED123'
        }
        
        serializer = ImageOrderEntrySerializer(
            data=data,
            context={'bulk_order': self.bulk_order}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('coupon_code', serializer.errors)

    def test_validate_coupon_from_different_bulk_order(self):
        """Test validation rejects coupon from different bulk order"""
        other_bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Other Church',
            price_per_item=Decimal('4000.00'),
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )
        
        coupon = ImageCouponCode.objects.create(
            bulk_order=other_bulk_order,
            code='OTHER123'
        )
        
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'size': 'L',
            'coupon_code': 'OTHER123'
        }
        
        serializer = ImageOrderEntrySerializer(
            data=data,
            context={'bulk_order': self.bulk_order}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('coupon_code', serializer.errors)
        self.assertIn('does not belong to', str(serializer.errors['coupon_code']))

    def test_validate_expired_bulk_order(self):
        """Test validation rejects submissions to expired bulk orders"""
        expired_bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Expired Church',
            price_per_item=Decimal('5000.00'),
            payment_deadline=timezone.now() - timedelta(days=1),
            created_by=self.user
        )
        
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'size': 'L'
        }
        
        serializer = ImageOrderEntrySerializer(
            data=data,
            context={'bulk_order': expired_bulk_order}
        )
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('payment_deadline', serializer.errors)

    def test_validate_without_bulk_order_context(self):
        """Test validation fails without bulk_order in context"""
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'size': 'L'
        }
        
        serializer = ImageOrderEntrySerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('bulk_order', serializer.errors)

    def test_to_representation_removes_custom_name_when_disabled(self):
        """Test custom_name is removed when custom_branding_enabled=False"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order_no_branding,
            email='test@example.com',
            full_name='Test User',
            size='L',
            custom_name='SHOULD NOT APPEAR'
        )
        
        serializer = ImageOrderEntrySerializer(order)
        
        self.assertNotIn('custom_name', serializer.data)

    def test_to_representation_includes_custom_name_when_enabled(self):
        """Test custom_name is included when custom_branding_enabled=True"""
        order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L',
            custom_name='PASTOR TEST'
        )
        
        serializer = ImageOrderEntrySerializer(order)
        
        self.assertIn('custom_name', serializer.data)
        self.assertEqual(serializer.data['custom_name'], 'PASTOR TEST')

    def test_custom_name_removed_when_branding_disabled(self):
        """Test that custom_name is removed when branding is disabled"""
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'size': 'L',
            'custom_name': 'SHOULD BE REMOVED'
        }
        
        serializer = ImageOrderEntrySerializer(
            data=data,
            context={'bulk_order': self.bulk_order_no_branding}
        )
        
        self.assertTrue(serializer.is_valid())
        self.assertNotIn('custom_name', serializer.validated_data)

    def test_read_only_fields(self):
        """Test that appropriate fields are read-only"""
        serializer = ImageOrderEntrySerializer()
        
        read_only_fields = serializer.Meta.read_only_fields
        
        self.assertIn('id', read_only_fields)
        self.assertIn('reference', read_only_fields)
        self.assertIn('bulk_order', read_only_fields)
        self.assertIn('serial_number', read_only_fields)
        self.assertIn('paid', read_only_fields)
        self.assertIn('created_at', read_only_fields)
        self.assertIn('updated_at', read_only_fields)
        self.assertIn('image_url', read_only_fields)

    def test_coupon_code_uppercase_normalization(self):
        """Test that coupon codes are normalized to uppercase"""
        coupon = ImageCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='LOWERCASE'
        )
        
        data = {
            'email': 'test@example.com',
            'full_name': 'Test User',
            'size': 'L',
            'coupon_code': 'lowercase'  # lowercase input
        }
        
        serializer = ImageOrderEntrySerializer(
            data=data,
            context={'bulk_order': self.bulk_order}
        )
        
        self.assertTrue(serializer.is_valid())


class ImageBulkOrderLinkSerializerTest(TestCase):
    """Test ImageBulkOrderLinkSerializer (full serializer)"""

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.future_deadline = timezone.now() + timedelta(days=30)

    def test_serialize_bulk_order_with_nested_data(self):
        """Test full serialization with nested orders and coupons"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Full Test',
            price_per_item=Decimal('5000.00'),
            custom_branding_enabled=True,
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        # Create nested data
        order = ImageOrderEntry.objects.create(
            bulk_order=bulk_order,
            email='test@example.com',
            full_name='Test User',
            size='L'
        )
        
        coupon = ImageCouponCode.objects.create(
            bulk_order=bulk_order,
            code='NESTED123'
        )
        
        serializer = ImageBulkOrderLinkSerializer(bulk_order)
        data = serializer.data
        
        self.assertEqual(data['organization_name'], 'FULL TEST')
        self.assertEqual(data['order_count'], 1)
        self.assertEqual(data['coupon_count'], 1)
        self.assertEqual(data['paid_count'], 0)
        self.assertIn('orders', data)
        self.assertEqual(len(data['orders']), 1)

    def test_paid_count_method_field(self):
        """Test paid_count returns correct count"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Paid Count Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        # Create orders
        ImageOrderEntry.objects.create(
            bulk_order=bulk_order,
            email='paid@example.com',
            full_name='Paid User',
            size='L',
            paid=True
        )
        
        ImageOrderEntry.objects.create(
            bulk_order=bulk_order,
            email='unpaid@example.com',
            full_name='Unpaid User',
            size='M',
            paid=False
        )
        
        serializer = ImageBulkOrderLinkSerializer(bulk_order)
        
        self.assertEqual(serializer.data['paid_count'], 1)

    def test_create_sets_created_by_from_context(self):
        """Test that create() sets created_by from request context"""
        request = self.factory.post('/')
        request.user = self.user
        
        data = {
            'organization_name': 'Context Test',
            'price_per_item': '5000.00',
            'custom_branding_enabled': True,
            'payment_deadline': self.future_deadline.isoformat()
        }
        
        serializer = ImageBulkOrderLinkSerializer(
            data=data,
            context={'request': request}
        )
        
        self.assertTrue(serializer.is_valid())
        bulk_order = serializer.save()
        
        self.assertEqual(bulk_order.created_by, self.user)

    @override_settings(ALLOWED_HOSTS=['testserver'])
    def test_shareable_url_with_request(self):
        """Test shareable_url with request in context"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='URL Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        request = self.factory.get('/', HTTP_HOST='testserver')
        
        serializer = ImageBulkOrderLinkSerializer(
            bulk_order,
            context={'request': request}
        )
        
        expected_url = f'http://testserver/image-bulk-order/{bulk_order.slug}/'
        self.assertEqual(serializer.data['shareable_url'], expected_url)

    def test_all_expected_fields_present(self):
        """Test that all expected fields are present"""
        bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Fields Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=self.future_deadline,
            created_by=self.user
        )
        
        serializer = ImageBulkOrderLinkSerializer(bulk_order)
        expected_fields = {
            'id', 'slug', 'organization_name', 'price_per_item',
            'custom_branding_enabled', 'payment_deadline',
            'created_by', 'created_at', 'updated_at',
            'orders', 'order_count', 'paid_count', 'coupon_count',
            'shareable_url'
        }
        
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_read_only_fields(self):
        """Test that appropriate fields are read-only"""
        serializer = ImageBulkOrderLinkSerializer()
        
        read_only_fields = serializer.Meta.read_only_fields
        
        self.assertIn('created_by', read_only_fields)
        self.assertIn('created_at', read_only_fields)
        self.assertIn('updated_at', read_only_fields)
        self.assertIn('slug', read_only_fields)

    def test_lookup_field_is_slug(self):
        """Test that lookup_field is set to slug"""
        serializer = ImageBulkOrderLinkSerializer()
        
        self.assertEqual(serializer.Meta.lookup_field, 'slug')