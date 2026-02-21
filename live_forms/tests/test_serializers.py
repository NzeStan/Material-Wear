# live_forms/tests/test_serializers.py
"""
Comprehensive serializer tests for live_forms app.

Tests:
  - LiveFormLinkSummarySerializer : social_proof, seconds_remaining, is_open/is_expired
  - LiveFormLinkSerializer        : create/update validation, expires_at guard,
                                    read-only field enforcement
  - LiveFormEntrySerializer       : custom_name conditional, form-open guards,
                                    to_representation, create via context
  - LiveFormEntryPublicSerializer : lean feed serializer, custom_name strip
"""
import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory

from live_forms.models import LiveFormEntry, LiveFormLink
from live_forms.serializers import (
    LiveFormEntryPublicSerializer,
    LiveFormEntrySerializer,
    LiveFormLinkSerializer,
    LiveFormLinkSummarySerializer,
)

User = get_user_model()
factory = APIRequestFactory()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def future(hours=24):
    return timezone.now() + timedelta(hours=hours)


def past(hours=1):
    return timezone.now() - timedelta(hours=hours)


def make_user(username=None, staff=False):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(
        username=username, password="testpass", is_staff=staff,
        email=f"{username}@test.com"
    )


def make_form(user=None, **kwargs):
    user = user or make_user()
    defaults = dict(
        organization_name="Test Org",
        expires_at=future(),
        is_active=True,
    )
    defaults.update(kwargs)
    return LiveFormLink.objects.create(created_by=user, **defaults)


def make_entry(live_form, **kwargs):
    defaults = dict(full_name="John Doe", size="M")
    defaults.update(kwargs)
    return LiveFormEntry.objects.create(live_form=live_form, **defaults)


def get_request():
    return factory.get("/")


# ===========================================================================
# LiveFormLinkSummarySerializer
# ===========================================================================

class LiveFormLinkSummarySerializerTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user, organization_name="Unilag FC")

    def _serialise(self, form=None):
        form = form or self.form
        request = get_request()
        return LiveFormLinkSummarySerializer(
            form, context={"request": request}
        ).data

    # ── Field presence ──────────────────────────────────────────────────

    def test_contains_expected_fields(self):
        data = self._serialise()
        expected = {
            "id", "slug", "organization_name", "custom_branding_enabled",
            "expires_at", "max_submissions", "is_active", "is_expired",
            "is_open", "shareable_url", "seconds_remaining", "total_submissions",
            "view_count", "last_submission_at", "social_proof", "created_at",
        }
        self.assertEqual(set(data.keys()), expected)

    # ── is_expired / is_open ────────────────────────────────────────────

    def test_is_open_true_for_active_non_expired_form(self):
        data = self._serialise()
        self.assertTrue(data["is_open"])
        self.assertFalse(data["is_expired"])

    def test_is_open_false_for_expired_form(self):
        form = make_form(self.user, expires_at=past())
        data = self._serialise(form)
        self.assertFalse(data["is_open"])
        self.assertTrue(data["is_expired"])

    def test_is_open_false_for_inactive_form(self):
        form = make_form(self.user, is_active=False)
        data = self._serialise(form)
        self.assertFalse(data["is_open"])

    # ── seconds_remaining ───────────────────────────────────────────────

    def test_seconds_remaining_positive_for_future_form(self):
        data = self._serialise()
        self.assertGreater(data["seconds_remaining"], 0)

    def test_seconds_remaining_zero_for_expired_form(self):
        form = make_form(self.user, expires_at=past())
        data = self._serialise(form)
        self.assertEqual(data["seconds_remaining"], 0)

    def test_seconds_remaining_never_negative(self):
        form = make_form(self.user, expires_at=past(100))
        data = self._serialise(form)
        self.assertGreaterEqual(data["seconds_remaining"], 0)

    # ── total_submissions ───────────────────────────────────────────────

    def test_total_submissions_zero_initially(self):
        data = self._serialise()
        self.assertEqual(data["total_submissions"], 0)

    def test_total_submissions_counts_entries(self):
        make_entry(self.form, full_name="Alice Adams", size="S")
        make_entry(self.form, full_name="Bob Brown", size="M")
        data = self._serialise()
        self.assertEqual(data["total_submissions"], 2)

    # ── social_proof block ──────────────────────────────────────────────

    def test_social_proof_keys_present(self):
        data = self._serialise()
        sp = data["social_proof"]
        for key in ["total_submissions", "submissions_last_hour",
                    "recent_submitters", "view_count", "last_submission_at"]:
            self.assertIn(key, sp)

    def test_social_proof_recent_submitters_privacy(self):
        """Names should be truncated: 'John D.' not 'John Doe'."""
        make_entry(self.form, full_name="John Doe", size="M")
        data = self._serialise()
        submitters = data["social_proof"]["recent_submitters"]
        self.assertEqual(len(submitters), 1)
        name = submitters[0]["name"]
        # Should NOT contain full last name
        self.assertNotEqual(name, "JOHN DOE")
        # Should end with a period (truncated initial)
        self.assertTrue(name.endswith("."))

    def test_social_proof_max_five_recent_submitters(self):
        for i in range(10):
            make_entry(self.form, full_name=f"Person {i} Test", size="M")
        data = self._serialise()
        submitters = data["social_proof"]["recent_submitters"]
        self.assertLessEqual(len(submitters), 5)

    def test_social_proof_submissions_last_hour(self):
        make_entry(self.form, full_name="Recent Person", size="S")
        data = self._serialise()
        self.assertGreaterEqual(data["social_proof"]["submissions_last_hour"], 1)

    # ── shareable_url ───────────────────────────────────────────────────

    def test_shareable_url_contains_slug(self):
        data = self._serialise()
        self.assertIn(self.form.slug, data["shareable_url"])

    def test_shareable_url_is_absolute_with_request(self):
        data = self._serialise()
        self.assertTrue(data["shareable_url"].startswith("http"))


