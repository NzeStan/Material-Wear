# live_forms/tests/test_views.py
"""
Comprehensive view tests for live_forms app.

Tests:
  - SheetViewTest              : Django template view, 404, view_count increment
  - LiveFormLinkViewSetTest    : CRUD, permission matrix, queryset scoping
  - SubmitActionTest           : Public submit endpoint — valid/invalid/closed
  - LiveFeedPollingTest        : live_feed ?since= filtering, structure
  - AdminActionsTest           : admin_entries, download_pdf/word/excel permissions
  - LiveFormEntryViewSetTest   : list (admin-only), retrieve (public), delete
"""
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from live_forms.models import LiveFormEntry, LiveFormLink

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def future(hours=24):
    return timezone.now() + timedelta(hours=hours)


def past(hours=1):
    return timezone.now() - timedelta(hours=hours)


def make_user(username=None, staff=False, superuser=False):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    if superuser:
        return User.objects.create_superuser(
            username=username, password="testpass", email=f"{username}@test.com"
        )
    return User.objects.create_user(
        username=username,
        password="testpass",
        is_staff=staff,
        email=f"{username}@test.com",
    )


def make_form(user, **kwargs):
    defaults = dict(
        organization_name="Test Org",
        expires_at=future(),
        is_active=True,
    )
    defaults.update(kwargs)
    return LiveFormLink.objects.create(created_by=user, **defaults)


def make_entry(form, **kwargs):
    defaults = dict(full_name="Test Person", size="M")
    defaults.update(kwargs)
    return LiveFormEntry.objects.create(live_form=form, **defaults)


# ---------------------------------------------------------------------------
# URL helpers  (adjust prefixes to match your root urls.py mounts)
# ---------------------------------------------------------------------------

def form_list_url():
    return "/api/live_forms/api/forms/"


def form_detail_url(slug):
    return f"/api/live_forms/api/forms/{slug}/"


def submit_url(slug):
    return f"/api/live_forms/api/forms/{slug}/submit/"


def live_feed_url(slug):
    return f"/api/live_forms/api/forms/{slug}/live_feed/"


def admin_entries_url(slug):
    return f"/api/live_forms/api/forms/{slug}/admin_entries/"


def download_pdf_url(slug):
    return f"/api/live_forms/api/forms/{slug}/download_pdf/"


def download_word_url(slug):
    return f"/api/live_forms/api/forms/{slug}/download_word/"


def download_excel_url(slug):
    return f"/api/live_forms/api/forms/{slug}/download_excel/"


def entry_list_url():
    return "/api/live_forms/api/entries/"


def entry_detail_url(pk):
    return f"/api/live_forms/api/entries/{pk}/"


def sheet_url(slug):
    return f"/api/live_forms/{slug}/"


# ===========================================================================
# SheetView (Django template view)
# ===========================================================================

class SheetViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)

    def test_sheet_view_returns_200(self):
        response = self.client.get(sheet_url(self.form.slug))
        self.assertEqual(response.status_code, 200)

    def test_sheet_view_renders_correct_template(self):
        response = self.client.get(sheet_url(self.form.slug))
        self.assertTemplateUsed(response, "live_forms/sheet.html")

    def test_sheet_view_increments_view_count(self):
        initial_count = self.form.view_count
        self.client.get(sheet_url(self.form.slug))
        self.form.refresh_from_db()
        self.assertEqual(self.form.view_count, initial_count + 1)

    def test_sheet_view_increments_atomically_on_multiple_hits(self):
        for _ in range(5):
            self.client.get(sheet_url(self.form.slug))
        self.form.refresh_from_db()
        self.assertEqual(self.form.view_count, 5)

    def test_sheet_view_404_for_nonexistent_slug(self):
        response = self.client.get(sheet_url("this-does-not-exist"))
        self.assertEqual(response.status_code, 404)

    def test_sheet_view_context_contains_live_form(self):
        response = self.client.get(sheet_url(self.form.slug))
        self.assertIn("live_form", response.context)

    def test_sheet_view_context_contains_entries(self):
        response = self.client.get(sheet_url(self.form.slug))
        self.assertIn("entries", response.context)

    def test_sheet_view_context_contains_is_open(self):
        response = self.client.get(sheet_url(self.form.slug))
        self.assertIn("is_open", response.context)
        self.assertTrue(response.context["is_open"])

    def test_sheet_view_context_is_open_false_when_expired(self):
        form = make_form(self.user, expires_at=past(), organization_name="Expired")
        response = self.client.get(sheet_url(form.slug))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_open"])

    def test_sheet_view_context_seconds_remaining_non_negative(self):
        response = self.client.get(sheet_url(self.form.slug))
        self.assertGreaterEqual(response.context["seconds_remaining"], 0)

    def test_sheet_view_context_size_choices_populated(self):
        response = self.client.get(sheet_url(self.form.slug))
        self.assertIn("size_choices", response.context)
        self.assertTrue(len(response.context["size_choices"]) > 0)

    def test_sheet_view_only_allows_get(self):
        response = self.client.post(sheet_url(self.form.slug), {})
        self.assertEqual(response.status_code, 405)


