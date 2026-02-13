# image_bulk_orders/tests/test_utils.py
"""
Comprehensive test suite for image_bulk_orders utility functions.

Tests cover:
- generate_coupon_codes_image: Coupon generation with uniqueness
- _get_image_bulk_order_with_orders: Query optimization helper
- generate_image_bulk_order_pdf: PDF generation and content
- generate_image_bulk_order_word: DOCX generation
- generate_image_bulk_order_excel: XLSX generation
- generate_admin_package_with_images: Complete package generation with images
- download_image_from_cloudinary: Image downloading

Coverage targets: 100% for all utility functions
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch, Mock, MagicMock
import zipfile
from io import BytesIO

from image_bulk_orders.models import ImageBulkOrderLink, ImageCouponCode, ImageOrderEntry
from image_bulk_orders.utils import (
    generate_coupon_codes_image,
    _get_image_bulk_order_with_orders,
    generate_image_bulk_order_pdf,
    generate_image_bulk_order_word,
    generate_image_bulk_order_excel,
    generate_admin_package_with_images,
    download_image_from_cloudinary
)

User = get_user_model()


class GenerateCouponCodesImageTest(TestCase):
    """Test generate_coupon_codes_image function"""

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

    def test_generate_default_count(self):
        """Test generating default 10 coupons"""
        coupons = generate_coupon_codes_image(self.bulk_order)
        
        self.assertEqual(len(coupons), 10)
        self.assertEqual(ImageCouponCode.objects.filter(bulk_order=self.bulk_order).count(), 10)

    def test_generate_custom_count(self):
        """Test generating custom number of coupons"""
        coupons = generate_coupon_codes_image(self.bulk_order, count=25)
        
        self.assertEqual(len(coupons), 25)
        self.assertEqual(ImageCouponCode.objects.filter(bulk_order=self.bulk_order).count(), 25)

    def test_generated_codes_are_unique(self):
        """Test that all generated codes are unique"""
        coupons = generate_coupon_codes_image(self.bulk_order, count=50)
        
        codes = [c.code for c in coupons]
        self.assertEqual(len(codes), len(set(codes)))

    def test_generated_codes_format(self):
        """Test that generated codes have correct format"""
        coupons = generate_coupon_codes_image(self.bulk_order, count=5)
        
        for coupon in coupons:
            self.assertEqual(len(coupon.code), 8)
            self.assertTrue(coupon.code.isupper())
            self.assertTrue(coupon.code.isalnum())

    def test_codes_belong_to_correct_bulk_order(self):
        """Test that generated codes are associated with correct bulk order"""
        coupons = generate_coupon_codes_image(self.bulk_order, count=10)
        
        for coupon in coupons:
            self.assertEqual(coupon.bulk_order, self.bulk_order)

    def test_all_codes_initially_unused(self):
        """Test that generated codes are initially unused"""
        coupons = generate_coupon_codes_image(self.bulk_order, count=10)
        
        for coupon in coupons:
            self.assertFalse(coupon.is_used)


class GetImageBulkOrderWithOrdersTest(TestCase):
    """Test _get_image_bulk_order_with_orders helper function"""

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

    def test_get_by_slug(self):
        """Test retrieving bulk order by slug"""
        result = _get_image_bulk_order_with_orders(self.bulk_order.slug)
        
        self.assertEqual(result.id, self.bulk_order.id)

    def test_get_by_instance(self):
        """Test retrieving bulk order by instance"""
        result = _get_image_bulk_order_with_orders(self.bulk_order)
        
        self.assertEqual(result.id, self.bulk_order.id)

    def test_prefetch_includes_orders(self):
        """Test that orders are prefetched"""
        # Create orders
        ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='test1@example.com',
            full_name='User 1',
            size='L',
            paid=True
        )
        
        result = _get_image_bulk_order_with_orders(self.bulk_order.slug)
        
        # Access orders (should not cause additional query due to prefetch)
        with self.assertNumQueries(0):
            orders_list = list(result.orders.all())
            self.assertEqual(len(orders_list), 1)

    def test_orders_filtered_by_paid_or_coupon(self):
        """Test that only paid orders or those with coupons are included"""
        # Create paid order
        paid_order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='paid@example.com',
            full_name='Paid User',
            size='L',
            paid=True
        )
        
        # Create unpaid order without coupon
        unpaid_order = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='unpaid@example.com',
            full_name='Unpaid User',
            size='M'
        )
        
        result = _get_image_bulk_order_with_orders(self.bulk_order)
        orders = list(result.orders.all())
        
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].id, paid_order.id)

    def test_orders_sorted_by_size_then_name(self):
        """Test that orders are sorted correctly"""
        # Create orders with different sizes and names
        order_l1 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='l-user@example.com',
            full_name='Alpha User',
            size='L',
            paid=True
        )
        
        order_l2 = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='l-user2@example.com',
            full_name='Zebra User',
            size='L',
            paid=True
        )
        
        order_m = ImageOrderEntry.objects.create(
            bulk_order=self.bulk_order,
            email='m-user@example.com',
            full_name='Beta User',
            size='M',
            paid=True
        )
        
        result = _get_image_bulk_order_with_orders(self.bulk_order)
        orders = list(result.orders.all())
        
        # Verify we have all 3 orders
        self.assertEqual(len(orders), 3)
        
        # Within same size, should be sorted by name
        l_orders = [o for o in orders if o.size == 'L']
        self.assertEqual(len(l_orders), 2)
        self.assertEqual(l_orders[0].full_name, 'Alpha User')
        self.assertEqual(l_orders[1].full_name, 'Zebra User')


class GenerateImageBulkOrderPDFTest(TestCase):
    """Test generate_image_bulk_order_pdf function"""

    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='PDF Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )

    @patch('weasyprint.HTML')
    def test_generate_pdf_returns_response(self, mock_html):
        """Test that PDF generation returns HttpResponse"""
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_html_instance
        
        response = generate_image_bulk_order_pdf(self.bulk_order)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    @patch('weasyprint.HTML')
    def test_pdf_filename_includes_slug(self, mock_html):
        """Test that PDF filename includes bulk order slug"""
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b'fake pdf'
        mock_html.return_value = mock_html_instance
        
        response = generate_image_bulk_order_pdf(self.bulk_order)
        
        self.assertIn(self.bulk_order.slug, response['Content-Disposition'])

    @patch('weasyprint.HTML')
    def test_pdf_with_request_context(self, mock_html):
        """Test PDF generation with request context"""
        mock_html_instance = Mock()
        mock_html_instance.write_pdf.return_value = b'fake pdf'
        mock_html.return_value = mock_html_instance
        
        request = self.factory.get('/')
        response = generate_image_bulk_order_pdf(self.bulk_order, request)
        
        self.assertIsNotNone(response)
        mock_html.assert_called_once()


class GenerateImageBulkOrderWordTest(TestCase):
    """Test generate_image_bulk_order_word function"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Word Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )

    @patch('docx.Document')
    def test_generate_word_returns_response(self, mock_document):
        """Test that Word generation returns HttpResponse"""
        # Mock Document with proper structure to avoid subscript errors
        mock_doc = Mock()
        mock_table = Mock()
        mock_rows = Mock()
        mock_row = Mock()
        mock_cells = [Mock(), Mock(), Mock(), Mock(), Mock()]
        
        mock_row.cells = mock_cells
        mock_rows.__getitem__ = Mock(return_value=mock_row)
        mock_table.rows = mock_rows
        mock_doc.add_table.return_value = mock_table
        mock_doc.add_paragraph.return_value = Mock()
        mock_doc.save = Mock()
        
        mock_document.return_value = mock_doc
        
        response = generate_image_bulk_order_word(self.bulk_order)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('application', response['Content-Type'])

    @patch('docx.Document')
    def test_word_filename_includes_slug(self, mock_document):
        """Test that Word filename includes bulk order slug"""
        # Mock Document with proper structure to avoid subscript errors
        mock_doc = Mock()
        mock_table = Mock()
        mock_rows = Mock()
        mock_row = Mock()
        mock_cells = [Mock(), Mock(), Mock(), Mock(), Mock()]
        
        mock_row.cells = mock_cells
        mock_rows.__getitem__ = Mock(return_value=mock_row)
        mock_table.rows = mock_rows
        mock_doc.add_table.return_value = mock_table
        mock_doc.add_paragraph.return_value = Mock()
        mock_doc.save = Mock()
        
        mock_document.return_value = mock_doc
        
        response = generate_image_bulk_order_word(self.bulk_order)
        
        self.assertIn(self.bulk_order.slug, response['Content-Disposition'])


