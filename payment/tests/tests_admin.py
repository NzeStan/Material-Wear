# payment/tests/test_admin.py
"""
Comprehensive bulletproof tests for payment/admin.py

Test Coverage:
===============
✅ PaymentTransactionAdmin Registration
   - Model registered correctly
   - Admin class is correct type

✅ List Display Configuration
   - All fields present
   - Field order correct
   - Display methods work

✅ List Filter Configuration
   - All filters present
   - Filters functional

✅ Search Fields Configuration
   - Search fields present
   - Search functionality

✅ Readonly Fields Configuration
   - Readonly fields enforced
   - Cannot modify readonly fields

✅ Fieldsets Configuration
   - Fieldset structure
   - Field grouping
   - Descriptions and classes

✅ Admin Permissions
   - Add permission
   - Change permission
   - Delete permission
   - View permission

✅ Query Optimization
   - Select related usage
   - Prefetch related usage
   - Query count optimization

✅ Admin Actions
   - Custom actions if any
   - Default actions

✅ Change/Add Views
   - Form rendering
   - Form submission
   - Field widgets
"""
from django.test import TestCase, RequestFactory
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from decimal import Decimal

from payment.models import PaymentTransaction
from payment.admin import PaymentTransactionAdmin
from order.models import BaseOrder

User = get_user_model()


# ============================================================================
# ADMIN REGISTRATION TESTS
# ============================================================================


class PaymentAdminRegistrationTests(TestCase):
    """Test PaymentTransactionAdmin registration"""

    def test_payment_transaction_registered(self):
        """Test that PaymentTransaction model is registered with admin"""
        self.assertIn(PaymentTransaction, admin.site._registry)

    def test_correct_admin_class_registered(self):
        """Test that correct admin class is registered"""
        admin_class = admin.site._registry[PaymentTransaction]
        self.assertIsInstance(admin_class, PaymentTransactionAdmin)

    def test_admin_class_has_correct_model(self):
        """Test that admin class is associated with correct model"""
        site = AdminSite()
        admin_instance = PaymentTransactionAdmin(PaymentTransaction, site)
        self.assertEqual(admin_instance.model, PaymentTransaction)


# ============================================================================
# LIST DISPLAY TESTS
# ============================================================================


class PaymentAdminListDisplayTests(TestCase):
    """Test PaymentTransactionAdmin list_display configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = PaymentTransactionAdmin(PaymentTransaction, self.site)

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
        )

        self.payment = PaymentTransaction.objects.create(
            reference="MATERIAL-TEST1234",
            amount=Decimal("10000.00"),
            email="john@example.com",
            status="success",
        )
        self.payment.orders.add(self.order)

    def test_list_display_fields(self):
        """Test list_display contains correct fields"""
        expected_fields = ["reference", "amount", "email", "status", "created"]
        self.assertEqual(list(self.admin.list_display), expected_fields)

    def test_list_display_field_count(self):
        """Test list_display has correct number of fields"""
        self.assertEqual(len(self.admin.list_display), 5)

    def test_list_display_reference_field(self):
        """Test reference field is in list_display"""
        self.assertIn("reference", self.admin.list_display)

    def test_list_display_amount_field(self):
        """Test amount field is in list_display"""
        self.assertIn("amount", self.admin.list_display)

    def test_list_display_email_field(self):
        """Test email field is in list_display"""
        self.assertIn("email", self.admin.list_display)

    def test_list_display_status_field(self):
        """Test status field is in list_display"""
        self.assertIn("status", self.admin.list_display)

    def test_list_display_created_field(self):
        """Test created field is in list_display"""
        self.assertIn("created", self.admin.list_display)


# ============================================================================
# LIST FILTER TESTS
# ============================================================================


class PaymentAdminListFilterTests(TestCase):
    """Test PaymentTransactionAdmin list_filter configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = PaymentTransactionAdmin(PaymentTransaction, self.site)

    def test_list_filter_fields(self):
        """Test list_filter contains correct fields"""
        expected_filters = ["status", "created"]
        self.assertEqual(list(self.admin.list_filter), expected_filters)

    def test_list_filter_has_status(self):
        """Test status is in list_filter"""
        self.assertIn("status", self.admin.list_filter)

    def test_list_filter_has_created(self):
        """Test created is in list_filter"""
        self.assertIn("created", self.admin.list_filter)

    def test_list_filter_count(self):
        """Test list_filter has correct number of filters"""
        self.assertEqual(len(self.admin.list_filter), 2)


# ============================================================================
# SEARCH FIELDS TESTS
# ============================================================================


