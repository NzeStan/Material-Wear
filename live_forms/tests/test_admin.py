# live_forms/tests/test_admin.py
"""
Comprehensive admin tests for live_forms app.

Tests:
  - LiveFormEntryAdminTest      : list display, custom_name_display, live_form_link,
                                  readonly enforcement, has_add_permission=False
  - LiveFormLinkAdminTest       : list display, shareable_link_display, expiry_status,
                                  entry_count_display, get_queryset annotation,
                                  download_pdf_action, download_word_action,
                                  download_excel_action, copy_link_action
  - IsExpiredFilterTest         : yes/no queryset filtering by expires_at
  - HasSubmissionsFilterTest    : yes/no queryset filtering by entry_count annotation
  - LiveFormEntryInlineTest     : has_add_permission=False, fields, readonly
"""
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db.models import Count
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone

from live_forms.admin import (
    HasSubmissionsFilter,
    IsExpiredFilter,
    LiveFormEntryAdmin,
    LiveFormEntryInline,
    LiveFormLinkAdmin,
    _build_shareable_url,
)
from live_forms.models import LiveFormEntry, LiveFormLink

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def future(hours=24):
    return timezone.now() + timedelta(hours=hours)


def past(hours=1):
    return timezone.now() - timedelta(hours=hours)


def make_user(username=None, staff=True):
    username = username or f"u_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(
        username=username, password="testpass", is_staff=staff, email=f"{username}@test.com"
    )


def make_form(user=None, **kwargs):
    user = user or make_user()
    defaults = dict(
        organization_name="Admin Test Org",
        expires_at=future(),
        is_active=True,
    )
    defaults.update(kwargs)
    return LiveFormLink.objects.create(created_by=user, **defaults)


def make_entry(form, **kwargs):
    defaults = dict(full_name="Admin Entry Person", size="M")
    defaults.update(kwargs)
    return LiveFormEntry.objects.create(live_form=form, **defaults)


def make_request(user=None):
    rf = RequestFactory()
    request = rf.get("/admin/")
    request.user = user or make_user()
    # Attach message storage so admin actions can use self.message_user
    setattr(request, "session", "session")
    messages = FallbackStorage(request)
    setattr(request, "_messages", messages)
    return request


# ===========================================================================
# _build_shareable_url helper
# ===========================================================================

class BuildShareableUrlTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)

    def test_relative_url_without_frontend_url(self):
        with self.settings(FRONTEND_URL=""):
            url = _build_shareable_url(self.form)
        self.assertIn(self.form.slug, url)
        self.assertIn("/live-form/", url)

    def test_absolute_url_with_frontend_url(self):
        with self.settings(FRONTEND_URL="https://materialwear.ng"):
            url = _build_shareable_url(self.form)
        self.assertTrue(url.startswith("https://materialwear.ng"))
        self.assertIn(self.form.slug, url)

    def test_no_double_slashes(self):
        with self.settings(FRONTEND_URL="https://materialwear.ng/"):
            url = _build_shareable_url(self.form)
        self.assertNotIn("//live-form", url)


# ===========================================================================
# LiveFormEntryAdmin
# ===========================================================================

class LiveFormEntryAdminTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin_obj = LiveFormEntryAdmin(LiveFormEntry, self.site)
        self.user = make_user()
        self.form = make_form(self.user, organization_name="Entry Admin Org")
        self.entry_no_custom = make_entry(self.form, full_name="No Custom", size="S")
        self.form_branded = make_form(
            self.user,
            organization_name="Branded Admin Org",
            custom_branding_enabled=True,
        )
        self.entry_branded = make_entry(
            self.form_branded,
            full_name="Branded Person",
            size="XL",
            custom_name="Gold Star",
        )

    # ── custom_name_display ─────────────────────────────────────────────

    def test_custom_name_display_shows_dash_when_branding_disabled(self):
        result = self.admin_obj.custom_name_display(self.entry_no_custom)
        self.assertEqual(result, "—")

    def test_custom_name_display_shows_name_when_branding_enabled(self):
        result = self.admin_obj.custom_name_display(self.entry_branded)
        self.assertEqual(result, "GOLD STAR")

    def test_custom_name_display_shows_dash_when_branding_enabled_but_empty(self):
        entry = make_entry(
            self.form_branded, full_name="Empty Custom", size="M", custom_name=""
        )
        result = self.admin_obj.custom_name_display(entry)
        self.assertEqual(result, "—")

    # ── live_form_link ──────────────────────────────────────────────────

    def test_live_form_link_returns_html_anchor(self):
        result = self.admin_obj.live_form_link(self.entry_no_custom)
        self.assertIn("<a", str(result))
        self.assertIn(self.form.organization_name, str(result))

    # ── has_add_permission ──────────────────────────────────────────────

    def test_has_add_permission_returns_false(self):
        request = make_request(self.user)
        self.assertFalse(self.admin_obj.has_add_permission(request))

    # ── readonly_fields ─────────────────────────────────────────────────

    def test_readonly_fields_contains_all_required(self):
        required = {"id", "serial_number", "live_form", "full_name", "custom_name",
                    "size", "created_at", "updated_at"}
        self.assertTrue(required.issubset(set(self.admin_obj.readonly_fields)))

    # ── list_display ────────────────────────────────────────────────────

    def test_list_display_contains_expected_fields(self):
        expected = {"serial_number", "full_name", "size", "created_at"}
        self.assertTrue(expected.issubset(set(self.admin_obj.list_display)))

    # ── search_fields ───────────────────────────────────────────────────

    def test_search_fields_include_full_name_and_org(self):
        self.assertIn("full_name", self.admin_obj.search_fields)
        self.assertIn("live_form__organization_name", self.admin_obj.search_fields)


