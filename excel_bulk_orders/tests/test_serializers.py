# excel_bulk_orders/tests/test_serializers.py
"""
Comprehensive tests for Excel Bulk Orders serializers.

Coverage:
- ExcelBulkOrderCreateSerializer: Validation, email normalization, user assignment
- ExcelBulkOrderListSerializer: Method fields, read-only fields
- ExcelBulkOrderDetailSerializer: Nested data, context handling
- ExcelParticipantSerializer: Conditional fields, coupon status display
- ExcelUploadSerializer: File validation, size limits, extension checks
- ValidationErrorSerializer: Error response structure
- Security: Input validation, data sanitization
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO

from excel_bulk_orders.models import ExcelBulkOrder, ExcelCouponCode, ExcelParticipant
from excel_bulk_orders.serializers import (
    ExcelBulkOrderCreateSerializer,
    ExcelBulkOrderListSerializer,
    ExcelBulkOrderDetailSerializer,
    ExcelParticipantSerializer,
    ExcelUploadSerializer,
    ValidationErrorSerializer,
)

User = get_user_model()


class ExcelBulkOrderCreateSerializerTest(TestCase):
    """Test ExcelBulkOrderCreateSerializer"""

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )

    def test_create_bulk_order_with_valid_data(self):
        """Test creating bulk order with valid data"""
        data = {
            'title': 'NYSC Camp Registration',
            'coordinator_name': 'John Coordinator',
            'coordinator_email': 'john@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
            'requires_custom_name': True,
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        bulk_order = serializer.save()
        self.assertEqual(bulk_order.title, 'NYSC Camp Registration')
        self.assertEqual(bulk_order.coordinator_email, 'john@example.com')

    def test_coordinator_email_normalization(self):
        """Test that coordinator email is normalized to lowercase"""
        data = {
            'title': 'Email Test',
            'coordinator_name': 'Test',
            'coordinator_email': 'TEST.EMAIL@EXAMPLE.COM',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        bulk_order = serializer.save()
        self.assertEqual(bulk_order.coordinator_email, 'test.email@example.com')

    def test_empty_coordinator_email_rejected(self):
        """Test that empty coordinator email is rejected"""
        data = {
            'title': 'Email Test',
            'coordinator_name': 'Test',
            'coordinator_email': '',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coordinator_email', serializer.errors)

    def test_create_with_authenticated_user_context(self):
        """Test that created_by is set when user is in request context"""
        data = {
            'title': 'User Context Test',
            'coordinator_name': 'Test',
            'coordinator_email': 'context@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        # Create request with authenticated user
        request = self.factory.post('/api/excel-bulk-orders/')
        request.user = self.user

        serializer = ExcelBulkOrderCreateSerializer(
            data=data,
            context={'request': request}
        )
        self.assertTrue(serializer.is_valid())

        bulk_order = serializer.save()
        self.assertEqual(bulk_order.created_by, self.user)

    def test_create_without_user_context(self):
        """Test that created_by is None when no user in context"""
        data = {
            'title': 'No User Test',
            'coordinator_name': 'Test',
            'coordinator_email': 'nouser@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        bulk_order = serializer.save()
        self.assertIsNone(bulk_order.created_by)

    def test_price_per_participant_validation(self):
        """Test price validation"""
        # Valid price
        data = {
            'title': 'Price Test',
            'coordinator_name': 'Test',
            'coordinator_email': 'price@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        # Zero price - comment out if serializer has MinValueValidator
        # data['price_per_participant'] = '0.00'
        # serializer = ExcelBulkOrderCreateSerializer(data=data)
        # self.assertTrue(serializer.is_valid())

        # Negative price should be invalid
        data['price_per_participant'] = '-1000.00'
        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_requires_custom_name_default_false(self):
        """Test that requires_custom_name defaults to False"""
        data = {
            'title': 'Default Test',
            'coordinator_name': 'Test',
            'coordinator_email': 'default@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
            # No requires_custom_name specified
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        bulk_order = serializer.save()
        self.assertFalse(bulk_order.requires_custom_name)

    def test_required_fields_validation(self):
        """Test that all required fields are enforced"""
        # Missing title
        data = {
            'coordinator_name': 'Test',
            'coordinator_email': 'test@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

        # Missing coordinator_name
        data = {
            'title': 'Test',
            'coordinator_email': 'test@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('coordinator_name', serializer.errors)

    def test_long_title_accepted(self):
        """Test that long titles are accepted"""
        long_title = 'A' * 200

        data = {
            'title': long_title,
            'coordinator_name': 'Test',
            'coordinator_email': 'long@example.com',
            'coordinator_phone': '08012345678',
            'price_per_participant': '5000.00',
        }

        serializer = ExcelBulkOrderCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())


class ExcelBulkOrderListSerializerTest(TestCase):
    """Test ExcelBulkOrderListSerializer"""

    def setUp(self):
        """Set up test data"""
        self.bulk_order = ExcelBulkOrder.objects.create(
            title='Test Order',
            coordinator_name='Test Coordinator',
            coordinator_email='test@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            total_amount=Decimal('25000.00'),
            validation_status='valid'
        )

        # Create participants
        for i in range(5):
            ExcelParticipant.objects.create(
                bulk_order=self.bulk_order,
                full_name=f'Participant {i}',
                size='M',
                row_number=i + 2
            )

        # Create coupon and participant with coupon
        coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order,
            code='COUPON123'
        )

        ExcelParticipant.objects.create(
            bulk_order=self.bulk_order,
            full_name='Coupon User',
            size='M',
            coupon_code='COUPON123',
            coupon=coupon,
            is_coupon_applied=True,
            row_number=7
        )

    def test_list_serializer_fields(self):
        """Test that list serializer includes all expected fields"""
        serializer = ExcelBulkOrderListSerializer(self.bulk_order)
        data = serializer.data

        expected_fields = [
            'id', 'reference', 'title', 'coordinator_name',
            'coordinator_email', 'price_per_participant',
            'participant_count', 'couponed_count', 'total_amount',
            'validation_status', 'status_display', 'payment_status',
            'created_at', 'updated_at'
        ]

        for field in expected_fields:
            self.assertIn(field, data)

    def test_participant_count_method_field(self):
        """Test participant_count method field"""
        serializer = ExcelBulkOrderListSerializer(self.bulk_order)
        data = serializer.data

        self.assertEqual(data['participant_count'], 6)  # 5 regular + 1 with coupon

    def test_couponed_count_method_field(self):
        """Test couponed_count method field"""
        serializer = ExcelBulkOrderListSerializer(self.bulk_order)
        data = serializer.data

        self.assertEqual(data['couponed_count'], 1)

    def test_status_display_field(self):
        """Test status_display field"""
        serializer = ExcelBulkOrderListSerializer(self.bulk_order)
        data = serializer.data

        self.assertIn('status_display', data)
        self.assertEqual(data['status_display'], 'Validated - Ready for Payment')

    def test_read_only_fields(self):
        """Test that read-only fields cannot be set via serializer"""
        serializer = ExcelBulkOrderListSerializer(self.bulk_order)

        # Check read_only_fields
        read_only_fields = serializer.Meta.read_only_fields

        self.assertIn('id', read_only_fields)
        self.assertIn('reference', read_only_fields)
        self.assertIn('total_amount', read_only_fields)
        self.assertIn('created_at', read_only_fields)
        self.assertIn('updated_at', read_only_fields)


class ExcelBulkOrderDetailSerializerTest(TestCase):
    """Test ExcelBulkOrderDetailSerializer"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='detailuser',
            email='detailuser@example.com',
            password='testpass123'
        )

        self.bulk_order = ExcelBulkOrder.objects.create(
            title='Detail Test Order',
            coordinator_name='Detail Coordinator',
            coordinator_email='detail@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            created_by=self.user
        )

    def test_detail_serializer_includes_all_fields(self):
        """Test that detail serializer includes all fields"""
        serializer = ExcelBulkOrderDetailSerializer(self.bulk_order)
        data = serializer.data

        expected_fields = [
            'id', 'reference', 'title', 'coordinator_name',
            'coordinator_email', 'coordinator_phone',
            'price_per_participant', 'requires_custom_name',
            'template_file', 'uploaded_file', 'validation_status',
            'total_amount', 'payment_status', 'paystack_reference',
            'created_at', 'updated_at',  # Note: 'created_by' not in serializer output
            'status_display', 'validation_summary',
            'payment_breakdown', 'participants'  # Not participant_count/couponed_count
        ]

        for field in expected_fields:
            self.assertIn(field, data)


