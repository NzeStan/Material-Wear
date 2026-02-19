# orderitem_generation/tests/tests_admin.py
"""
Comprehensive tests for OrderItem Generation Admin Functionality

Coverage:
- OrderItemGenerationAdminMixin: URL generation, PDF view, redirects
- Helper Functions: get_nysc_kit_pdf_context, get_nysc_tour_pdf_context, get_church_pdf_context
- Integration with Order Admins: NyscKitOrderAdmin, NyscTourOrderAdmin, ChurchOrderAdmin
- Form rendering and validation
- PDF generation through admin interface
- Error handling
- Permission checks
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory, Client
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.urls import reverse
from django.http import QueryDict
from unittest.mock import Mock, patch, MagicMock
import json

from order.models import NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem, BaseOrder
from products.models import Category, NyscKit, NyscTour, Church
from orderitem_generation.admin import (
    OrderItemGenerationAdminMixin,
    get_nysc_kit_pdf_context,
    get_nysc_tour_pdf_context,
    get_church_pdf_context,
)

# Import the actual admin classes that use the mixin
from order.admin import NyscKitOrderAdmin, NyscTourOrderAdmin, ChurchOrderAdmin

User = get_user_model()


class MockRequest:
    """Mock request object for admin tests"""

    def __init__(self, user=None):
        self.user = user
        self.GET = QueryDict("", mutable=True)
        self.POST = QueryDict("", mutable=True)
        self.method = "GET"
        self.META = {}


class OrderItemGenerationAdminMixinTests(TestCase):
    """Test the OrderItemGenerationAdminMixin functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )

        # Create test admin instance using NyscKitOrderAdmin
        self.admin = NyscKitOrderAdmin(NyscKitOrder, self.site)

        self.factory = RequestFactory()
        self.client = Client()
        self.client.force_login(self.admin_user)

    def test_mixin_change_list_template(self):
        """Test mixin sets custom changelist template"""
        self.assertEqual(
            self.admin.change_list_template,
            "orderitem_generation/admin_changelist.html",
        )

    def test_mixin_adds_custom_url(self):
        """Test mixin adds generate-pdf URL to admin"""
        urls = self.admin.get_urls()
        url_names = [url.name for url in urls if hasattr(url, "name")]

        # Check that the custom URL was added
        self.assertIn("order_nysckitorder_generate_pdf", url_names)

    def test_custom_url_pattern(self):
        """Test custom URL pattern is correct"""
        urls = self.admin.get_urls()
        generate_pdf_url = None

        for url in urls:
            if hasattr(url, "name") and url.name == "order_nysckitorder_generate_pdf":
                generate_pdf_url = url
                break

        self.assertIsNotNone(generate_pdf_url)
        # URL pattern should be 'generate-pdf/'
        self.assertEqual(str(generate_pdf_url.pattern), "generate-pdf/")

    def test_get_pdf_context_not_implemented(self):
        """Test get_pdf_context raises NotImplementedError if not overridden"""

        # Create a minimal mixin instance without get_pdf_context implementation
        class BadAdmin(OrderItemGenerationAdminMixin, type("MockAdmin", (), {})):
            model = NyscKitOrder

        bad_admin = BadAdmin()
        request = MockRequest()

        with self.assertRaises(NotImplementedError):
            bad_admin.get_pdf_context(request)

    def test_redirect_to_changelist(self):
        """Test _redirect_to_changelist helper method"""
        request = self.factory.get("/admin/order/nysckitorder/")
        request.user = self.admin_user

        response = self.admin._redirect_to_changelist(request)

        # Should redirect to changelist
        self.assertEqual(response.status_code, 302)
        # Check redirect contains model path (admin prefix may be custom like /i_must_win/)
        self.assertIn("order/nysckitorder/", response.url)