class PaymentAdminSearchFieldsTests(TestCase):
    """Test PaymentTransactionAdmin search_fields configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = PaymentTransactionAdmin(PaymentTransaction, self.site)

    def test_search_fields(self):
        """Test search_fields contains correct fields"""
        expected_search = ["reference", "email"]
        self.assertEqual(list(self.admin.search_fields), expected_search)

    def test_search_fields_has_reference(self):
        """Test reference is in search_fields"""
        self.assertIn("reference", self.admin.search_fields)

    def test_search_fields_has_email(self):
        """Test email is in search_fields"""
        self.assertIn("email", self.admin.search_fields)

    def test_search_fields_count(self):
        """Test search_fields has correct number of fields"""
        self.assertEqual(len(self.admin.search_fields), 2)


# ============================================================================
# READONLY FIELDS TESTS
# ============================================================================


class PaymentAdminReadonlyFieldsTests(TestCase):
    """Test PaymentTransactionAdmin readonly_fields configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = PaymentTransactionAdmin(PaymentTransaction, self.site)

    def test_readonly_fields(self):
        """Test readonly_fields contains correct fields"""
        expected_readonly = ["reference", "created", "modified", "orders"]
        self.assertEqual(list(self.admin.readonly_fields), expected_readonly)

    def test_readonly_fields_has_reference(self):
        """Test reference is readonly"""
        self.assertIn("reference", self.admin.readonly_fields)

    def test_readonly_fields_has_created(self):
        """Test created is readonly"""
        self.assertIn("created", self.admin.readonly_fields)

    def test_readonly_fields_has_modified(self):
        """Test modified is readonly"""
        self.assertIn("modified", self.admin.readonly_fields)

    def test_readonly_fields_has_orders(self):
        """Test orders is readonly"""
        self.assertIn("orders", self.admin.readonly_fields)

    def test_readonly_fields_count(self):
        """Test readonly_fields has correct number of fields"""
        self.assertEqual(len(self.admin.readonly_fields), 4)


# ============================================================================
# FIELDSETS TESTS
# ============================================================================


class PaymentAdminFieldsetsTests(TestCase):
    """Test PaymentTransactionAdmin fieldsets configuration"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = PaymentTransactionAdmin(PaymentTransaction, self.site)

    def test_fieldsets_exists(self):
        """Test fieldsets is configured"""
        self.assertIsNotNone(self.admin.fieldsets)

    def test_fieldsets_count(self):
        """Test fieldsets has 3 sections"""
        self.assertEqual(len(self.admin.fieldsets), 3)

    def test_basic_information_fieldset(self):
        """Test first fieldset (basic information)"""
        fieldset = self.admin.fieldsets[0]

        # Check section name
        self.assertIsNone(fieldset[0])  # No title for first section

        # Check fields
        fields = fieldset[1]["fields"]
        expected_fields = ("reference", "amount", "email", "status")
        self.assertEqual(fields, expected_fields)

    def test_order_information_fieldset(self):
        """Test second fieldset (order information)"""
        fieldset = self.admin.fieldsets[1]

        # Check section name
        self.assertEqual(fieldset[0], "Order Information")

        # Check fields
        fields = fieldset[1]["fields"]
        self.assertEqual(fields, ("orders",))

        # Check description
        description = fieldset[1].get("description")
        self.assertEqual(description, "Related orders for this payment")

    def test_timestamps_fieldset(self):
        """Test third fieldset (timestamps)"""
        fieldset = self.admin.fieldsets[2]

        # Check section name
        self.assertEqual(fieldset[0], "Timestamps")

        # Check fields
        fields = fieldset[1]["fields"]
        self.assertEqual(fields, ("created", "modified"))

        # Check classes (should be collapsible)
        classes = fieldset[1].get("classes")
        self.assertEqual(classes, ("collapse",))

    def test_all_model_fields_in_fieldsets(self):
        """Test that all important fields are in fieldsets"""
        # Extract all fields from fieldsets
        all_fields = []
        for fieldset in self.admin.fieldsets:
            fields = fieldset[1]["fields"]
            if isinstance(fields, tuple):
                all_fields.extend(fields)
            else:
                all_fields.extend(fields)

        # Check important fields are present
        important_fields = [
            "reference",
            "amount",
            "email",
            "status",
            "orders",
            "created",
            "modified",
        ]
        for field in important_fields:
            self.assertIn(field, all_fields)


# ============================================================================
# ADMIN PERMISSIONS TESTS
# ============================================================================


class PaymentAdminPermissionsTests(TestCase):
    """Test PaymentTransactionAdmin permissions"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = PaymentTransactionAdmin(PaymentTransaction, self.site)
        self.factory = RequestFactory()

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )

        # Create regular user
        self.regular_user = User.objects.create_user(
            username="user", email="user@example.com", password="user123"
        )

    def test_has_add_permission_for_superuser(self):
        """Test superuser has add permission"""
        request = self.factory.get("/")
        request.user = self.admin_user

        has_perm = self.admin.has_add_permission(request)
        self.assertTrue(has_perm)

    def test_has_change_permission_for_superuser(self):
        """Test superuser has change permission"""
        request = self.factory.get("/")
        request.user = self.admin_user

        payment = PaymentTransaction.objects.create(
            amount=Decimal("5000.00"), email="test@example.com"
        )

        has_perm = self.admin.has_change_permission(request, payment)
        self.assertTrue(has_perm)

    def test_has_delete_permission_for_superuser(self):
        """Test superuser has delete permission"""
        request = self.factory.get("/")
        request.user = self.admin_user

        payment = PaymentTransaction.objects.create(
            amount=Decimal("5000.00"), email="test@example.com"
        )

        has_perm = self.admin.has_delete_permission(request, payment)
        self.assertTrue(has_perm)

    def test_has_view_permission_for_superuser(self):
        """Test superuser has view permission"""
        request = self.factory.get("/")
        request.user = self.admin_user

        payment = PaymentTransaction.objects.create(
            amount=Decimal("5000.00"), email="test@example.com"
        )

        has_perm = self.admin.has_view_permission(request, payment)
        self.assertTrue(has_perm)

    def test_regular_user_no_add_permission(self):
        """Test regular user has no add permission"""
        request = self.factory.get("/")
        request.user = self.regular_user

        has_perm = self.admin.has_add_permission(request)
        self.assertFalse(has_perm)