class GenerateImageBulkOrderExcelTest(TestCase):
    """Test generate_image_bulk_order_excel function"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Excel Test',
            price_per_item=Decimal('5000.00'),
            custom_branding_enabled=True,
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )

    @patch('xlsxwriter.Workbook')
    def test_generate_excel_returns_response(self, mock_workbook):
        """Test that Excel generation returns HttpResponse"""
        response = generate_image_bulk_order_excel(self.bulk_order)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('spreadsheetml', response['Content-Type'])

    @patch('xlsxwriter.Workbook')
    def test_excel_filename_includes_slug(self, mock_workbook):
        """Test that Excel filename includes bulk order slug"""
        response = generate_image_bulk_order_excel(self.bulk_order)
        
        self.assertIn(self.bulk_order.slug, response['Content-Disposition'])


class DownloadImageFromCloudinaryTest(TestCase):
    """Test download_image_from_cloudinary function"""

    @patch('image_bulk_orders.utils.requests.get')
    def test_download_success(self, mock_get):
        """Test successful image download"""
        mock_response = Mock()
        mock_response.content = b'fake image content'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = download_image_from_cloudinary('https://cloudinary.com/image.jpg')
        
        self.assertEqual(result, b'fake image content')

    @patch('image_bulk_orders.utils.requests.get')
    def test_download_failure(self, mock_get):
        """Test failed image download"""
        mock_get.side_effect = Exception('Network error')
        
        result = download_image_from_cloudinary('https://cloudinary.com/image.jpg')
        
        self.assertIsNone(result)


class GenerateAdminPackageWithImagesTest(TestCase):
    """Test generate_admin_package_with_images function"""

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.bulk_order = ImageBulkOrderLink.objects.create(
            organization_name='Package Test',
            price_per_item=Decimal('5000.00'),
            payment_deadline=timezone.now() + timedelta(days=30),
            created_by=self.user
        )

    @patch('image_bulk_orders.utils.generate_image_bulk_order_pdf')
    @patch('image_bulk_orders.utils.generate_image_bulk_order_word')
    @patch('image_bulk_orders.utils.generate_image_bulk_order_excel')
    @patch('image_bulk_orders.utils.download_image_from_cloudinary')
    def test_package_generation(self, mock_download, mock_excel, mock_word, mock_pdf):
        """Test complete package generation"""
        # Mock responses
        mock_pdf_response = Mock()
        mock_pdf_response.content = b'fake pdf'
        mock_pdf.return_value = mock_pdf_response
        
        mock_word_response = Mock()
        mock_word_response.content = b'fake docx'
        mock_word.return_value = mock_word_response
        
        mock_excel_response = Mock()
        mock_excel_response.content = b'fake xlsx'
        mock_excel.return_value = mock_excel_response
        
        response = generate_admin_package_with_images(self.bulk_order.id)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/zip', response['Content-Type'])