class GeneratePDFViewGetTests(TestCase):
    """Test generate_pdf_view GET requests (form display)"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )

        self.client = Client()
        self.client.force_login(self.admin_user)

        # Create test data
        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_get_request_shows_form(self):
        """Test GET request displays PDF generation form"""
        # Create order so we have states to select
        NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            state="Lagos",
            local_government="Ikeja",
            call_up_number="LA/23A/1234",
            total_cost=Decimal("25000.00"),
            paid=True,
        )

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Generate NYSC Kit Orders PDF", response.content)
        self.assertIn(b"Lagos", response.content)  # State should be in dropdown

    def test_form_contains_required_elements(self):
        """Test form has all required elements"""
        NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            state="Lagos",
            local_government="Ikeja",
            call_up_number="LA/23A/1234",
            total_cost=Decimal("25000.00"),
            paid=True,
        )

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.get(url)

        content = response.content.decode()

        # Check for form elements
        self.assertIn('method="post"', content)
        self.assertIn('name="pdf_type"', content)
        self.assertIn('value="nysc_kit"', content)
        self.assertIn('name="filter_value"', content)
        self.assertIn('type="submit"', content)


class GeneratePDFViewPostTests(TestCase):
    """Test generate_pdf_view POST requests (PDF generation)"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )

        self.client = Client()
        self.client.force_login(self.admin_user)

        # Create test data
        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @patch("orderitem_generation.api_views.HTML")
    @patch("orderitem_generation.api_views.upload_pdf_to_cloudinary")
    def test_post_request_generates_pdf(self, mock_cloudinary, mock_html):
        """Test POST request generates PDF successfully"""
        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b"fake pdf content"
        mock_html.return_value = mock_pdf
        mock_cloudinary.return_value = "https://cloudinary.com/fake-url.pdf"

        # Create order with items
        order = NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            state="Lagos",
            local_government="Ikeja",
            call_up_number="LA/23A/1234",
            total_cost=Decimal("25000.00"),
            paid=True,
        )

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.post(
            url, {"filter_value": "Lagos", "pdf_type": "nysc_kit"}
        )

        # Should return PDF
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_post_without_filter_value_shows_error(self):
        """Test POST without filter_value shows error message"""
        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.post(
            url,
            {
                "pdf_type": "nysc_kit"
                # Missing filter_value
            },
        )

        # Should redirect back to changelist
        self.assertEqual(response.status_code, 302)

        # Check error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn("Please select a filter value", str(messages[0]))

    @patch("orderitem_generation.api_views.HTML")
    @patch("orderitem_generation.api_views.upload_pdf_to_cloudinary")
    def test_post_with_no_orders_shows_error(self, mock_cloudinary, mock_html):
        """Test POST with no matching orders shows error"""
        # Don't create any orders

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.post(
            url, {"filter_value": "Lagos", "pdf_type": "nysc_kit"}
        )

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        self.assertIn("No orders found", str(messages[0]))

    def test_post_with_invalid_pdf_type(self):
        """Test POST with invalid pdf_type shows error"""
        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.post(
            url, {"filter_value": "Lagos", "pdf_type": "invalid_type"}
        )

        # Should redirect with error
        self.assertEqual(response.status_code, 302)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        self.assertIn("Invalid PDF type", str(messages[0]))