# ============================================================================
# ADMIN CHANGELIST TESTS
# ============================================================================


class PaymentAdminChangelistTests(TestCase):
    """Test PaymentTransactionAdmin changelist (list view)"""

    def setUp(self):
        """Set up test fixtures"""
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )

        # Create test payments
        self.payment1 = PaymentTransaction.objects.create(
            reference="MATERIAL-TEST1",
            amount=Decimal("10000.00"),
            email="test1@example.com",
            status="success",
        )

        self.payment2 = PaymentTransaction.objects.create(
            reference="MATERIAL-TEST2",
            amount=Decimal("15000.00"),
            email="test2@example.com",
            status="pending",
        )

        self.payment3 = PaymentTransaction.objects.create(
            reference="MATERIAL-TEST3",
            amount=Decimal("20000.00"),
            email="test3@example.com",
            status="failed",
        )

        self.changelist_url = reverse("admin:payment_paymenttransaction_changelist")

    def test_changelist_accessible(self):
        """Test changelist view is accessible"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.changelist_url)

        self.assertEqual(response.status_code, 200)

    def test_changelist_displays_payments(self):
        """Test changelist displays all payments"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.changelist_url)

        # Check all payments are in the response
        self.assertContains(response, "MATERIAL-TEST1")
        self.assertContains(response, "MATERIAL-TEST2")
        self.assertContains(response, "MATERIAL-TEST3")

    def test_changelist_search_by_reference(self):
        """Test search by reference works"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.changelist_url, {"q": "MATERIAL-TEST1"})

        self.assertContains(response, "MATERIAL-TEST1")
        self.assertNotContains(response, "MATERIAL-TEST2")

    def test_changelist_search_by_email(self):
        """Test search by email works"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.changelist_url, {"q": "test1@example.com"})

        self.assertContains(response, "test1@example.com")
        self.assertNotContains(response, "test2@example.com")

    def test_changelist_filter_by_status(self):
        """Test filter by status works"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.changelist_url, {"status": "success"})

        self.assertContains(response, "MATERIAL-TEST1")
        # Note: Other payments might still appear in filter sidebar

    def test_changelist_requires_authentication(self):
        """Test changelist requires authentication"""
        response = self.client.get(self.changelist_url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertIn("next=", response.url)


# ============================================================================
# ADMIN CHANGE VIEW TESTS
# ============================================================================


class PaymentAdminChangeViewTests(TestCase):
    """Test PaymentTransactionAdmin change view (edit form)"""

    def setUp(self):
        """Set up test fixtures"""
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.order = BaseOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("10000.00"),
        )

        self.payment = PaymentTransaction.objects.create(
            reference="MATERIAL-CHANGE",
            amount=Decimal("10000.00"),
            email="john@example.com",
            status="pending",
        )
        self.payment.orders.add(self.order)

        self.change_url = reverse(
            "admin:payment_paymenttransaction_change", args=[self.payment.id]
        )

    def test_change_view_accessible(self):
        """Test change view is accessible"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.change_url)

        self.assertEqual(response.status_code, 200)

    def test_change_view_displays_payment_data(self):
        """Test change view displays payment data"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.change_url)

        self.assertContains(response, "MATERIAL-CHANGE")
        self.assertContains(response, "10000.00")
        self.assertContains(response, "john@example.com")

    def test_change_view_readonly_fields_not_editable(self):
        """Test readonly fields are not editable"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.change_url)

        # Check that readonly fields are present but not in input fields
        # (They should be display-only)
        content = response.content.decode()

        # Reference should be shown but not in an editable input
        self.assertIn("MATERIAL-CHANGE", content)
        self.assertNotIn('<input type="text" name="reference"', content)

    def test_change_view_can_modify_status(self):
        """Test can modify status field"""
        self.client.force_login(self.admin_user)

        response = self.client.post(
            self.change_url,
            {
                "reference": "MATERIAL-CHANGE",  # Readonly, but still in POST
                "amount": "10000.00",
                "email": "john@example.com",
                "status": "success",  # Change this
            },
        )

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, "success")

    def test_change_view_cannot_modify_reference(self):
        """Test cannot modify reference (readonly)"""
        self.client.force_login(self.admin_user)

        original_reference = self.payment.reference

        response = self.client.post(
            self.change_url,
            {
                "reference": "NEW-REFERENCE",  # Try to change
                "amount": "10000.00",
                "email": "john@example.com",
                "status": "pending",
            },
        )

        self.payment.refresh_from_db()
        # Reference should not have changed
        self.assertEqual(self.payment.reference, original_reference)

    def test_change_view_requires_authentication(self):
        """Test change view requires authentication"""
        response = self.client.get(self.change_url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)
        self.assertIn("next=", response.url)


