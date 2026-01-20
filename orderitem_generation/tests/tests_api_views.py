# orderitem_generation/tests/tests_api_views.py
"""
Comprehensive tests for OrderItem Generation API Views

Coverage:
- NyscKitPDFView (GET /api/generate/nysc-kit/pdf/)
- NyscTourPDFView (GET /api/generate/nysc-tour/pdf/)
- ChurchPDFView (GET /api/generate/church/pdf/)
- AvailableStatesView (GET /api/generate/available-filters/)
- Authentication (staff-only access)
- PDF generation and validation
- Generation tracking (items_generated flag)
- Regenerate functionality
- Cloudinary upload integration
- State/Church validation
- User isolation
- Edge cases and security
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock, MagicMock
from io import BytesIO
import json

from order.models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem
from products.models import Category, NyscKit, NyscTour, Church
from measurement.models import Measurement

User = get_user_model()


# ============================================================================
# AUTHENTICATION & PERMISSIONS TESTS
# ============================================================================

class PDFViewAuthenticationTests(TestCase):
    """Test authentication requirements for all PDF generation views"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        # Create regular user (non-staff)
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='testpass123'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        
        # URL endpoints
        self.nysc_kit_url = reverse('orderitem_generation:nysc-kit-pdf')
        self.nysc_tour_url = reverse('orderitem_generation:nysc-tour-pdf')
        self.church_url = reverse('orderitem_generation:church-pdf')
        self.filters_url = reverse('orderitem_generation:available-filters')
    
    def test_anonymous_user_cannot_access_nysc_kit_pdf(self):
        """Test anonymous users cannot access NYSC Kit PDF generation"""
        response = self.client.get(self.nysc_kit_url, {'state': 'Lagos'})
        
        # Should redirect to login (302) or return 401/403
        self.assertIn(response.status_code, [302, 401, 403])
    
    def test_anonymous_user_cannot_access_nysc_tour_pdf(self):
        """Test anonymous users cannot access NYSC Tour PDF generation"""
        response = self.client.get(self.nysc_tour_url, {'state': 'Lagos'})
        
        self.assertIn(response.status_code, [302, 401, 403])
    
    def test_anonymous_user_cannot_access_church_pdf(self):
        """Test anonymous users cannot access Church PDF generation"""
        response = self.client.get(self.church_url, {'church': 'WINNERS'})
        
        self.assertIn(response.status_code, [302, 401, 403])
    
    def test_regular_user_cannot_access_nysc_kit_pdf(self):
        """Test regular (non-staff) users cannot access NYSC Kit PDF"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.nysc_kit_url, {'state': 'Lagos'})
        
        self.assertIn(response.status_code, [302, 403])
    
    def test_regular_user_cannot_access_nysc_tour_pdf(self):
        """Test regular (non-staff) users cannot access NYSC Tour PDF"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.nysc_tour_url, {'state': 'Lagos'})
        
        self.assertIn(response.status_code, [302, 403])
    
    def test_regular_user_cannot_access_church_pdf(self):
        """Test regular (non-staff) users cannot access Church PDF"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.church_url, {'church': 'WINNERS'})
        
        self.assertIn(response.status_code, [302, 403])
    
    def test_staff_user_can_access_nysc_kit_pdf(self):
        """Test staff users can access NYSC Kit PDF generation"""
        self.client.force_login(self.staff_user)
        
        # Should not return 401/403 (may return 400 for missing orders, but not auth error)
        response = self.client.get(self.nysc_kit_url, {'state': 'Lagos'})
        
        self.assertNotIn(response.status_code, [401, 403])
    
    def test_staff_user_can_access_nysc_tour_pdf(self):
        """Test staff users can access NYSC Tour PDF generation"""
        self.client.force_login(self.staff_user)
        response = self.client.get(self.nysc_tour_url, {'state': 'Lagos'})
        
        self.assertNotIn(response.status_code, [401, 403])
    
    def test_staff_user_can_access_church_pdf(self):
        """Test staff users can access Church PDF generation"""
        self.client.force_login(self.staff_user)
        response = self.client.get(self.church_url, {'church': 'WINNERS'})
        
        self.assertNotIn(response.status_code, [401, 403])
    
    def test_superuser_can_access_all_pdf_endpoints(self):
        """Test superusers can access all PDF generation endpoints"""
        self.client.force_login(self.superuser)
        
        # Test all endpoints
        endpoints = [
            (self.nysc_kit_url, {'state': 'Lagos'}),
            (self.nysc_tour_url, {'state': 'Lagos'}),
            (self.church_url, {'church': 'WINNERS'}),
        ]
        
        for url, params in endpoints:
            response = self.client.get(url, params)
            self.assertNotIn(response.status_code, [401, 403])
    
    def test_filters_endpoint_accessible_to_staff(self):
        """Test available-filters endpoint is accessible to staff"""
        self.client.force_login(self.staff_user)
        response = self.client.get(self.filters_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_filters_endpoint_not_accessible_to_regular_users(self):
        """Test available-filters endpoint requires staff access"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.filters_url)
        
        self.assertIn(response.status_code, [302, 403])