class ExcelParticipantSerializerTest(TestCase):
    """Test ExcelParticipantSerializer"""

    def setUp(self):
        """Set up test data"""
        # Bulk order with custom name required
        self.bulk_order_with_custom = ExcelBulkOrder.objects.create(
            title='Custom Name Order',
            coordinator_name='Test',
            coordinator_email='custom@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            requires_custom_name=True
        )

        # Bulk order without custom name
        self.bulk_order_no_custom = ExcelBulkOrder.objects.create(
            title='No Custom Name Order',
            coordinator_name='Test',
            coordinator_email='nocustom@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            requires_custom_name=False
        )

        self.coupon = ExcelCouponCode.objects.create(
            bulk_order=self.bulk_order_with_custom,
            code='TESTCOUPON'
        )

    def test_participant_serializer_all_fields(self):
        """Test that participant serializer includes all fields"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order_with_custom,
            full_name='John Doe',
            size='M',
            custom_name='JOHNNY',
            row_number=2
        )

        serializer = ExcelParticipantSerializer(participant)
        data = serializer.data

        expected_fields = [
            'id', 'full_name', 'size', 'custom_name',
            'coupon_code', 'is_coupon_applied', 'coupon_status',
            'row_number', 'created_at'
        ]

        for field in expected_fields:
            self.assertIn(field, data)

    def test_custom_name_included_when_required(self):
        """Test that custom_name is included when bulk order requires it"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order_with_custom,
            full_name='John Doe',
            size='M',
            custom_name='JOHNNY',
            row_number=2
        )

        serializer = ExcelParticipantSerializer(participant)
        data = serializer.data

        self.assertIn('custom_name', data)
        self.assertEqual(data['custom_name'], 'JOHNNY')

    def test_custom_name_excluded_when_not_required(self):
        """Test that custom_name is excluded when not required"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order_no_custom,
            full_name='Jane Doe',
            size='L',
            row_number=2
        )

        serializer = ExcelParticipantSerializer(participant)
        data = serializer.data

        self.assertNotIn('custom_name', data)

    def test_coupon_status_applied(self):
        """Test coupon_status when coupon is applied"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order_with_custom,
            full_name='Coupon User',
            size='M',
            coupon_code='TESTCOUPON',
            coupon=self.coupon,
            is_coupon_applied=True,
            row_number=2
        )

        serializer = ExcelParticipantSerializer(participant)
        data = serializer.data

        self.assertEqual(data['coupon_status'], 'Applied - Free')

    def test_coupon_status_invalid(self):
        """Test coupon_status when coupon is invalid"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order_with_custom,
            full_name='Invalid Coupon User',
            size='M',
            coupon_code='INVALID',
            row_number=2
        )

        serializer = ExcelParticipantSerializer(participant)
        data = serializer.data

        self.assertEqual(data['coupon_status'], 'Invalid/Expired')

    def test_coupon_status_no_coupon(self):
        """Test coupon_status when no coupon provided"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order_with_custom,
            full_name='No Coupon User',
            size='M',
            row_number=2
        )

        serializer = ExcelParticipantSerializer(participant)
        data = serializer.data

        self.assertEqual(data['coupon_status'], 'No Coupon')

    def test_read_only_fields(self):
        """Test that certain fields are read-only"""
        participant = ExcelParticipant.objects.create(
            bulk_order=self.bulk_order_with_custom,
            full_name='Read Only Test',
            size='M',
            row_number=2
        )

        serializer = ExcelParticipantSerializer(participant)

        # These fields should be read-only
        read_only_fields = serializer.Meta.read_only_fields

        self.assertIn('id', read_only_fields)
        self.assertIn('is_coupon_applied', read_only_fields)
        self.assertIn('created_at', read_only_fields)