class GetNyscKitPDFContextTests(TestCase):
    """Test get_nysc_kit_pdf_context helper function"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
        )

        self.admin_instance = NyscKitOrderAdmin(NyscKitOrder, self.site)
        self.request = MockRequest(user=self.admin_user)

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_returns_correct_structure(self):
        """Test function returns correctly structured context"""
        # Create order
        NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            state="Lagos",
            local_government="Ikeja",
            call_up_number="LA/23A/1234",
            total_cost=Decimal("25000.00"),
            paid=True,
        )

        context = get_nysc_kit_pdf_context(self.admin_instance, self.request)

        # Check structure
        self.assertIn("title", context)
        self.assertIn("pdf_type", context)
        self.assertIn("filter_label", context)
        self.assertIn("filter_choices", context)
        self.assertIn("opts", context)

        # Check values
        self.assertEqual(context["title"], "Generate NYSC Kit Orders PDF")
        self.assertEqual(context["pdf_type"], "nysc_kit")
        self.assertEqual(context["filter_label"], "Select State")

    def test_includes_only_states_with_paid_orders(self):
        """Test only states with paid orders are included"""
        # Create paid order in Lagos
        NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            state="Lagos",
            local_government="Ikeja",
            call_up_number="LA/23A/1234",
            total_cost=Decimal("25000.00"),
            paid=True,
        )

        # Create unpaid order in Abuja
        NyscKitOrder.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            middle_name="Test",
            email="jane@example.com",
            phone_number="08087654321",
            state="Abuja",
            local_government="Gwagwalada",
            call_up_number="AB/23A/5678",
            total_cost=Decimal("25000.00"),
            paid=False,
        )

        context = get_nysc_kit_pdf_context(self.admin_instance, self.request)

        states = [choice[0] for choice in context["filter_choices"]]

        # Only Lagos should be included
        self.assertIn("Lagos", states)
        self.assertNotIn("Abuja", states)

    def test_handles_multiple_states(self):
        """Test function handles multiple states correctly"""
        # Create orders in multiple states
        for state in ["Lagos", "Abuja", "Rivers"]:
            NyscKitOrder.objects.create(
                user=self.user,
                first_name="John",
                last_name="Doe",
                middle_name="Test",
                email="john@example.com",
                phone_number="08012345678",
                state=state,
                local_government="Test LGA",
                call_up_number=f"{state[:2].upper()}/23A/1234",
                total_cost=Decimal("25000.00"),
                paid=True,
            )

        context = get_nysc_kit_pdf_context(self.admin_instance, self.request)

        states = [choice[0] for choice in context["filter_choices"]]

        self.assertEqual(len(states), 3)
        self.assertIn("Lagos", states)
        self.assertIn("Abuja", states)
        self.assertIn("Rivers", states)

    def test_states_are_ordered(self):
        """Test states are returned in alphabetical order"""
        # Create orders in random order
        for state in ["Rivers", "Abuja", "Lagos"]:
            NyscKitOrder.objects.create(
                user=self.user,
                first_name="John",
                last_name="Doe",
                middle_name="Test",
                email="john@example.com",
                phone_number="08012345678",
                state=state,
                local_government="Test LGA",
                call_up_number=f"{state[:2].upper()}/23A/1234",
                total_cost=Decimal("25000.00"),
                paid=True,
            )

        context = get_nysc_kit_pdf_context(self.admin_instance, self.request)

        states = [choice[0] for choice in context["filter_choices"]]

        # Should be alphabetically ordered
        self.assertEqual(states, ["Abuja", "Lagos", "Rivers"])

    def test_empty_database_returns_empty_choices(self):
        """Test function with no orders returns empty choices"""
        context = get_nysc_kit_pdf_context(self.admin_instance, self.request)

        self.assertEqual(len(context["filter_choices"]), 0)


class GetNyscTourPDFContextTests(TestCase):
    """Test get_nysc_tour_pdf_context helper function"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
        )

        self.admin_instance = NyscTourOrderAdmin(NyscTourOrder, self.site)
        self.request = MockRequest(user=self.admin_user)

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.category = Category.objects.create(
            name="NYSC TOURS", slug="nysc-tours", product_type="nysc_tour"
        )

    def test_returns_correct_structure(self):
        """Test function returns correctly structured context"""
        # Create tour product
        tour = NyscTour.objects.create(
            name="Lagos",  # NyscTour uses 'name' for state
            category=self.category,
            price=Decimal("15000.00"),
            available=True,
        )

        # Create order
        order = NyscTourOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("15000.00"),
            paid=True,
        )

        # Create order item
        tour_ct = ContentType.objects.get_for_model(NyscTour)
        OrderItem.objects.create(
            order=order,
            content_type=tour_ct,
            object_id=tour.id,
            price=Decimal("15000.00"),
            quantity=1,
        )

        context = get_nysc_tour_pdf_context(self.admin_instance, self.request)

        # Check structure
        self.assertIn("title", context)
        self.assertIn("pdf_type", context)
        self.assertIn("filter_label", context)
        self.assertIn("filter_choices", context)

        # Check values
        self.assertEqual(context["title"], "Generate NYSC Tour Orders PDF")
        self.assertEqual(context["pdf_type"], "nysc_tour")
        self.assertEqual(context["filter_label"], "Select State")

    def test_gets_states_from_tour_products(self):
        """Test function gets states from NyscTour product names"""
        # Create tour products in different states
        for state in ["Lagos", "Abuja"]:
            tour = NyscTour.objects.create(
                name=state,  # NyscTour uses 'name' for state
                category=self.category,
                price=Decimal("15000.00"),
                available=True,
            )

            order = NyscTourOrder.objects.create(
                user=self.user,
                first_name="John",
                last_name="Doe",
                middle_name="Test",
                email="john@example.com",
                phone_number="08012345678",
                total_cost=Decimal("15000.00"),
                paid=True,
            )

            tour_ct = ContentType.objects.get_for_model(NyscTour)
            OrderItem.objects.create(
                order=order,
                content_type=tour_ct,
                object_id=tour.id,
                price=Decimal("15000.00"),
                quantity=1,
            )

        context = get_nysc_tour_pdf_context(self.admin_instance, self.request)

        states = [choice[0] for choice in context["filter_choices"]]

        self.assertIn("Lagos", states)
        self.assertIn("Abuja", states)

    def test_only_includes_paid_orders(self):
        """Test only tour products with paid orders are included"""
        # Create tour with paid order
        tour1 = NyscTour.objects.create(
            name="Lagos",
            category=self.category,
            price=Decimal("15000.00"),
            available=True,
        )

        order1 = NyscTourOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("15000.00"),
            paid=True,
        )

        tour_ct = ContentType.objects.get_for_model(NyscTour)
        OrderItem.objects.create(
            order=order1,
            content_type=tour_ct,
            object_id=tour1.id,
            price=Decimal("15000.00"),
            quantity=1,
        )

        # Create tour with unpaid order
        tour2 = NyscTour.objects.create(
            name="Abuja",
            category=self.category,
            price=Decimal("15000.00"),
            available=True,
        )

        order2 = NyscTourOrder.objects.create(
            user=self.user,
            first_name="Jane",
            last_name="Smith",
            middle_name="Test",
            email="jane@example.com",
            phone_number="08087654321",
            total_cost=Decimal("15000.00"),
            paid=False,
        )

        OrderItem.objects.create(
            order=order2,
            content_type=tour_ct,
            object_id=tour2.id,
            price=Decimal("15000.00"),
            quantity=1,
        )

        context = get_nysc_tour_pdf_context(self.admin_instance, self.request)

        states = [choice[0] for choice in context["filter_choices"]]

        # Only Lagos should be included
        self.assertIn("Lagos", states)
        self.assertNotIn("Abuja", states)