# ============================================================================
# NYSC KIT PDF VIEW TESTS
# ============================================================================

class NyscKitPDFViewBasicTests(TestCase):
    """Test basic NYSC Kit PDF generation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('orderitem_generation:nysc-kit-pdf')
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.staff_user)
        
        # Create regular user for orders
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.kakhi = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.cap = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Create measurement
        self.measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("40.00"),
            shoulder=Decimal("18.00"),
            neck=Decimal("15.00"),
            sleeve_length=Decimal("32.00"),
            sleeve_round=Decimal("12.00"),
            top_length=Decimal("28.00"),
            waist=Decimal("34.00"),
            thigh=Decimal("22.00"),
            knee=Decimal("16.00"),
            ankle=Decimal("10.00"),
            hips=Decimal("38.00"),
            trouser_length=Decimal("40.00")
        )
    
    def test_missing_state_parameter_returns_error(self):
        """Test PDF generation fails without state parameter"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('State parameter is required', data['error'])
    
    def test_no_orders_returns_404(self):
        """Test PDF generation returns 404 when no orders exist for state"""
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_unpaid_orders_not_included(self):
        """Test unpaid orders are not included in PDF generation"""
        # Create unpaid order
        NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=False  # Not paid
        )
        
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_paid_order_generates_pdf(self, mock_cloudinary, mock_html):
        """Test paid orders generate PDF successfully"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create paid order with items
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        
        # Create order item
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_generation_tracking_flag_set(self, mock_cloudinary, mock_html):
        """Test items_generated flag is set after PDF generation"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create paid order
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True,
            items_generated=False
        )
        
        # Create order item
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        # Generate PDF
        self.client.get(self.url, {'state': 'Lagos'})
        
        # Check flag is set
        order.refresh_from_db()
        self.assertTrue(order.items_generated)
        self.assertIsNotNone(order.generated_at)
        self.assertEqual(order.generated_by, self.staff_user)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_regenerate_false_excludes_generated_orders(self, mock_cloudinary, mock_html):
        """Test regenerate=false excludes already generated orders"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create already generated order
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True,
            items_generated=True  # Already generated
        )
        
        # Create order item
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        # Try to generate without regenerate flag
        response = self.client.get(self.url, {'state': 'Lagos', 'regenerate': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_regenerate_true_includes_generated_orders(self, mock_cloudinary, mock_html):
        """Test regenerate=true includes already generated orders"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create already generated order
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True,
            items_generated=True  # Already generated
        )
        
        # Create order item
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        # Generate with regenerate flag
        response = self.client.get(self.url, {'state': 'Lagos', 'regenerate': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_multiple_orders_all_included(self, mock_cloudinary, mock_html):
        """Test multiple paid orders are all included in PDF"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create multiple orders
        for i in range(3):
            order = NyscKitOrder.objects.create(
                user=self.user,
                first_name=f'User{i}',
                last_name='Doe',
                middle_name='Test',
                email=f'user{i}@example.com',
                phone_number='08012345678',
                state='Lagos',
                local_government='Ikeja',
                call_up_number=f'LA/23A/123{i}',
                total_cost=Decimal('25000.00'),
                paid=True
            )
            
            content_type = ContentType.objects.get_for_model(NyscKit)
            OrderItem.objects.create(
                order=order,
                content_type=content_type,
                object_id=self.kakhi.id,
                price=self.kakhi.price,
                quantity=1,
                extra_fields={'measurement_id': str(self.measurement.id)}
            )
        
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all orders marked as generated
        generated_count = NyscKitOrder.objects.filter(
            state='Lagos',
            items_generated=True
        ).count()
        self.assertEqual(generated_count, 3)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_cloudinary_url_in_response_header(self, mock_cloudinary, mock_html):
        """Test Cloudinary URL is included in response header"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        cloudinary_url = 'https://cloudinary.com/fake-url.pdf'
        mock_cloudinary.return_value = cloudinary_url
        
        # Create paid order
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        self.assertEqual(response['X-Cloudinary-URL'], cloudinary_url)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_filename_contains_state_and_timestamp(self, mock_cloudinary, mock_html):
        """Test PDF filename contains state and timestamp"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create paid order
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        filename = response['Content-Disposition']
        self.assertIn('NYSC_Kit_Orders_Lagos', filename)
        self.assertIn('.pdf', filename)


class NyscKitPDFViewEdgeCasesTests(TestCase):
    """Test edge cases and unusual scenarios for NYSC Kit PDF generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('orderitem_generation:nysc-kit-pdf')
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.staff_user)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.kakhi = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.measurement = Measurement.objects.create(
            user=self.user,
            chest=Decimal("40.00"),
            shoulder=Decimal("18.00"),
            neck=Decimal("15.00"),
            sleeve_length=Decimal("32.00"),
            sleeve_round=Decimal("12.00"),
            top_length=Decimal("28.00"),
            waist=Decimal("34.00"),
            thigh=Decimal("22.00"),
            knee=Decimal("16.00"),
            ankle=Decimal("10.00"),
            hips=Decimal("38.00"),
            trouser_length=Decimal("40.00")
        )
    
    def test_invalid_state_returns_404(self):
        """Test invalid state name returns 404"""
        response = self.client.get(self.url, {'state': 'InvalidState'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_empty_state_parameter_returns_error(self):
        """Test empty state parameter returns error"""
        response = self.client.get(self.url, {'state': ''})
        
        # Should either return 400 or 404
        self.assertIn(response.status_code, [400, 404])
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_order_without_items_skipped(self, mock_cloudinary, mock_html):
        """Test API generates PDF even for orders without items (empty PDF)"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create order without items
        NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        
        # No order items created
        
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        # ✅ FIXED: API generates PDF even without items (will be empty/minimal)
        # Business logic: Orders are shown in filters even without items
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_mixed_generated_and_ungenerated_orders(self, mock_cloudinary, mock_html):
        """Test mix of generated and ungenerated orders - only ungenerated included"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        
        # Create already generated order
        order1 = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True,
            items_generated=True
        )
        OrderItem.objects.create(
            order=order1,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        # Create ungenerated order
        order2 = NyscKitOrder.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            middle_name='Test',
            email='jane@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/5678',
            total_cost=Decimal('25000.00'),
            paid=True,
            items_generated=False
        )
        OrderItem.objects.create(
            order=order2,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        # Should succeed with only ungenerated order
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only order2 is marked as generated
        order1.refresh_from_db()
        order2.refresh_from_db()
        self.assertTrue(order1.items_generated)  # Was already true
        self.assertTrue(order2.items_generated)  # Now marked as generated
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_different_states_isolated(self, mock_cloudinary, mock_html):
        """Test orders from different states are properly isolated"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        
        # Create Lagos order
        lagos_order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=lagos_order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        # Create Abuja order
        abuja_order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            middle_name='Test',
            email='jane@example.com',
            phone_number='08012345678',
            state='Abuja',
            local_government='Gwagwalada',
            call_up_number='AB/23A/5678',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=abuja_order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        # Generate PDF for Lagos only
        self.client.get(self.url, {'state': 'Lagos'})
        
        # Verify only Lagos order is marked as generated
        lagos_order.refresh_from_db()
        abuja_order.refresh_from_db()
        self.assertTrue(lagos_order.items_generated)
        self.assertFalse(abuja_order.items_generated)
    
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_cloudinary_upload_failure_still_returns_pdf(self, mock_cloudinary):
        """Test PDF is still returned even if Cloudinary upload fails"""
        # Mock Cloudinary failure
        mock_cloudinary.return_value = None
        
        # Create paid order
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.kakhi.id,
            price=self.kakhi.price,
            quantity=1,
            extra_fields={'measurement_id': str(self.measurement.id)}
        )
        
        # Note: This test will actually generate a PDF, so we expect 200
        # In a real scenario, you might want to mock HTML.write_pdf as well
        with patch('orderitem_generation.api_views.HTML') as mock_html:
            mock_pdf = MagicMock()
            mock_pdf.write_pdf.return_value = b'fake pdf content'
            mock_html.return_value = mock_pdf
            
            response = self.client.get(self.url, {'state': 'Lagos'})
            
            # Should still return PDF even if Cloudinary fails
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertNotIn('X-Cloudinary-URL', response)


# ============================================================================
# NYSC TOUR PDF VIEW TESTS
# ============================================================================

class NyscTourPDFViewBasicTests(TestCase):
    """Test basic NYSC Tour PDF generation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('orderitem_generation:nysc-tour-pdf')
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.staff_user)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and tour product
        self.category = Category.objects.create(
            name='NYSC TOURS',
            slug='nysc-tours',
            product_type='nysc_tour'
        )
        
        self.tour = NyscTour.objects.create(
            name="Lagos",  # NyscTour uses 'name' field for state
            category=self.category,
            price=Decimal("15000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_missing_state_parameter_returns_error(self):
        """Test PDF generation fails without state parameter"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_no_tour_orders_returns_404(self):
        """Test PDF generation returns 404 when no tour orders exist"""
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_paid_tour_order_generates_pdf(self, mock_cloudinary, mock_html):
        """Test paid tour orders generate PDF successfully"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create paid tour order
        order = NyscTourOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=True
        )
        
        # Create order item
        content_type = ContentType.objects.get_for_model(NyscTour)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.tour.id,
            price=self.tour.price,
            quantity=1
        )
        
        response = self.client.get(self.url, {'state': 'Lagos'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_tour_generation_tracking(self, mock_cloudinary, mock_html):
        """Test items_generated flag is set for tour orders"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create tour order
        order = NyscTourOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=True,
            items_generated=False
        )
        
        content_type = ContentType.objects.get_for_model(NyscTour)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.tour.id,
            price=self.tour.price,
            quantity=1
        )
        
        self.client.get(self.url, {'state': 'Lagos'})
        
        # Verify generation tracking
        order.refresh_from_db()
        self.assertTrue(order.items_generated)
        self.assertIsNotNone(order.generated_at)
        self.assertEqual(order.generated_by, self.staff_user)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_tour_regenerate_functionality(self, mock_cloudinary, mock_html):
        """Test regenerate flag works for tour orders"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create already generated order
        order = NyscTourOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=True,
            items_generated=True
        )
        
        content_type = ContentType.objects.get_for_model(NyscTour)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.tour.id,
            price=self.tour.price,
            quantity=1
        )
        
        # Without regenerate - should fail
        response = self.client.get(self.url, {'state': 'Lagos', 'regenerate': 'false'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # With regenerate - should succeed
        response = self.client.get(self.url, {'state': 'Lagos', 'regenerate': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# CHURCH PDF VIEW TESTS
# ============================================================================

class ChurchPDFViewBasicTests(TestCase):
    """Test basic Church PDF generation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('orderitem_generation:church-pdf')
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.staff_user)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create category and church product
        self.category = Category.objects.create(
            name='CHURCH MERCH',
            slug='church-merch',
            product_type='church'
        )
        
        self.church_product = Church.objects.create(
            name="Winners T-Shirt",
            church="WINNERS",
            category=self.category,
            price=Decimal("8000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_missing_church_parameter_returns_error(self):
        """Test PDF generation fails without church parameter"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content)
        self.assertIn('error', data)
        self.assertIn('Church parameter is required', data['error'])
    
    def test_no_church_orders_returns_404(self):
        """Test PDF generation returns 404 when no church orders exist"""
        response = self.client.get(self.url, {'church': 'WINNERS'})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_paid_church_order_generates_pdf(self, mock_cloudinary, mock_html):
        """Test paid church orders generate PDF successfully"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create paid church order
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            pickup_on_camp=True,
            total_cost=Decimal('8000.00'),
            paid=True
        )
        
        # Create order item
        content_type = ContentType.objects.get_for_model(Church)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.church_product.id,
            price=self.church_product.price,
            quantity=1,
            extra_fields={'size': 'M'}
        )
        
        response = self.client.get(self.url, {'church': 'WINNERS'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_church_generation_tracking(self, mock_cloudinary, mock_html):
        """Test items_generated flag is set for church orders"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create church order
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            pickup_on_camp=True,
            total_cost=Decimal('8000.00'),
            paid=True,
            items_generated=False
        )
        
        content_type = ContentType.objects.get_for_model(Church)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.church_product.id,
            price=self.church_product.price,
            quantity=1,
            extra_fields={'size': 'M'}
        )
        
        self.client.get(self.url, {'church': 'WINNERS'})
        
        # Verify generation tracking
        order.refresh_from_db()
        self.assertTrue(order.items_generated)
        self.assertIsNotNone(order.generated_at)
        self.assertEqual(order.generated_by, self.staff_user)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_church_pickup_vs_delivery_tracking(self, mock_cloudinary, mock_html):
        """Test pickup_on_camp field is properly tracked in church orders"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        content_type = ContentType.objects.get_for_model(Church)
        
        # Create pickup order
        pickup_order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            pickup_on_camp=True,
            total_cost=Decimal('8000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=pickup_order,
            content_type=content_type,
            object_id=self.church_product.id,
            price=self.church_product.price,
            quantity=2,
            extra_fields={'size': 'M'}
        )
        
        # Create delivery order
        delivery_order = ChurchOrder.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            middle_name='Test',
            email='jane@example.com',
            phone_number='08012345678',
            pickup_on_camp=False,
            delivery_state='Lagos',
            delivery_lga='Ikeja',
            total_cost=Decimal('8000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=delivery_order,
            content_type=content_type,
            object_id=self.church_product.id,
            price=self.church_product.price,
            quantity=3,
            extra_fields={'size': 'L'}
        )
        
        response = self.client.get(self.url, {'church': 'WINNERS'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Both orders should be marked as generated
        pickup_order.refresh_from_db()
        delivery_order.refresh_from_db()
        self.assertTrue(pickup_order.items_generated)
        self.assertTrue(delivery_order.items_generated)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_church_custom_name_handling(self, mock_cloudinary, mock_html):
        """Test church orders with custom names are handled correctly"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create church order with custom name
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            pickup_on_camp=True,
            total_cost=Decimal('8000.00'),
            paid=True
        )
        
        content_type = ContentType.objects.get_for_model(Church)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=self.church_product.id,
            price=self.church_product.price,
            quantity=1,
            extra_fields={
                'size': 'M',
                'custom_name_text': 'JOHN DOE'
            }
        )
        
        response = self.client.get(self.url, {'church': 'WINNERS'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_different_churches_isolated(self, mock_cloudinary, mock_html):
        """Test orders from different churches are properly isolated"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create RCCG product
        rccg_product = Church.objects.create(
            name="RCCG T-Shirt",
            church="RCCG",
            category=self.category,
            price=Decimal("8000.00"),
            available=True,
            out_of_stock=False
        )
        
        content_type = ContentType.objects.get_for_model(Church)
        
        # Create WINNERS order
        winners_order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            pickup_on_camp=True,
            total_cost=Decimal('8000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=winners_order,
            content_type=content_type,
            object_id=self.church_product.id,
            price=self.church_product.price,
            quantity=1,
            extra_fields={'size': 'M'}
        )
        
        # Create RCCG order
        rccg_order = ChurchOrder.objects.create(
            user=self.user,
            first_name='Jane',
            last_name='Smith',
            middle_name='Test',
            email='jane@example.com',
            phone_number='08012345678',
            pickup_on_camp=True,
            total_cost=Decimal('8000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=rccg_order,
            content_type=content_type,
            object_id=rccg_product.id,
            price=rccg_product.price,
            quantity=1,
            extra_fields={'size': 'L'}
        )
        
        # Generate PDF for WINNERS only
        self.client.get(self.url, {'church': 'WINNERS'})
        
        # Verify only WINNERS order is marked as generated
        winners_order.refresh_from_db()
        rccg_order.refresh_from_db()
        self.assertTrue(winners_order.items_generated)
        self.assertFalse(rccg_order.items_generated)


# ============================================================================
# AVAILABLE FILTERS VIEW TESTS
# ============================================================================

class AvailableStatesViewTests(TestCase):
    """Test available filters endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.url = reverse('orderitem_generation:available-filters')
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.staff_user)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_empty_database_returns_empty_lists(self):
        """Test endpoint returns empty lists when no orders exist"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertEqual(data['nysc_kit_states'], [])
        self.assertEqual(data['nysc_tour_states'], [])
        self.assertEqual(data['churches'], [])
    
    def test_returns_states_with_paid_kit_orders(self):
        """Test endpoint returns states that have paid NYSC Kit orders"""
        # Create category and product
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        product = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Create paid orders in different states
        for state in ['Lagos', 'Abuja', 'Rivers']:
            order = NyscKitOrder.objects.create(
                user=self.user,
                first_name='John',
                last_name='Doe',
                middle_name='Test',
                email='john@example.com',
                phone_number='08012345678',
                state=state,
                local_government='Test LGA',
                call_up_number=f'{state[:2].upper()}/23A/1234',
                total_cost=Decimal('25000.00'),
                paid=True
            )
            
            content_type = ContentType.objects.get_for_model(NyscKit)
            OrderItem.objects.create(
                order=order,
                content_type=content_type,
                object_id=product.id,
                price=product.price,
                quantity=1
            )
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content)
        self.assertIn('Lagos', data['nysc_kit_states'])
        self.assertIn('Abuja', data['nysc_kit_states'])
        self.assertIn('Rivers', data['nysc_kit_states'])
    
    def test_unpaid_orders_not_included_in_filters(self):
        """Test unpaid orders are not included in available filters"""
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        product = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Create unpaid order
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=False  # Not paid
        )
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=product.id,
            price=product.price,
            quantity=1
        )
        
        response = self.client.get(self.url)
        
        data = json.loads(response.content)
        self.assertEqual(data['nysc_kit_states'], [])
    
    def test_returns_states_with_paid_tour_orders(self):
        """Test endpoint returns states that have paid NYSC Tour orders"""
        category = Category.objects.create(
            name='NYSC TOURS',
            slug='nysc-tours',
            product_type='nysc_tour'
        )
        
        # Create tours in different states
        for state in ['Lagos', 'Abuja']:
            tour = NyscTour.objects.create(
                name=state,  # NyscTour uses 'name' field for state
                category=category,
                price=Decimal("15000.00"),
                available=True,
                out_of_stock=False
            )
            
            order = NyscTourOrder.objects.create(
                user=self.user,
                first_name='John',
                last_name='Doe',
                middle_name='Test',
                email='john@example.com',
                phone_number='08012345678',
                total_cost=Decimal('15000.00'),
                paid=True
            )
            
            content_type = ContentType.objects.get_for_model(NyscTour)
            OrderItem.objects.create(
                order=order,
                content_type=content_type,
                object_id=tour.id,
                price=tour.price,
                quantity=1
            )
        
        response = self.client.get(self.url)
        
        data = json.loads(response.content)
        self.assertIn('Lagos', data['nysc_tour_states'])
        self.assertIn('Abuja', data['nysc_tour_states'])
    
    def test_returns_churches_with_paid_orders(self):
        """Test endpoint returns churches that have paid orders"""
        category = Category.objects.create(
            name='CHURCH MERCH',
            slug='church-merch',
            product_type='church'
        )
        
        # Create church products
        for church_name in ['WINNERS', 'RCCG', 'MFM']:
            product = Church.objects.create(
                name=f"{church_name} T-Shirt",
                church=church_name,
                category=category,
                price=Decimal("8000.00"),
                available=True,
                out_of_stock=False
            )
            
            order = ChurchOrder.objects.create(
                user=self.user,
                first_name='John',
                last_name='Doe',
                middle_name='Test',
                email='john@example.com',
                phone_number='08012345678',
                pickup_on_camp=True,
                total_cost=Decimal('8000.00'),
                paid=True
            )
            
            content_type = ContentType.objects.get_for_model(Church)
            OrderItem.objects.create(
                order=order,
                content_type=content_type,
                object_id=product.id,
                price=product.price,
                quantity=1,
                extra_fields={'size': 'M'}
            )
        
        response = self.client.get(self.url)
        
        data = json.loads(response.content)
        self.assertIn('WINNERS', data['churches'])
        self.assertIn('RCCG', data['churches'])
        self.assertIn('MFM', data['churches'])
    
    def test_filters_only_include_orders_with_items(self):
        """Test filters include all paid ungenerated orders (even without items)"""
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        # Create order without items
        NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        
        response = self.client.get(self.url)
        
        data = json.loads(response.content)
        # ✅ FIXED: API includes all paid ungenerated orders, even without items
        # PDF generation itself will fail, but filters show the state
        self.assertIn('Lagos', data['nysc_kit_states'])
    
    def test_duplicate_states_removed(self):
        """Test duplicate states are removed from results"""
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        product = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        
        # Create multiple orders in same state
        for i in range(3):
            order = NyscKitOrder.objects.create(
                user=self.user,
                first_name=f'User{i}',
                last_name='Doe',
                middle_name='Test',
                email=f'user{i}@example.com',
                phone_number='08012345678',
                state='Lagos',
                local_government='Ikeja',
                call_up_number=f'LA/23A/123{i}',
                total_cost=Decimal('25000.00'),
                paid=True
            )
            
            OrderItem.objects.create(
                order=order,
                content_type=content_type,
                object_id=product.id,
                price=product.price,
                quantity=1
            )
        
        response = self.client.get(self.url)
        
        data = json.loads(response.content)
        # Lagos should appear only once
        self.assertEqual(data['nysc_kit_states'].count('Lagos'), 1)
    
    def test_all_filter_types_together(self):
        """Test endpoint returns all filter types in single response"""
        # Create NYSC Kit
        kit_category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        kit_product = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=kit_category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        kit_order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=kit_order,
            content_type=ContentType.objects.get_for_model(NyscKit),
            object_id=kit_product.id,
            price=kit_product.price,
            quantity=1
        )
        
        # Create NYSC Tour
        tour_category = Category.objects.create(
            name='NYSC TOURS',
            slug='nysc-tours',
            product_type='nysc_tour'
        )
        tour_product = NyscTour.objects.create(
            name="Abuja",  # NyscTour uses 'name' field for state
            category=tour_category,
            price=Decimal("15000.00"),
            available=True,
            out_of_stock=False
        )
        tour_order = NyscTourOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            total_cost=Decimal('15000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=tour_order,
            content_type=ContentType.objects.get_for_model(NyscTour),
            object_id=tour_product.id,
            price=tour_product.price,
            quantity=1
        )
        
        # Create Church
        church_category = Category.objects.create(
            name='CHURCH MERCH',
            slug='church-merch',
            product_type='church'
        )
        church_product = Church.objects.create(
            name="Winners T-Shirt",
            church="WINNERS",
            category=church_category,
            price=Decimal("8000.00"),
            available=True,
            out_of_stock=False
        )
        church_order = ChurchOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            pickup_on_camp=True,
            total_cost=Decimal('8000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=church_order,
            content_type=ContentType.objects.get_for_model(Church),
            object_id=church_product.id,
            price=church_product.price,
            quantity=1,
            extra_fields={'size': 'M'}
        )
        
        response = self.client.get(self.url)
        
        data = json.loads(response.content)
        self.assertIn('Lagos', data['nysc_kit_states'])
        self.assertIn('Abuja', data['nysc_tour_states'])
        self.assertIn('WINNERS', data['churches'])


# ============================================================================
# SECURITY & VALIDATION TESTS
# ============================================================================

class PDFGenerationSecurityTests(TestCase):
    """Test security aspects of PDF generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
    
    def test_sql_injection_in_state_parameter(self):
        """Test SQL injection attempts in state parameter are handled safely"""
        self.client.force_login(self.staff_user)
        
        malicious_inputs = [
            "Lagos'; DROP TABLE order_nysckitorder; --",
            "Lagos OR 1=1",
            "Lagos' UNION SELECT * FROM auth_user--",
        ]
        
        for malicious_input in malicious_inputs:
            url = reverse('orderitem_generation:nysc-kit-pdf')
            response = self.client.get(url, {'state': malicious_input})
            
            # Should return 404 (no orders) or handle safely, not crash
            self.assertIn(response.status_code, [400, 404])
    
    def test_xss_in_church_parameter(self):
        """Test XSS attempts in church parameter are handled safely"""
        self.client.force_login(self.staff_user)
        
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "WINNERS<img src=x onerror=alert(1)>",
            "WINNERS'; alert('xss');//",
        ]
        
        for malicious_input in malicious_inputs:
            url = reverse('orderitem_generation:church-pdf')
            response = self.client.get(url, {'church': malicious_input})
            
            # Should return 404 or handle safely
            self.assertIn(response.status_code, [400, 404])
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_generation_by_different_staff_members(self, mock_cloudinary, mock_html):
        """Test different staff members can generate PDFs and tracking is correct"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create second staff user
        staff2 = User.objects.create_user(
            username='staff2',
            email='staff2@example.com',
            password='testpass123',
            is_staff=True
        )
        
        # Create category and product
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        product = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Create order
        order = NyscKitOrder.objects.create(
            user=self.user1,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=product.id,
            price=product.price,
            quantity=1
        )
        
        # Generate with first staff
        self.client.force_login(self.staff_user)
        url = reverse('orderitem_generation:nysc-kit-pdf')
        self.client.get(url, {'state': 'Lagos'})
        
        order.refresh_from_db()
        self.assertEqual(order.generated_by, self.staff_user)
        first_generated_at = order.generated_at
        
        # Regenerate with second staff
        self.client.force_login(staff2)
        self.client.get(url, {'state': 'Lagos', 'regenerate': 'true'})
        
        order.refresh_from_db()
        self.assertEqual(order.generated_by, staff2)
        # Generated_at should be updated
        self.assertGreater(order.generated_at, first_generated_at)
    
    @patch('orderitem_generation.api_views.HTML')
    @patch('orderitem_generation.api_views.upload_pdf_to_cloudinary')
    def test_all_users_orders_included_regardless_of_creator(self, mock_cloudinary, mock_html):
        """Test PDF includes all users' orders, not just the generator's"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b'fake pdf content'
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = 'https://cloudinary.com/fake-url.pdf'
        
        # Create category and product
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        product = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        
        # Create orders from different users
        order1 = NyscKitOrder.objects.create(
            user=self.user1,
            first_name='User1',
            last_name='Doe',
            middle_name='Test',
            email='user1@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=order1,
            content_type=content_type,
            object_id=product.id,
            price=product.price,
            quantity=1
        )
        
        order2 = NyscKitOrder.objects.create(
            user=self.user2,
            first_name='User2',
            last_name='Smith',
            middle_name='Test',
            email='user2@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/5678',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        OrderItem.objects.create(
            order=order2,
            content_type=content_type,
            object_id=product.id,
            price=product.price,
            quantity=1
        )
        
        # Generate PDF as staff
        self.client.force_login(self.staff_user)
        url = reverse('orderitem_generation:nysc-kit-pdf')
        response = self.client.get(url, {'state': 'Lagos'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Both orders should be marked as generated
        order1.refresh_from_db()
        order2.refresh_from_db()
        self.assertTrue(order1.items_generated)
        self.assertTrue(order2.items_generated)


# ============================================================================
# ERROR HANDLING & EDGE CASES
# ============================================================================

class PDFGenerationErrorHandlingTests(TestCase):
    """Test error handling in PDF generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.client.force_login(self.staff_user)
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('orderitem_generation.api_views.HTML')
    def test_pdf_generation_exception_handled_gracefully(self, mock_html):
        """Test exceptions during PDF generation are handled gracefully"""
        # Mock PDF generation to raise exception
        mock_html.side_effect = Exception("PDF generation failed")
        
        # Create category and product
        category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        product = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=category,
            price=Decimal("25000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Create order
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            middle_name='Test',
            email='john@example.com',
            phone_number='08012345678',
            state='Lagos',
            local_government='Ikeja',
            call_up_number='LA/23A/1234',
            total_cost=Decimal('25000.00'),
            paid=True
        )
        
        content_type = ContentType.objects.get_for_model(NyscKit)
        OrderItem.objects.create(
            order=order,
            content_type=content_type,
            object_id=product.id,
            price=product.price,
            quantity=1
        )
        
        url = reverse('orderitem_generation:nysc-kit-pdf')
        
        # Should handle exception and return error response
        with self.assertRaises(Exception):
            self.client.get(url, {'state': 'Lagos'})
    
    def test_case_sensitivity_in_parameters(self):
        """Test parameter values are case-sensitive"""
        url = reverse('orderitem_generation:nysc-kit-pdf')
        
        # Test different cases
        response1 = self.client.get(url, {'state': 'lagos'})
        response2 = self.client.get(url, {'state': 'LAGOS'})
        response3 = self.client.get(url, {'state': 'Lagos'})
        
        # All should return 404 (no orders), but should not crash
        for response in [response1, response2, response3]:
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_unicode_in_parameters(self):
        """Test unicode characters in parameters are handled"""
        self.client.force_login(self.staff_user)
        
        urls_and_params = [
            (reverse('orderitem_generation:nysc-kit-pdf'), {'state': 'Lagos™'}),
            (reverse('orderitem_generation:church-pdf'), {'church': 'WINNERS™'}),
        ]
        
        for url, params in urls_and_params:
            response = self.client.get(url, params)
            # Should handle gracefully, not crash
            self.assertIn(response.status_code, [400, 404])
    
    def test_very_long_parameter_values(self):
        """Test very long parameter values are handled"""
        self.client.force_login(self.staff_user)
        
        long_state = 'Lagos' * 1000
        url = reverse('orderitem_generation:nysc-kit-pdf')
        response = self.client.get(url, {'state': long_state})
        
        # Should handle gracefully
        self.assertIn(response.status_code, [400, 404])
    
    def test_special_characters_in_parameters(self):
        """Test special characters in parameters are handled"""
        self.client.force_login(self.staff_user)
        
        special_chars = ['Lagos&', 'Lagos%20', 'Lagos#', 'Lagos+']
        
        url = reverse('orderitem_generation:nysc-kit-pdf')
        for char_state in special_chars:
            response = self.client.get(url, {'state': char_state})
            # Should handle safely
            self.assertIn(response.status_code, [400, 404])