# ===========================================================================
# LiveFormLinkAdmin
# ===========================================================================

class LiveFormLinkAdminTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin_obj = LiveFormLinkAdmin(LiveFormLink, self.site)
        self.user = make_user()
        self.form = make_form(self.user, organization_name="Link Admin Org")
        make_entry(self.form, full_name="Entry One", size="M")

    def _annotated_form(self):
        return LiveFormLink.objects.annotate(entry_count=Count("entries")).get(
            pk=self.form.pk
        )

    # ── shareable_link_display ──────────────────────────────────────────

    def test_shareable_link_display_returns_html_anchor(self):
        result = self.admin_obj.shareable_link_display(self.form)
        self.assertIn("<a", str(result))
        self.assertIn(self.form.slug, str(result))

    def test_shareable_link_contains_live_form_path(self):
        result = self.admin_obj.shareable_link_display(self.form)
        self.assertIn("/live-form/", str(result))

    # ── entry_count_display ─────────────────────────────────────────────

    def test_entry_count_display_reflects_actual_count(self):
        form = self._annotated_form()
        result = self.admin_obj.entry_count_display(form)
        self.assertEqual(result, 1)

    def test_entry_count_display_zero_for_empty_form(self):
        empty_form = make_form(self.user, organization_name="Empty Form")
        form = LiveFormLink.objects.annotate(entry_count=Count("entries")).get(
            pk=empty_form.pk
        )
        result = self.admin_obj.entry_count_display(form)
        self.assertEqual(result, 0)

    # ── expiry_status ───────────────────────────────────────────────────

    def test_expiry_status_active(self):
        result = str(self.admin_obj.expiry_status(self.form))
        self.assertIn("Active", result)

    def test_expiry_status_expired(self):
        expired = make_form(self.user, expires_at=past(), organization_name="Expired For Admin")
        result = str(self.admin_obj.expiry_status(expired))
        self.assertIn("Expired", result)

    def test_expiry_status_deactivated(self):
        inactive = make_form(self.user, is_active=False, organization_name="Inactive For Admin")
        result = str(self.admin_obj.expiry_status(inactive))
        self.assertIn("Deactivated", result)

    # ── copy_link_action ────────────────────────────────────────────────

    def test_copy_link_action_adds_success_message(self):
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk=self.form.pk)
        self.admin_obj.copy_link_action(request, qs)
        # If no exception raised, the action ran successfully
        storage = request._messages
        messages = list(storage)
        self.assertTrue(len(messages) > 0)

    def test_copy_link_action_message_contains_slug(self):
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk=self.form.pk)
        self.admin_obj.copy_link_action(request, qs)
        messages = list(request._messages)
        combined = " ".join(str(m) for m in messages)
        self.assertIn(self.form.slug, combined)

    # ── download_pdf_action ─────────────────────────────────────────────

    @patch("live_forms.admin.generate_live_form_pdf")
    def test_download_pdf_action_returns_pdf_response(self, mock_pdf):
        mock_pdf.return_value = HttpResponse(b"%PDF", content_type="application/pdf")
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk=self.form.pk)
        response = self.admin_obj.download_pdf_action(request, qs)
        self.assertIsNotNone(response)
        mock_pdf.assert_called_once()

    @patch("live_forms.admin.generate_live_form_pdf")
    def test_download_pdf_action_warns_if_multiple_selected(self, mock_pdf):
        form2 = make_form(self.user, organization_name="Second PDF Form")
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk__in=[self.form.pk, form2.pk])
        result = self.admin_obj.download_pdf_action(request, qs)
        # Should return None (early return) and not call generate
        self.assertIsNone(result)
        mock_pdf.assert_not_called()

    @patch("live_forms.admin.generate_live_form_pdf", side_effect=ImportError("no weasyprint"))
    def test_download_pdf_action_handles_import_error(self, mock_pdf):
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk=self.form.pk)
        # Should not crash — should show error message
        try:
            self.admin_obj.download_pdf_action(request, qs)
        except ImportError:
            self.fail("ImportError should be handled gracefully")

    # ── download_word_action ────────────────────────────────────────────

    @patch("live_forms.admin.generate_live_form_word")
    def test_download_word_action_returns_word_response(self, mock_word):
        mock_word.return_value = HttpResponse(b"PK", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk=self.form.pk)
        response = self.admin_obj.download_word_action(request, qs)
        self.assertIsNotNone(response)
        mock_word.assert_called_once()

    @patch("live_forms.admin.generate_live_form_word")
    def test_download_word_action_warns_if_multiple_selected(self, mock_word):
        form2 = make_form(self.user, organization_name="Second Word Form")
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk__in=[self.form.pk, form2.pk])
        result = self.admin_obj.download_word_action(request, qs)
        self.assertIsNone(result)
        mock_word.assert_not_called()

    # ── download_excel_action ───────────────────────────────────────────

    @patch("live_forms.admin.generate_live_form_excel")
    def test_download_excel_action_returns_excel_response(self, mock_excel):
        mock_excel.return_value = HttpResponse(b"PK", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk=self.form.pk)
        response = self.admin_obj.download_excel_action(request, qs)
        self.assertIsNotNone(response)
        mock_excel.assert_called_once()

    @patch("live_forms.admin.generate_live_form_excel")
    def test_download_excel_action_warns_if_multiple_selected(self, mock_excel):
        form2 = make_form(self.user, organization_name="Second Excel Form")
        request = make_request(self.user)
        qs = LiveFormLink.objects.filter(pk__in=[self.form.pk, form2.pk])
        result = self.admin_obj.download_excel_action(request, qs)
        self.assertIsNone(result)
        mock_excel.assert_not_called()

    # ── get_queryset annotation ─────────────────────────────────────────

    def test_get_queryset_annotates_entry_count(self):
        request = make_request(self.user)
        qs = self.admin_obj.get_queryset(request)
        form = qs.get(pk=self.form.pk)
        self.assertTrue(hasattr(form, "entry_count"))
        self.assertEqual(form.entry_count, 1)

    # ── list_display ────────────────────────────────────────────────────

    def test_list_display_contains_expected_fields(self):
        expected = {"organization_name", "expiry_status", "created_at"}
        self.assertTrue(expected.issubset(set(self.admin_obj.list_display)))

    # ── actions list ───────────────────────────────────────────────────

    def test_actions_includes_expected_actions(self):
        action_names = [
            a if isinstance(a, str) else a.__name__
            for a in self.admin_obj.actions
        ]
        self.assertIn("download_pdf_action", action_names)
        self.assertIn("download_word_action", action_names)
        self.assertIn("download_excel_action", action_names)
        self.assertIn("copy_link_action", action_names)