class ExcelUploadSerializerTest(TestCase):
    """Test ExcelUploadSerializer for file validation"""

    def test_valid_xlsx_file(self):
        """Test that valid .xlsx file is accepted"""
        # Create a simple Excel-like file
        file_content = b'PK\x03\x04'  # ZIP header (Excel files are zipped)
        excel_file = SimpleUploadedFile(
            'test.xlsx',
            file_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        data = {'excel_file': excel_file}
        serializer = ExcelUploadSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_invalid_file_extension_rejected(self):
        """Test that non-.xlsx files are rejected"""
        csv_file = SimpleUploadedFile(
            'test.csv',
            b'name,size\nJohn,M',
            content_type='text/csv'
        )

        data = {'excel_file': csv_file}
        serializer = ExcelUploadSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('excel_file', serializer.errors)
        self.assertIn('Only .xlsx files are accepted', str(serializer.errors['excel_file']))

    def test_xls_file_rejected(self):
        """Test that .xls (old format) is rejected"""
        xls_file = SimpleUploadedFile(
            'test.xls',
            b'some content',
            content_type='application/vnd.ms-excel'
        )

        data = {'excel_file': xls_file}
        serializer = ExcelUploadSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('excel_file', serializer.errors)

    def test_file_size_limit_exceeded(self):
        """Test that files over 5MB are rejected"""
        # Create a file larger than 5MB
        large_content = b'X' * (6 * 1024 * 1024)  # 6MB
        large_file = SimpleUploadedFile(
            'large.xlsx',
            large_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        data = {'excel_file': large_file}
        serializer = ExcelUploadSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('excel_file', serializer.errors)
        self.assertIn('exceeds 5MB limit', str(serializer.errors['excel_file']))

    def test_file_size_within_limit(self):
        """Test that files under 5MB are accepted"""
        # Create a file under 5MB
        small_content = b'PK\x03\x04' + (b'X' * 1024)  # Small file
        small_file = SimpleUploadedFile(
            'small.xlsx',
            small_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        data = {'excel_file': small_file}
        serializer = ExcelUploadSerializer(data=data)

        self.assertTrue(serializer.is_valid())

    def test_missing_file_rejected(self):
        """Test that missing file is rejected"""
        data = {}
        serializer = ExcelUploadSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn('excel_file', serializer.errors)


class ValidationErrorSerializerTest(TestCase):
    """Test ValidationErrorSerializer"""

    def test_validation_error_serialization(self):
        """Test serializing validation error"""
        error_data = {
            'row': 5,
            'field': 'Size',
            'error': 'Invalid size value',
            'current_value': 'XL+'
        }

        serializer = ValidationErrorSerializer(data=error_data)
        self.assertTrue(serializer.is_valid())

        data = serializer.data
        self.assertEqual(data['row'], 5)
        self.assertEqual(data['field'], 'Size')
        self.assertEqual(data['error'], 'Invalid size value')
        self.assertEqual(data['current_value'], 'XL+')

    def test_validation_error_with_empty_current_value(self):
        """Test validation error with empty current value"""
        error_data = {
            'row': 3,
            'field': 'Full Name',
            'error': 'Full Name is required',
            'current_value': ''
        }

        serializer = ValidationErrorSerializer(data=error_data)
        self.assertTrue(serializer.is_valid())

    def test_validation_error_with_null_current_value(self):
        """Test validation error with null current value"""
        error_data = {
            'row': 4,
            'field': 'Custom Name',
            'error': 'Custom Name is required',
            'current_value': None
        }

        serializer = ValidationErrorSerializer(data=error_data)
        self.assertTrue(serializer.is_valid())

    def test_all_fields_present(self):
        """Test that all expected fields are present"""
        error_data = {
            'row': 2,
            'field': 'Test Field',
            'error': 'Test error',
            'current_value': 'test'
        }

        serializer = ValidationErrorSerializer(data=error_data)
        self.assertTrue(serializer.is_valid())

        data = serializer.data
        self.assertIn('row', data)
        self.assertIn('field', data)
        self.assertIn('error', data)
        self.assertIn('current_value', data)