# ===========================================================================
# LiveFormLinkViewSet — CRUD and permissions
# ===========================================================================

class LiveFormLinkViewSetCRUDTest(APITestCase):

    def setUp(self):
        self.admin = make_user(staff=True)
        self.owner = make_user()
        self.other = make_user()
        self.form = make_form(self.owner, organization_name="Owner Form")
        self.admin_form = make_form(self.admin, organization_name="Admin Form")

    # ── List ────────────────────────────────────────────────────────────

    def test_admin_sees_all_forms(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(form_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [f["slug"] for f in response.data.get("results", response.data)]
        self.assertIn(self.form.slug, slugs)
        self.assertIn(self.admin_form.slug, slugs)

    def test_owner_sees_only_own_forms(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(form_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [f["slug"] for f in response.data.get("results", response.data)]
        self.assertIn(self.form.slug, slugs)
        self.assertNotIn(self.admin_form.slug, slugs)

    def test_anonymous_cannot_list(self):
        response = self.client.get(form_list_url())
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])

    # ── Retrieve ────────────────────────────────────────────────────────

    def test_public_can_retrieve_active_form(self):
        response = self.client.get(form_detail_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_returns_summary_serializer_for_anonymous(self):
        response = self.client.get(form_detail_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Summary serializer includes social_proof
        self.assertIn("social_proof", response.data)

    def test_retrieve_returns_full_serializer_for_authenticated(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(form_detail_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Full serializer does not have social_proof (that's Summary)
        # but does have updated_at
        self.assertIn("updated_at", response.data)

    def test_retrieve_increments_view_count(self):
        before = self.form.view_count
        self.client.get(form_detail_url(self.form.slug))
        self.form.refresh_from_db()
        self.assertEqual(self.form.view_count, before + 1)

    def test_retrieve_404_for_nonexistent_slug(self):
        response = self.client.get(form_detail_url("no-such-slug"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── Create ──────────────────────────────────────────────────────────

    def test_authenticated_user_can_create_form(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "organization_name": "Brand New Org",
            "expires_at": future(48).isoformat(),
        }
        response = self.client.post(form_list_url(), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("slug", response.data)

    def test_anonymous_cannot_create_form(self):
        payload = {
            "organization_name": "Anon Org",
            "expires_at": future(48).isoformat(),
        }
        response = self.client.post(form_list_url(), payload, format="json")
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])

    def test_create_assigns_created_by_to_request_user(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "organization_name": "Assigned Owner Org",
            "expires_at": future(48).isoformat(),
        }
        response = self.client.post(form_list_url(), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        form = LiveFormLink.objects.get(slug=response.data["slug"])
        self.assertEqual(form.created_by, self.owner)

    def test_create_rejects_past_expiry(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "organization_name": "Past Expiry Org",
            "expires_at": past().isoformat(),
        }
        response = self.client.post(form_list_url(), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Update ──────────────────────────────────────────────────────────

    def test_owner_can_update_own_form(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(
            form_detail_url(self.form.slug),
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_update_form(self):
        self.client.force_authenticate(self.other)
        response = self.client.patch(
            form_detail_url(self.form.slug),
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_update_any_form(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            form_detail_url(self.form.slug),
            {"is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── Delete ──────────────────────────────────────────────────────────

    def test_owner_can_delete_own_form(self):
        self.client.force_authenticate(self.owner)
        response = self.client.delete(form_detail_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_other_user_cannot_delete_form(self):
        self.client.force_authenticate(self.other)
        response = self.client.delete(form_detail_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_cannot_delete_form(self):
        response = self.client.delete(form_detail_url(self.form.slug))
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])


# ===========================================================================
# Submit action
# ===========================================================================

class SubmitActionTest(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user, organization_name="Submit Test Org")
        self.form_branded = make_form(
            self.user,
            organization_name="Branded Submit Org",
            custom_branding_enabled=True,
        )

    def _submit(self, slug, payload):
        return self.client.post(submit_url(slug), payload, format="json")

    # ── Happy path ──────────────────────────────────────────────────────

    def test_public_can_submit_to_open_form(self):
        response = self._submit(self.form.slug, {"full_name": "Alice Adeyemi", "size": "M"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_response_contains_entry_data(self):
        response = self._submit(self.form.slug, {"full_name": "Bob Nwosu", "size": "L"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("serial_number", response.data)
        self.assertIn("id", response.data)

    def test_serial_number_increments(self):
        self._submit(self.form.slug, {"full_name": "First Person", "size": "S"})
        response = self._submit(self.form.slug, {"full_name": "Second Person", "size": "M"})
        self.assertEqual(response.data["serial_number"], 2)

    def test_submit_with_custom_name_when_branding_enabled(self):
        response = self._submit(
            self.form_branded.slug,
            {"full_name": "Custom User", "size": "XL", "custom_name": "Gold Striker"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_submit_stores_names_uppercase(self):
        self._submit(self.form.slug, {"full_name": "emeka obi", "size": "S"})
        entry = LiveFormEntry.objects.get(live_form=self.form)
        self.assertEqual(entry.full_name, "EMEKA OBI")

    # ── Guard failures ──────────────────────────────────────────────────

    def test_submit_to_nonexistent_form_returns_404(self):
        response = self._submit("no-such-form", {"full_name": "Ghost", "size": "M"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_to_expired_form_rejected(self):
        expired = make_form(self.user, expires_at=past(), organization_name="Expired Form")
        response = self._submit(expired.slug, {"full_name": "Late Person", "size": "M"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_to_inactive_form_rejected(self):
        inactive = make_form(self.user, is_active=False, organization_name="Inactive Form")
        response = self._submit(inactive.slug, {"full_name": "Blocked", "size": "M"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_rejected_when_max_submissions_reached(self):
        full_form = make_form(self.user, max_submissions=1, organization_name="Full Form")
        self._submit(full_form.slug, {"full_name": "First Slot", "size": "S"})
        response = self._submit(full_form.slug, {"full_name": "Second Slot", "size": "M"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_missing_full_name_rejected(self):
        response = self._submit(self.form.slug, {"size": "M"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_missing_size_rejected(self):
        response = self._submit(self.form.slug, {"full_name": "No Size"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_invalid_size_rejected(self):
        response = self._submit(self.form.slug, {"full_name": "Invalid Size", "size": "GIANT"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_missing_custom_name_rejected_when_branding_enabled(self):
        response = self._submit(
            self.form_branded.slug, {"full_name": "No Custom", "size": "M"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_submit_updates_last_submission_at(self):
        self.assertIsNone(self.form.last_submission_at)
        self._submit(self.form.slug, {"full_name": "Time Test", "size": "M"})
        self.form.refresh_from_db()
        self.assertIsNotNone(self.form.last_submission_at)

    @patch("live_forms.views.send_live_form_submission_email_async")
    def test_submit_triggers_background_email(self, mock_email):
        self._submit(self.form.slug, {"full_name": "Email Person", "size": "M"})
        mock_email.assert_called_once()

    @patch("live_forms.views.send_live_form_submission_email_async", side_effect=Exception("SMTP down"))
    def test_submit_succeeds_even_if_email_fails(self, mock_email):
        """Email failure must NOT fail the submission response."""
        response = self._submit(self.form.slug, {"full_name": "Resilient Person", "size": "M"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# ===========================================================================
# live_feed polling
# ===========================================================================

class LiveFeedPollingTest(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user, organization_name="Feed Test Org")

    def _feed(self, slug=None, since=None):
        slug = slug or self.form.slug
        url = live_feed_url(slug)
        if since:
            url = f"{url}?since={since}"
        return self.client.get(url)

    # ── Basic structure ─────────────────────────────────────────────────

    def test_feed_returns_200(self):
        response = self._feed()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_feed_contains_form_block(self):
        response = self._feed()
        self.assertIn("form", response.data)

    def test_feed_contains_entries_list(self):
        response = self._feed()
        self.assertIn("entries", response.data)

    def test_feed_contains_server_time(self):
        response = self._feed()
        self.assertIn("server_time", response.data)

    def test_feed_form_block_contains_is_open(self):
        response = self._feed()
        self.assertIn("is_open", response.data["form"])

    def test_feed_form_block_contains_social_proof(self):
        response = self._feed()
        self.assertIn("social_proof", response.data["form"])

    def test_feed_form_block_contains_seconds_remaining(self):
        response = self._feed()
        self.assertIn("seconds_remaining", response.data["form"])

    def test_feed_returns_all_entries_initially(self):
        make_entry(self.form, full_name="First Person", size="S")
        make_entry(self.form, full_name="Second Person", size="M")
        response = self._feed()
        self.assertEqual(len(response.data["entries"]), 2)

    def test_feed_404_for_nonexistent_slug(self):
        response = self._feed("no-such-slug")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── ?since= filtering ───────────────────────────────────────────────

    def test_since_param_filters_new_entries_only(self):
        old_entry = make_entry(self.form, full_name="Old Person", size="S")
        # Manually set old_entry's created_at using update() since auto_now_add fields aren't editable
        old_time = timezone.now() - timedelta(seconds=10)
        LiveFormEntry.objects.filter(pk=old_entry.pk).update(created_at=old_time)
        old_entry.refresh_from_db()

        # Record a timestamp AFTER the old entry
        cutoff = timezone.now() - timedelta(seconds=5)
        # Create a new entry after the cutoff
        new_entry = make_entry(self.form, full_name="New Person", size="M")

        response = self._feed(since=cutoff.isoformat())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry_ids = [str(e["id"]) for e in response.data["entries"]]
        self.assertIn(str(new_entry.id), entry_ids)
        self.assertNotIn(str(old_entry.id), entry_ids)

    def test_since_param_with_utc_z_suffix(self):
        make_entry(self.form, full_name="Test Person", size="L")
        since = (timezone.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        response = self._feed(since=since)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Future `since` → no entries
        self.assertEqual(len(response.data["entries"]), 0)

    def test_invalid_since_param_returns_all_entries(self):
        make_entry(self.form, full_name="Entry One", size="S")
        response = self._feed(since="not-a-valid-date")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["entries"]), 1)

    # ── Expired form ────────────────────────────────────────────────────

    def test_feed_is_open_false_for_expired_form(self):
        expired_form = make_form(self.user, expires_at=past(), organization_name="Exp Feed")
        response = self._feed(expired_form.slug)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["form"]["is_open"])
        self.assertEqual(response.data["form"]["seconds_remaining"], 0)

    # ── Public access ───────────────────────────────────────────────────

    def test_feed_accessible_without_authentication(self):
        """live_feed must be public — no auth header."""
        response = self.client.get(live_feed_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ===========================================================================
# Admin-only actions
# ===========================================================================

class AdminActionsTest(APITestCase):

    def setUp(self):
        self.admin = make_user(staff=True)
        self.regular = make_user()
        self.form = make_form(self.admin, organization_name="Admin Action Org")
        make_entry(self.form, full_name="Admin Entry One", size="L")

    # ── admin_entries ───────────────────────────────────────────────────

    def test_admin_can_access_admin_entries(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(admin_entries_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_access_admin_entries(self):
        self.client.force_authenticate(self.regular)
        response = self.client.get(admin_entries_url(self.form.slug))
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ])

    def test_anonymous_cannot_access_admin_entries(self):
        response = self.client.get(admin_entries_url(self.form.slug))
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])

    def test_admin_entries_returns_all_entries(self):
        make_entry(self.form, full_name="Second Entry", size="M")
        self.client.force_authenticate(self.admin)
        response = self.client.get(admin_entries_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    # ── download_pdf ────────────────────────────────────────────────────

    @patch("live_forms.views.generate_live_form_pdf")
    def test_admin_can_download_pdf(self, mock_pdf):
        from django.http import HttpResponse as DjHttpResponse
        mock_pdf.return_value = DjHttpResponse(
            b"%PDF-1.4", content_type="application/pdf"
        )
        self.client.force_authenticate(self.admin)
        response = self.client.get(download_pdf_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_pdf.assert_called_once()

    @patch("live_forms.views.generate_live_form_pdf")
    def test_regular_user_cannot_download_pdf(self, mock_pdf):
        self.client.force_authenticate(self.regular)
        response = self.client.get(download_pdf_url(self.form.slug))
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ])
        mock_pdf.assert_not_called()

    @patch("live_forms.views.generate_live_form_pdf", side_effect=ImportError("no weasyprint"))
    def test_pdf_import_error_returns_503(self, mock_pdf):
        self.client.force_authenticate(self.admin)
        response = self.client.get(download_pdf_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch("live_forms.views.generate_live_form_pdf", side_effect=Exception("boom"))
    def test_pdf_generic_error_returns_500(self, mock_pdf):
        self.client.force_authenticate(self.admin)
        response = self.client.get(download_pdf_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── download_word ───────────────────────────────────────────────────

    @patch("live_forms.views.generate_live_form_word")
    def test_admin_can_download_word(self, mock_word):
        from django.http import HttpResponse as DjHttpResponse
        mock_word.return_value = DjHttpResponse(
            b"PK", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        self.client.force_authenticate(self.admin)
        response = self.client.get(download_word_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_word.assert_called_once()

    @patch("live_forms.views.generate_live_form_word")
    def test_regular_user_cannot_download_word(self, mock_word):
        self.client.force_authenticate(self.regular)
        response = self.client.get(download_word_url(self.form.slug))
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ])

    @patch("live_forms.views.generate_live_form_word", side_effect=Exception("word crash"))
    def test_word_generic_error_returns_500(self, mock_word):
        self.client.force_authenticate(self.admin)
        response = self.client.get(download_word_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ── download_excel ──────────────────────────────────────────────────

    @patch("live_forms.views.generate_live_form_excel")
    def test_admin_can_download_excel(self, mock_excel):
        from django.http import HttpResponse as DjHttpResponse
        mock_excel.return_value = DjHttpResponse(
            b"PK", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.client.force_authenticate(self.admin)
        response = self.client.get(download_excel_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_excel.assert_called_once()

    @patch("live_forms.views.generate_live_form_excel", side_effect=Exception("excel crash"))
    def test_excel_generic_error_returns_500(self, mock_excel):
        self.client.force_authenticate(self.admin)
        response = self.client.get(download_excel_url(self.form.slug))
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===========================================================================
# LiveFormEntryViewSet
# ===========================================================================

class LiveFormEntryViewSetTest(APITestCase):

    def setUp(self):
        self.admin = make_user(staff=True)
        self.regular = make_user()
        self.form = make_form(self.admin, organization_name="Entry VS Org")
        self.entry = make_entry(self.form, full_name="Entry Person", size="L")

    # ── List ────────────────────────────────────────────────────────────

    def test_admin_can_list_all_entries(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(entry_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_list_entries(self):
        self.client.force_authenticate(self.regular)
        response = self.client.get(entry_list_url())
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        ])

    def test_anonymous_cannot_list_entries(self):
        response = self.client.get(entry_list_url())
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        ])

    # ── Retrieve ────────────────────────────────────────────────────────

    def test_public_can_retrieve_entry_by_uuid(self):
        response = self.client.get(entry_detail_url(self.entry.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_returns_correct_entry(self):
        response = self.client.get(entry_detail_url(self.entry.id))
        self.assertEqual(str(response.data["id"]), str(self.entry.id))

    def test_retrieve_404_for_nonexistent_uuid(self):
        fake_uuid = uuid.uuid4()
        response = self.client.get(entry_detail_url(fake_uuid))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── Delete ──────────────────────────────────────────────────────────

    def test_admin_can_delete_entry(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(entry_detail_url(self.entry.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(LiveFormEntry.objects.filter(pk=self.entry.pk).exists())

    def test_regular_user_cannot_delete_entry(self):
        self.client.force_authenticate(self.regular)
        response = self.client.delete(entry_detail_url(self.entry.id))
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        ])

    def test_anonymous_cannot_delete_entry(self):
        response = self.client.delete(entry_detail_url(self.entry.id))
        self.assertIn(response.status_code, [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        ])