# ===========================================================================
# IsExpiredFilter
# ===========================================================================

class IsExpiredFilterTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.active_form = make_form(self.user, organization_name="Active Form")
        self.expired_form = make_form(
            self.user, expires_at=past(), organization_name="Expired Form"
        )
        self.site = AdminSite()
        self.admin_obj = LiveFormLinkAdmin(LiveFormLink, self.site)

    def _apply_filter(self, value):
        """Build the filter and apply it to the base queryset."""
        request = make_request(self.user)
        # Django 5.x expects params values as lists (like QueryDict)
        params = {"is_expired": [value]} if value else {}
        # Manually instantiate the filter
        f = IsExpiredFilter(request, params, LiveFormLink, self.admin_obj)
        base_qs = LiveFormLink.objects.annotate(entry_count=Count("entries"))
        return f.queryset(request, base_qs)

    def test_lookups_returns_two_options(self):
        request = make_request(self.user)
        f = IsExpiredFilter(request, {}, LiveFormLink, self.admin_obj)
        lookups = f.lookups(request, self.admin_obj)
        self.assertEqual(len(lookups), 2)

    def test_filter_yes_returns_only_expired(self):
        qs = self._apply_filter("yes")
        # Filter to only forms created in this test
        test_pks = {self.active_form.pk, self.expired_form.pk}
        pks = set(qs.filter(pk__in=test_pks).values_list("pk", flat=True))
        self.assertIn(self.expired_form.pk, pks)
        self.assertNotIn(self.active_form.pk, pks)

    def test_filter_no_returns_only_active(self):
        qs = self._apply_filter("no")
        # Filter to only forms created in this test
        test_pks = {self.active_form.pk, self.expired_form.pk}
        pks = set(qs.filter(pk__in=test_pks).values_list("pk", flat=True))
        self.assertIn(self.active_form.pk, pks)
        self.assertNotIn(self.expired_form.pk, pks)

    def test_no_filter_returns_all(self):
        qs = self._apply_filter(None)
        pks = list(qs.values_list("pk", flat=True))
        self.assertIn(self.active_form.pk, pks)
        self.assertIn(self.expired_form.pk, pks)