class GetChurchPDFContextTests(TestCase):
    """Test get_church_pdf_context helper function"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
        )

        self.admin_instance = ChurchOrderAdmin(ChurchOrder, self.site)
        self.request = MockRequest(user=self.admin_user)

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        self.category = Category.objects.create(
            name="CHURCH PROGRAMME", slug="church-prog", product_type="church"
        )

    def test_returns_correct_structure(self):
        """Test function returns correctly structured context"""
        # Create church product
        church_product = Church.objects.create(
            name="Winners Men Jacket",
            church="WINNERS",
            category=self.category,
            price=Decimal("8000.00"),
            available=True,
        )

        # Create order
        order = ChurchOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("8000.00"),
            paid=True,
            pickup_on_camp=True,
        )

        # Create order item
        church_ct = ContentType.objects.get_for_model(Church)
        OrderItem.objects.create(
            order=order,
            content_type=church_ct,
            object_id=church_product.id,
            price=Decimal("8000.00"),
            quantity=1,
        )

        context = get_church_pdf_context(self.admin_instance, self.request)

        # Check structure
        self.assertIn("title", context)
        self.assertIn("pdf_type", context)
        self.assertIn("filter_label", context)
        self.assertIn("filter_choices", context)

        # Check values
        self.assertEqual(context["title"], "Generate Church Orders PDF")
        self.assertEqual(context["pdf_type"], "church")
        self.assertEqual(context["filter_label"], "Select Church")

    def test_gets_churches_from_church_products(self):
        """Test function gets churches from Church product church field"""
        # Create church products
        for church in ["WINNERS", "RCCG"]:
            church_product = Church.objects.create(
                name=f"{church} Product",
                church=church,
                category=self.category,
                price=Decimal("8000.00"),
                available=True,
            )

            order = ChurchOrder.objects.create(
                user=self.user,
                first_name="John",
                last_name="Doe",
                middle_name="Test",
                email="john@example.com",
                phone_number="08012345678",
                total_cost=Decimal("8000.00"),
                paid=True,
                pickup_on_camp=True,
            )

            church_ct = ContentType.objects.get_for_model(Church)
            OrderItem.objects.create(
                order=order,
                content_type=church_ct,
                object_id=church_product.id,
                price=Decimal("8000.00"),
                quantity=1,
            )

        context = get_church_pdf_context(self.admin_instance, self.request)

        churches = [choice[0] for choice in context["filter_choices"]]

        self.assertIn("WINNERS", churches)
        self.assertIn("RCCG", churches)

    def test_filter_choices_include_display_names(self):
        """Test filter choices include proper display names from CHURCH_CHOICES"""
        # Create church product
        church_product = Church.objects.create(
            name="Winners Product",
            church="WINNERS",
            category=self.category,
            price=Decimal("8000.00"),
            available=True,
        )

        order = ChurchOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            total_cost=Decimal("8000.00"),
            paid=True,
            pickup_on_camp=True,
        )

        church_ct = ContentType.objects.get_for_model(Church)
        OrderItem.objects.create(
            order=order,
            content_type=church_ct,
            object_id=church_product.id,
            price=Decimal("8000.00"),
            quantity=1,
        )

        context = get_church_pdf_context(self.admin_instance, self.request)

        # filter_choices should be list of tuples (value, display)
        self.assertTrue(
            all(
                isinstance(choice, tuple) and len(choice) == 2
                for choice in context["filter_choices"]
            )
        )


class AdminIntegrationTests(TestCase):
    """Test integration with actual Order admin classes"""

    def setUp(self):
        """Set up test fixtures"""
        self.site = AdminSite()
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )

        self.client = Client()
        self.client.force_login(self.admin_user)

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_nysckit_order_admin_uses_mixin(self):
        """Test NyscKitOrderAdmin properly uses the mixin"""
        admin = NyscKitOrderAdmin(NyscKitOrder, self.site)

        # Should have mixin's template
        self.assertEqual(
            admin.change_list_template, "orderitem_generation/admin_changelist.html"
        )

        # Should have get_pdf_context method
        self.assertTrue(hasattr(admin, "get_pdf_context"))

    def test_nysctour_order_admin_uses_mixin(self):
        """Test NyscTourOrderAdmin properly uses the mixin"""
        admin = NyscTourOrderAdmin(NyscTourOrder, self.site)

        self.assertEqual(
            admin.change_list_template, "orderitem_generation/admin_changelist.html"
        )

        self.assertTrue(hasattr(admin, "get_pdf_context"))

    def test_church_order_admin_uses_mixin(self):
        """Test ChurchOrderAdmin properly uses the mixin"""
        admin = ChurchOrderAdmin(ChurchOrder, self.site)

        self.assertEqual(
            admin.change_list_template, "orderitem_generation/admin_changelist.html"
        )

        self.assertTrue(hasattr(admin, "get_pdf_context"))

    def test_changelist_page_has_generate_pdf_button(self):
        """Test changelist page includes Generate PDF button"""
        url = reverse("admin:order_nysckitorder_changelist")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check for PDF generation button
        self.assertIn(b"Generate PDF Report", response.content)


class PermissionTests(TestCase):
    """Test permission requirements for PDF generation"""

    def setUp(self):
        """Set up test fixtures"""
        # Create regular user (non-staff)
        self.regular_user = User.objects.create_user(
            username="regular",
            email="regular@example.com",
            password="regular123",
            is_staff=False,
        )

        # Create staff user
        self.staff_user = User.objects.create_user(
            username="staff",
            email="staff@example.com",
            password="staff123",
            is_staff=True,
        )

        self.client = Client()

    def test_regular_user_cannot_access_generate_pdf_view(self):
        """Test regular users cannot access PDF generation"""
        self.client.force_login(self.regular_user)

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.get(url)

        # Should redirect to login or show 403
        self.assertIn(response.status_code, [302, 403])

    def test_staff_user_can_access_generate_pdf_view(self):
        """Test staff users can access PDF generation"""
        self.client.force_login(self.staff_user)

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.get(url)

        # Should show form
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_cannot_access(self):
        """Test anonymous users are redirected"""
        # Don't login

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.get(url)

        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        # Check that redirect URL contains login (admin prefix may vary)
        self.assertIn("/login/", response.url)


class ErrorHandlingTests(TestCase):
    """Test error handling in admin PDF generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )

        self.client = Client()
        self.client.force_login(self.admin_user)

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    @patch("orderitem_generation.admin.logger")
    @patch("orderitem_generation.api_views.HTML")
    def test_pdf_generation_exception_is_caught(self, mock_html, mock_logger):
        """Test exceptions during PDF generation are caught and logged"""
        # Mock HTML to raise exception
        mock_html.side_effect = Exception("PDF generation failed")

        # Create order
        NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            state="Lagos",
            local_government="Ikeja",
            call_up_number="LA/23A/1234",
            total_cost=Decimal("25000.00"),
            paid=True,
        )

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.post(
            url, {"filter_value": "Lagos", "pdf_type": "nysc_kit"}
        )

        # Should redirect with error message
        self.assertEqual(response.status_code, 302)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(len(messages) > 0)
        self.assertIn("Error generating PDF", str(messages[0]))

        # Error should be logged
        mock_logger.error.assert_called()