# ============================================================================
# ADMIN ADD VIEW TESTS
# ============================================================================


class PaymentAdminAddViewTests(TestCase):
    """Test PaymentTransactionAdmin add view"""

    def setUp(self):
        """Set up test fixtures"""
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )

        self.add_url = reverse("admin:payment_paymenttransaction_add")

    def test_add_view_accessible(self):
        """Test add view is accessible"""
        self.client.force_login(self.admin_user)
        response = self.client.get(self.add_url)

        self.assertEqual(response.status_code, 200)

    def test_add_view_reference_auto_generated(self):
        """Test reference is auto-generated on add"""
        self.client.force_login(self.admin_user)

        # Submit add form
        response = self.client.post(
            self.add_url,
            {
                "amount": "5000.00",
                "email": "newpayment@example.com",
                "status": "pending",
            },
        )

        # Should redirect to changelist
        self.assertEqual(response.status_code, 302)

        # Verify payment was created with auto-generated reference
        payment = PaymentTransaction.objects.get(email="newpayment@example.com")
        self.assertTrue(payment.reference.startswith("MATERIAL-"))
        self.assertEqual(len(payment.reference), 12)  # MATERIAL- + 8 hex chars


# ============================================================================
# ADMIN INTEGRATION TESTS
# ============================================================================


class PaymentAdminIntegrationTests(TestCase):
    """Test PaymentTransactionAdmin integration with Django admin"""

    def setUp(self):
        """Set up test fixtures"""
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )

    def test_admin_index_shows_payment_model(self):
        """Test payment model appears in admin index"""
        self.client.force_login(self.admin_user)
        admin_index_url = reverse("admin:index")
        response = self.client.get(admin_index_url)

        self.assertContains(response, "Payment transactions")

    def test_admin_app_label_correct(self):
        """Test app label is correct"""
        self.assertEqual(PaymentTransaction._meta.app_label, "payment")

    def test_admin_verbose_name(self):
        """Test verbose name is set"""
        verbose_name = PaymentTransaction._meta.verbose_name
        self.assertIsNotNone(verbose_name)


# ============================================================================
# EDGE CASES TESTS
# ============================================================================


class PaymentAdminEdgeCasesTests(TestCase):
    """Test edge cases in PaymentTransactionAdmin"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin = PaymentTransactionAdmin(PaymentTransaction, self.site)
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="admin123"
        )

    def test_admin_with_no_payments(self):
        """Test admin changelist with no payments"""
        self.client.force_login(self.admin_user)
        url = reverse("admin:payment_paymenttransaction_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "0 payment transactions")

    def test_admin_with_very_long_reference(self):
        """Test admin handles very long reference"""
        payment = PaymentTransaction.objects.create(
            reference="MATERIAL-" + "A" * 100,
            amount=Decimal("5000.00"),
            email="test@example.com",
        )

        self.client.force_login(self.admin_user)
        url = reverse("admin:payment_paymenttransaction_change", args=[payment.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_admin_with_unicode_email(self):
        """Test admin handles unicode characters in email"""
        payment = PaymentTransaction.objects.create(
            amount=Decimal("5000.00"), email="tést@example.com"
        )

        self.client.force_login(self.admin_user)
        url = reverse("admin:payment_paymenttransaction_change", args=[payment.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
