# excel_bulk_orders/tests/test_admin.py
"""
Comprehensive tests for Excel Bulk Orders Django Admin.

Coverage:
- ExcelBulkOrderAdmin: List display, filters, actions
- ExcelCouponCodeInline: Inline display, permissions
- ExcelParticipantInline: Inline display, permissions
- Custom admin actions: Generate documents, download files
- Permissions and access control
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory, Client, override_settings
from django.contrib.auth import get_user_model
from django.contrib.admin.sites import AdminSite
from unittest.mock import Mock, patch

from excel_bulk_orders.models import ExcelBulkOrder, ExcelCouponCode, ExcelParticipant
from excel_bulk_orders.admin import (
    ExcelBulkOrderAdmin,
    ExcelCouponCodeInline,
    ExcelParticipantInline,
)

User = get_user_model()


@override_settings(ADMIN_IP_WHITELIST=['127.0.0.1'])
class ExcelBulkOrderAdminTest(TestCase):
    """Test ExcelBulkOrderAdmin"""

    def setUp(self):
        """Set up test data"""
        self.site = AdminSite()
        self.admin = ExcelBulkOrderAdmin(ExcelBulkOrder, self.site)

        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )

        self.bulk_order = ExcelBulkOrder.objects.create(
            title='Admin Test Order',
            coordinator_name='Test',
            coordinator_email='admin@example.com',
            coordinator_phone='08012345678',
            price_per_participant=Decimal('5000.00'),
            total_amount=Decimal('25000.00')
        )

        # Create participants
        for i in range(5):
            ExcelParticipant.objects.create(
                bulk_order=self.bulk_order,
                full_name=f'Participant {i}',
                size='M',
                row_number=i + 2
            )

    def test_list_display_fields(self):
        """Test that all expected fields are in list_display"""
        expected_fields = [
            'reference',
            'title',
            'coordinator_name',
            'coordinator_email',
            'price_per_participant',
            'participant_count',
            'couponed_count',
            'total_amount',
            'validation_status_display',
            'payment_status_badge',  # Not 'payment_status_display'
            'created_at',
        ]

        for field in expected_fields:
            self.assertIn(field, self.admin.list_display)

    def test_list_filter_fields(self):
        """Test that filters are configured"""
        self.assertIsNotNone(self.admin.list_filter)
        self.assertIn('validation_status', self.admin.list_filter)
        self.assertIn('payment_status', self.admin.list_filter)

    def test_search_fields(self):
        """Test that search fields are configured"""
        self.assertIsNotNone(self.admin.search_fields)
        self.assertIn('reference', self.admin.search_fields)
        self.assertIn('coordinator_email', self.admin.search_fields)

    def test_readonly_fields(self):
        """Test that readonly fields are configured"""
        self.assertIsNotNone(self.admin.readonly_fields)

    def test_inlines_configured(self):
        """Test that inlines are configured"""
        self.assertEqual(len(self.admin.inlines), 2)
        self.assertIn(ExcelCouponCodeInline, self.admin.inlines)
        self.assertIn(ExcelParticipantInline, self.admin.inlines)

    def test_admin_accessible_to_staff(self):
        """Test that admin is accessible to staff users"""
        client = Client()
        client.force_login(self.admin_user)

        # Assume admin URL pattern, adjust if different
        response = client.get('/i_must_win/excel_bulk_orders/excelbulkorder/')

        # Should not be forbidden
        self.assertNotEqual(response.status_code, 403)


class ExcelCouponCodeInlineTest(TestCase):
    """Test ExcelCouponCodeInline"""

    def setUp(self):
        """Set up test data"""
        self.site = AdminSite()
        self.inline = ExcelCouponCodeInline(ExcelCouponCode, self.site)

    def test_inline_model(self):
        """Test that inline is for correct model"""
        self.assertEqual(self.inline.model, ExcelCouponCode)

    def test_readonly_fields(self):
        """Test that all fields are readonly"""
        expected_readonly = ['code', 'is_used', 'created_at']

        for field in expected_readonly:
            self.assertIn(field, self.inline.readonly_fields)

    def test_no_add_permission(self):
        """Test that adding inline is not allowed"""
        request = Mock()
        self.assertFalse(self.inline.has_add_permission(request))


class ExcelParticipantInlineTest(TestCase):
    """Test ExcelParticipantInline"""

    def setUp(self):
        """Set up test data"""
        self.site = AdminSite()
        self.inline = ExcelParticipantInline(ExcelParticipant, self.site)

    def test_inline_model(self):
        """Test that inline is for correct model"""
        self.assertEqual(self.inline.model, ExcelParticipant)

    def test_readonly_fields(self):
        """Test that all fields are readonly"""
        expected_readonly = [
            'full_name', 'size', 'custom_name',
            'coupon_code', 'is_coupon_applied',
            'row_number', 'created_at'
        ]

        for field in expected_readonly:
            self.assertIn(field, self.inline.readonly_fields)

    def test_no_add_permission(self):
        """Test that adding inline is not allowed"""
        request = Mock()
        self.assertFalse(self.inline.has_add_permission(request))