# ===========================================================================
# LiveFormLinkSerializer (full admin serializer)
# ===========================================================================

class LiveFormLinkSerializerTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def _create_data(self, **overrides):
        data = dict(
            organization_name="New Org",
            expires_at=(future(48)).isoformat(),
            max_submissions=None,
            is_active=True,
            custom_branding_enabled=False,
        )
        data.update(overrides)
        return data

    def _deserialise(self, data):
        request = get_request()
        request.user = self.user
        return LiveFormLinkSerializer(data=data, context={"request": request})

    # ── Valid creation ──────────────────────────────────────────────────

    def test_valid_data_is_valid(self):
        s = self._deserialise(self._create_data())
        self.assertTrue(s.is_valid(), s.errors)

    def test_create_sets_slug_automatically(self):
        s = self._deserialise(self._create_data())
        self.assertTrue(s.is_valid())
        form = s.save(created_by=self.user)
        self.assertIsNotNone(form.slug)

    # ── expires_at validation ───────────────────────────────────────────

    def test_expires_at_in_past_is_invalid_on_create(self):
        data = self._create_data(expires_at=past().isoformat())
        s = self._deserialise(data)
        self.assertFalse(s.is_valid())
        self.assertIn("expires_at", s.errors)

    def test_expires_at_right_now_is_invalid(self):
        data = self._create_data(expires_at=timezone.now().isoformat())
        s = self._deserialise(data)
        self.assertFalse(s.is_valid())

    def test_expires_at_in_future_is_valid(self):
        data = self._create_data(expires_at=future(2).isoformat())
        s = self._deserialise(data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_expires_at_update_allows_past_value_on_existing(self):
        """On update (instance set), past expires_at should be allowed
        so admin can mark form as expired retrospectively."""
        form = make_form(self.user)
        request = get_request()
        request.user = self.user
        s = LiveFormLinkSerializer(
            instance=form,
            data={"expires_at": past().isoformat()},
            partial=True,
            context={"request": request},
        )
        # This should be valid (instance is set → creation guard skipped)
        self.assertTrue(s.is_valid(), s.errors)

    # ── Read-only fields ────────────────────────────────────────────────

    def test_slug_is_read_only(self):
        data = self._create_data()
        data["slug"] = "injected-slug"
        s = self._deserialise(data)
        self.assertTrue(s.is_valid())
        form = s.save(created_by=self.user)
        self.assertNotEqual(form.slug, "injected-slug")

    def test_view_count_is_read_only(self):
        data = self._create_data()
        data["view_count"] = 9999
        s = self._deserialise(data)
        self.assertTrue(s.is_valid())
        form = s.save(created_by=self.user)
        self.assertEqual(form.view_count, 0)

    def test_created_by_is_read_only(self):
        other_user = make_user()
        data = self._create_data()
        data["created_by"] = other_user.pk
        s = self._deserialise(data)
        self.assertTrue(s.is_valid())
        form = s.save(created_by=self.user)
        # Should be our user, not other_user
        self.assertEqual(form.created_by, self.user)

    # ── Computed method fields ──────────────────────────────────────────

    def test_is_open_computed_correctly(self):
        form = make_form(self.user)
        request = get_request()
        data = LiveFormLinkSerializer(form, context={"request": request}).data
        self.assertTrue(data["is_open"])

    def test_is_expired_computed_correctly(self):
        form = make_form(self.user, expires_at=past())
        request = get_request()
        data = LiveFormLinkSerializer(form, context={"request": request}).data
        self.assertTrue(data["is_expired"])


# ===========================================================================
# LiveFormEntrySerializer
# ===========================================================================

class LiveFormEntrySerializerTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)
        self.form_with_branding = make_form(
            self.user,
            organization_name="Branded Org",
            custom_branding_enabled=True,
        )

    def _deserialise(self, data, live_form=None):
        live_form = live_form or self.form
        return LiveFormEntrySerializer(
            data=data, context={"live_form": live_form, "request": get_request()}
        )

    def _valid_data(self, **overrides):
        data = dict(full_name="Jane Smith", size="L")
        data.update(overrides)
        return data

    # ── Valid submission ────────────────────────────────────────────────

    def test_valid_entry_is_valid(self):
        s = self._deserialise(self._valid_data())
        self.assertTrue(s.is_valid(), s.errors)

    def test_create_entry_via_serializer(self):
        s = self._deserialise(self._valid_data())
        self.assertTrue(s.is_valid())
        entry = s.save()
        self.assertIsNotNone(entry.pk)
        self.assertEqual(entry.live_form, self.form)

    def test_serial_number_auto_assigned(self):
        s = self._deserialise(self._valid_data())
        self.assertTrue(s.is_valid())
        entry = s.save()
        self.assertEqual(entry.serial_number, 1)

    # ── Form-open guards ────────────────────────────────────────────────

    def test_submission_rejected_when_form_expired(self):
        expired_form = make_form(self.user, expires_at=past(), organization_name="Exp Org")
        s = self._deserialise(self._valid_data(), live_form=expired_form)
        self.assertFalse(s.is_valid())
        errors = str(s.errors)
        self.assertIn("expired", errors.lower())

    def test_submission_rejected_when_form_inactive(self):
        inactive_form = make_form(self.user, is_active=False, organization_name="Inactive Org")
        s = self._deserialise(self._valid_data(), live_form=inactive_form)
        self.assertFalse(s.is_valid())
        errors = str(s.errors)
        self.assertIn("deactivated", errors.lower())

    def test_submission_rejected_when_max_submissions_reached(self):
        full_form = make_form(
            self.user, max_submissions=1, organization_name="Full Form"
        )
        # Fill it up
        LiveFormEntry.objects.create(
            live_form=full_form, full_name="Person One", size="S"
        )
        s = self._deserialise(self._valid_data(), live_form=full_form)
        self.assertFalse(s.is_valid())
        errors = str(s.errors)
        self.assertIn("maximum", errors.lower())

    def test_submission_rejected_when_no_live_form_context(self):
        s = LiveFormEntrySerializer(
            data=self._valid_data(),
            context={"request": get_request()},
        )
        self.assertFalse(s.is_valid())
        self.assertIn("live_form", s.errors)

    # ── custom_name conditional ─────────────────────────────────────────

    def test_custom_name_required_when_branding_enabled(self):
        s = self._deserialise(
            self._valid_data(),  # no custom_name
            live_form=self.form_with_branding,
        )
        self.assertFalse(s.is_valid())
        self.assertIn("custom_name", s.errors)

    def test_custom_name_accepted_when_branding_enabled(self):
        s = self._deserialise(
            self._valid_data(custom_name="Jersey Name"),
            live_form=self.form_with_branding,
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_custom_name_blank_rejected_when_branding_enabled(self):
        s = self._deserialise(
            self._valid_data(custom_name="  "),
            live_form=self.form_with_branding,
        )
        self.assertFalse(s.is_valid())

    def test_custom_name_not_required_when_branding_disabled(self):
        s = self._deserialise(
            self._valid_data(),  # no custom_name, branding off
            live_form=self.form,
        )
        self.assertTrue(s.is_valid(), s.errors)

    # ── to_representation ───────────────────────────────────────────────

    def test_custom_name_stripped_from_output_when_branding_disabled(self):
        entry = LiveFormEntry.objects.create(
            live_form=self.form,
            full_name="Test User",
            size="M",
            custom_name="Private Name",
        )
        s = LiveFormEntrySerializer(
            entry, context={"request": get_request()}
        )
        self.assertNotIn("custom_name", s.data)

    def test_custom_name_present_in_output_when_branding_enabled(self):
        entry = LiveFormEntry.objects.create(
            live_form=self.form_with_branding,
            full_name="Branded User",
            size="M",
            custom_name="Jersey Guy",
        )
        s = LiveFormEntrySerializer(
            entry, context={"request": get_request()}
        )
        self.assertIn("custom_name", s.data)
        self.assertEqual(s.data["custom_name"], "JERSEY GUY")

    def test_read_only_fields_not_writeable(self):
        data = self._valid_data()
        data["serial_number"] = 999
        s = self._deserialise(data)
        self.assertTrue(s.is_valid())
        entry = s.save()
        self.assertNotEqual(entry.serial_number, 999)

    # ── Size field validation ───────────────────────────────────────────

    def test_invalid_size_rejected(self):
        s = self._deserialise(self._valid_data(size="MEGA"))
        self.assertFalse(s.is_valid())
        self.assertIn("size", s.errors)

    def test_all_valid_sizes_accepted(self):
        for size_code, _ in LiveFormEntry.SIZE_CHOICES:
            s = self._deserialise(self._valid_data(size=size_code))
            self.assertTrue(s.is_valid(), f"Size {size_code} failed: {s.errors}")


# ===========================================================================
# LiveFormEntryPublicSerializer
# ===========================================================================

class LiveFormEntryPublicSerializerTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)
        self.form_branded = make_form(
            self.user,
            organization_name="Branded",
            custom_branding_enabled=True,
        )

    def test_fields_present(self):
        entry = LiveFormEntry.objects.create(
            live_form=self.form, full_name="Seun Kuti", size="M"
        )
        data = LiveFormEntryPublicSerializer(entry).data
        for field in ["id", "serial_number", "full_name", "size", "created_at"]:
            self.assertIn(field, data)

    def test_no_live_form_nested_object(self):
        """Public serializer should NOT embed the full live_form object."""
        entry = LiveFormEntry.objects.create(
            live_form=self.form, full_name="Test User", size="L"
        )
        data = LiveFormEntryPublicSerializer(entry).data
        self.assertNotIn("live_form", data)

    def test_custom_name_stripped_when_branding_disabled(self):
        entry = LiveFormEntry.objects.create(
            live_form=self.form,
            full_name="Hidden Name",
            size="S",
            custom_name="Secret",
        )
        data = LiveFormEntryPublicSerializer(entry).data
        self.assertNotIn("custom_name", data)

    def test_custom_name_present_when_branding_enabled(self):
        entry = LiveFormEntry.objects.create(
            live_form=self.form_branded,
            full_name="Public User",
            size="XL",
            custom_name="Show This",
        )
        data = LiveFormEntryPublicSerializer(entry).data
        self.assertIn("custom_name", data)

    def test_serialises_multiple_entries(self):
        for i in range(5):
            LiveFormEntry.objects.create(
                live_form=self.form,
                full_name=f"Person {i}",
                size="M",
            )
        entries = LiveFormEntry.objects.filter(live_form=self.form)
        data = LiveFormEntryPublicSerializer(entries, many=True).data
        self.assertEqual(len(data), 5)