# ===========================================================================
# HasSubmissionsFilter
# ===========================================================================

class HasSubmissionsFilterTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form_with = make_form(self.user, organization_name="Has Submissions Form")
        self.form_without = make_form(self.user, organization_name="No Submissions Form")
        make_entry(self.form_with, full_name="Entry Person", size="M")
        self.site = AdminSite()
        self.admin_obj = LiveFormLinkAdmin(LiveFormLink, self.site)

    def _apply_filter(self, value):
        request = make_request(self.user)
        # Django 5.x expects params values as lists (like QueryDict)
        params = {"has_submissions": [value]} if value else {}
        f = HasSubmissionsFilter(request, params, LiveFormLink, self.admin_obj)
        base_qs = LiveFormLink.objects.annotate(entry_count=Count("entries"))
        return f.queryset(request, base_qs)

    def test_lookups_returns_two_options(self):
        request = make_request(self.user)
        f = HasSubmissionsFilter(request, {}, LiveFormLink, self.admin_obj)
        lookups = f.lookups(request, self.admin_obj)
        self.assertEqual(len(lookups), 2)

    def test_filter_yes_returns_forms_with_entries(self):
        qs = self._apply_filter("yes")
        # Filter to only forms created in this test
        test_pks = {self.form_with.pk, self.form_without.pk}
        pks = set(qs.filter(pk__in=test_pks).values_list("pk", flat=True))
        self.assertIn(self.form_with.pk, pks)
        self.assertNotIn(self.form_without.pk, pks)

    def test_filter_no_returns_forms_without_entries(self):
        qs = self._apply_filter("no")
        # Filter to only forms created in this test
        test_pks = {self.form_with.pk, self.form_without.pk}
        pks = set(qs.filter(pk__in=test_pks).values_list("pk", flat=True))
        self.assertIn(self.form_without.pk, pks)
        self.assertNotIn(self.form_with.pk, pks)

    def test_no_filter_returns_all(self):
        qs = self._apply_filter(None)
        pks = list(qs.values_list("pk", flat=True))
        self.assertIn(self.form_with.pk, pks)
        self.assertIn(self.form_without.pk, pks)


# ===========================================================================
# LiveFormEntryInline
# ===========================================================================

class LiveFormEntryInlineTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.inline = LiveFormEntryInline(LiveFormLink, self.site)
        self.user = make_user()

    def test_has_add_permission_returns_false(self):
        request = make_request(self.user)
        self.assertFalse(self.inline.has_add_permission(request))

    def test_can_delete_is_false(self):
        self.assertFalse(self.inline.can_delete)

    def test_max_num_is_zero(self):
        self.assertEqual(self.inline.max_num, 0)

    def test_extra_is_zero(self):
        self.assertEqual(self.inline.extra, 0)

    def test_fields_contain_serial_and_name(self):
        self.assertIn("serial_number", self.inline.fields)
        self.assertIn("full_name", self.inline.fields)

    def test_readonly_fields_contain_all_displayed_fields(self):
        for field in self.inline.fields:
            self.assertIn(field, self.inline.readonly_fields)

    def test_show_change_link_is_true(self):
        self.assertTrue(self.inline.show_change_link)

    def test_ordering_by_serial_number(self):
        self.assertEqual(self.inline.ordering, ["serial_number"])