class EdgeCaseTests(TestCase):
    """Test edge cases in admin PDF generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
            is_superuser=True,
        )

        self.client = Client()
        self.client.force_login(self.admin_user)

        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_duplicate_states_are_deduplicated(self):
        """Test duplicate states in orders are deduplicated"""
        # Create multiple orders in same state
        for i in range(3):
            NyscKitOrder.objects.create(
                user=self.user,
                first_name=f"John{i}",
                last_name="Doe",
                middle_name="Test",
                email=f"john{i}@example.com",
                phone_number="08012345678",
                state="Lagos",
                local_government="Ikeja",
                call_up_number=f"LA/23A/123{i}",
                total_cost=Decimal("25000.00"),
                paid=True,
            )

        site = AdminSite()
        admin_instance = NyscKitOrderAdmin(NyscKitOrder, site)
        request = MockRequest(user=self.admin_user)

        context = get_nysc_kit_pdf_context(admin_instance, request)

        # Lagos should appear only once
        states = [choice[0] for choice in context["filter_choices"]]
        self.assertEqual(states.count("Lagos"), 1)

    def test_special_characters_in_state_names(self):
        """Test state names with special characters are handled"""
        # Create order with state containing space
        NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            state="Cross River",  # Contains space
            local_government="Calabar Municipal",
            call_up_number="CR/23A/1234",
            total_cost=Decimal("25000.00"),
            paid=True,
        )

        site = AdminSite()
        admin_instance = NyscKitOrderAdmin(NyscKitOrder, site)
        request = MockRequest(user=self.admin_user)

        context = get_nysc_kit_pdf_context(admin_instance, request)

        states = [choice[0] for choice in context["filter_choices"]]
        self.assertIn("Cross River", states)

    @patch("orderitem_generation.api_views.HTML")
    @patch("orderitem_generation.api_views.upload_pdf_to_cloudinary")
    def test_cloudinary_upload_failure_still_returns_pdf(
        self, mock_cloudinary, mock_html
    ):
        """Test PDF is still returned even if Cloudinary upload fails"""
        # Mock Cloudinary to return None (upload failed)
        mock_cloudinary.return_value = None

        # Mock PDF generation
        mock_pdf = MagicMock()
        mock_pdf.write_pdf.return_value = b"fake pdf content"
        mock_html.return_value = mock_pdf

        # Create order
        NyscKitOrder.objects.create(
            user=self.user,
            first_name="John",
            last_name="Doe",
            middle_name="Test",
            email="john@example.com",
            phone_number="08012345678",
            state="Lagos",
            local_government="Ikeja",
            call_up_number="LA/23A/1234",
            total_cost=Decimal("25000.00"),
            paid=True,
        )

        url = reverse("admin:order_nysckitorder_generate_pdf")
        response = self.client.post(
            url, {"filter_value": "Lagos", "pdf_type": "nysc_kit"}
        )

        # Should still return PDF successfully
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # X-Cloudinary-URL header should not be present
        self.assertNotIn("X-Cloudinary-URL", response)
