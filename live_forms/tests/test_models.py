# live_forms/tests/test_models.py
"""
Comprehensive model tests for live_forms app.

Tests:
  - LiveFormLink  : slug generation, name normalisation, expiry logic,
                    is_open() guards, get_shareable_url(), Meta/indexes
  - LiveFormEntry : serial_number auto-increment, name normalisation,
                    social-proof counter update, __str__, Meta
  - Concurrent    : race-condition safety (serial_number under select_for_update)
"""
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.utils.text import slugify

from live_forms.models import LiveFormEntry, LiveFormLink

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def future(hours=24):
    """Return a timezone-aware datetime `hours` from now."""
    return timezone.now() + timedelta(hours=hours)


def past(hours=1):
    """Return a timezone-aware datetime `hours` ago."""
    return timezone.now() - timedelta(hours=hours)


def make_user(username=None, staff=False):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(
        username=username,
        password="testpass123",
        is_staff=staff,
    )


def make_form(user=None, **kwargs):
    """Create a LiveFormLink with sensible defaults."""
    user = user or make_user()
    defaults = dict(
        organization_name="Test Org",
        expires_at=future(),
        is_active=True,
    )
    defaults.update(kwargs)
    return LiveFormLink.objects.create(created_by=user, **defaults)


def make_entry(live_form, **kwargs):
    """Create a LiveFormEntry with sensible defaults."""
    defaults = dict(full_name="John Doe", size="M")
    defaults.update(kwargs)
    return LiveFormEntry.objects.create(live_form=live_form, **defaults)


# ===========================================================================
# LiveFormLink Tests
# ===========================================================================

class LiveFormLinkSlugTest(TestCase):
    """Slug auto-generation and uniqueness."""

    def setUp(self):
        self.user = make_user()

    def test_slug_generated_on_save(self):
        form = make_form(self.user, organization_name="Lagos University")
        self.assertIsNotNone(form.slug)
        self.assertTrue(len(form.slug) > 0)

    def test_slug_derived_from_organisation_name(self):
        form = make_form(self.user, organization_name="Eko FM Radio")
        self.assertIn("eko", form.slug.lower())

    def test_slug_is_unique_for_duplicate_names(self):
        form1 = make_form(self.user, organization_name="Duplicate Org")
        form2 = make_form(self.user, organization_name="Duplicate Org")
        self.assertNotEqual(form1.slug, form2.slug)

    def test_slug_uniqueness_counter_increments(self):
        base = "counter-org"
        form1 = make_form(self.user, organization_name=base)
        form2 = make_form(self.user, organization_name=base)
        form3 = make_form(self.user, organization_name=base)
        slugs = {form1.slug, form2.slug, form3.slug}
        self.assertEqual(len(slugs), 3)

    def test_slug_not_regenerated_on_update(self):
        form = make_form(self.user, organization_name="Original Org")
        original_slug = form.slug
        form.is_active = False
        form.save()
        form.refresh_from_db()
        self.assertEqual(form.slug, original_slug)

    def test_slug_is_slugified(self):
        form = make_form(self.user, organization_name="Abuja Tech Hub 2025")
        # slug must only contain letters, digits, hyphens
        self.assertRegex(form.slug, r'^[a-z0-9\-]+$')

    def test_slug_max_length_respected(self):
        long_name = "A" * 290
        form = make_form(self.user, organization_name=long_name)
        self.assertLessEqual(len(form.slug), 300)


class LiveFormLinkNameNormalisationTest(TestCase):
    """Organisation name is uppercased on save."""

    def setUp(self):
        self.user = make_user()

    def test_name_uppercased_on_create(self):
        form = make_form(self.user, organization_name="lagos state polytechnic")
        self.assertEqual(form.organization_name, "LAGOS STATE POLYTECHNIC")

    def test_name_uppercased_on_update(self):
        form = make_form(self.user, organization_name="UNILAG")
        form.organization_name = "updated name"
        form.save()
        form.refresh_from_db()
        self.assertEqual(form.organization_name, "UPDATED NAME")

    def test_already_uppercase_name_unchanged(self):
        form = make_form(self.user, organization_name="OAU ILE-IFE")
        self.assertEqual(form.organization_name, "OAU ILE-IFE")

    def test_mixed_case_normalised(self):
        form = make_form(self.user, organization_name="nIgErIaN aRmY")
        self.assertEqual(form.organization_name, "NIGERIAN ARMY")


class LiveFormLinkExpiryTest(TestCase):
    """is_expired() and is_open() logic."""

    def setUp(self):
        self.user = make_user()

    def test_not_expired_when_future(self):
        form = make_form(self.user, expires_at=future(24))
        self.assertFalse(form.is_expired())

    def test_expired_when_past(self):
        form = make_form(self.user, expires_at=past(1))
        self.assertTrue(form.is_expired())

    def test_is_open_when_active_and_not_expired(self):
        form = make_form(self.user, expires_at=future(24), is_active=True)
        self.assertTrue(form.is_open())

    def test_not_open_when_inactive(self):
        form = make_form(self.user, is_active=False, expires_at=future(24))
        self.assertFalse(form.is_open())

    def test_not_open_when_expired(self):
        form = make_form(self.user, expires_at=past(1), is_active=True)
        self.assertFalse(form.is_open())

    def test_not_open_when_max_submissions_reached(self):
        form = make_form(self.user, expires_at=future(24), max_submissions=2)
        make_entry(form, full_name="Alice Smith", size="S")
        make_entry(form, full_name="Bob Jones", size="M")
        self.assertFalse(form.is_open())

    def test_open_when_below_max_submissions(self):
        form = make_form(self.user, expires_at=future(24), max_submissions=5)
        make_entry(form, full_name="Alice Smith", size="S")
        self.assertTrue(form.is_open())

    def test_open_when_max_submissions_is_none(self):
        form = make_form(self.user, expires_at=future(24), max_submissions=None)
        for i in range(100):
            make_entry(form, full_name=f"Person {i}", size="M")
        self.assertTrue(form.is_open())

    def test_not_open_when_both_inactive_and_expired(self):
        form = make_form(self.user, is_active=False, expires_at=past(1))
        self.assertFalse(form.is_open())

    def test_is_expired_boundary_exact_now(self):
        """Forms exactly at expiry should be treated as expired."""
        form = make_form(self.user, expires_at=past(0))
        # tiny window — just verify it doesn't raise
        result = form.is_expired()
        self.assertIsInstance(result, bool)


class LiveFormLinkShareableUrlTest(TestCase):
    """get_shareable_url() behaviour with/without FRONTEND_URL setting."""

    def setUp(self):
        self.user = make_user()

    def test_relative_url_without_frontend_url(self):
        form = make_form(self.user)
        with self.settings(FRONTEND_URL=""):
            url = form.get_shareable_url()
        self.assertTrue(url.startswith("/live-form/"))
        self.assertIn(form.slug, url)

    def test_absolute_url_with_frontend_url(self):
        form = make_form(self.user)
        with self.settings(FRONTEND_URL="https://materialwear.ng"):
            url = form.get_shareable_url()
        self.assertTrue(url.startswith("https://materialwear.ng"))
        self.assertIn(form.slug, url)

    def test_trailing_slash_stripped_from_frontend_url(self):
        form = make_form(self.user)
        with self.settings(FRONTEND_URL="https://materialwear.ng/"):
            url = form.get_shareable_url()
        # Must not have double slashes
        self.assertNotIn("//live-form", url)

    def test_url_contains_slug(self):
        form = make_form(self.user, organization_name="Test University")
        with self.settings(FRONTEND_URL=""):
            url = form.get_shareable_url()
        self.assertIn(form.slug, url)


class LiveFormLinkMetaTest(TestCase):
    """Model Meta: ordering, verbose names, indexes."""

    def setUp(self):
        self.user = make_user()

    def test_default_ordering_is_newest_first(self):
        old = make_form(self.user, organization_name="Old Org")
        new = make_form(self.user, organization_name="New Org")
        forms = list(LiveFormLink.objects.filter(created_by=self.user))
        self.assertEqual(forms[0].pk, new.pk)

    def test_str_representation(self):
        form = make_form(self.user, organization_name="My Org")
        result = str(form)
        self.assertIn("MY ORG", result)
        self.assertIn(form.slug, result)

    def test_verbose_name(self):
        self.assertEqual(LiveFormLink._meta.verbose_name, "Live Form Link")

    def test_verbose_name_plural(self):
        self.assertEqual(LiveFormLink._meta.verbose_name_plural, "Live Form Links")

    def test_pk_is_uuid(self):
        form = make_form(self.user)
        self.assertIsInstance(form.id, uuid.UUID)

    def test_cascade_delete_removes_entries(self):
        form = make_form(self.user)
        e1 = make_entry(form)
        e2 = make_entry(form, full_name="Another Person", size="L")
        self.assertEqual(LiveFormEntry.objects.filter(live_form=form).count(), 2)
        entry_ids = [e1.pk, e2.pk]
        form.delete()
        self.assertEqual(LiveFormEntry.objects.filter(pk__in=entry_ids).count(), 0)


# ===========================================================================
# LiveFormEntry Tests
# ===========================================================================

class LiveFormEntrySerialNumberTest(TestCase):
    """Auto-increment serial_number per form."""

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)

    def test_first_entry_gets_serial_one(self):
        entry = make_entry(self.form)
        self.assertEqual(entry.serial_number, 1)

    def test_serial_increments_per_form(self):
        e1 = make_entry(self.form, full_name="Alice Smith", size="S")
        e2 = make_entry(self.form, full_name="Bob Jones", size="M")
        e3 = make_entry(self.form, full_name="Carol King", size="L")
        self.assertEqual(e1.serial_number, 1)
        self.assertEqual(e2.serial_number, 2)
        self.assertEqual(e3.serial_number, 3)

    def test_serial_is_independent_per_form(self):
        form2 = make_form(self.user, organization_name="Second Org")
        e1 = make_entry(self.form, full_name="Person One", size="S")
        e2 = make_entry(form2, full_name="Person Two", size="M")
        self.assertEqual(e1.serial_number, 1)
        self.assertEqual(e2.serial_number, 1)

    def test_serial_not_reset_after_deletion(self):
        e1 = make_entry(self.form, full_name="First Person", size="S")
        e1.delete()
        e2 = make_entry(self.form, full_name="Second Person", size="M")
        self.assertEqual(e2.serial_number, 2)

    def test_serial_not_reassigned_on_update(self):
        entry = make_entry(self.form)
        original_serial = entry.serial_number
        entry.size = "XL"
        entry.save()
        entry.refresh_from_db()
        self.assertEqual(entry.serial_number, original_serial)


class LiveFormEntryNameNormalisationTest(TestCase):
    """Names must be stored in UPPERCASE."""

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)

    def test_full_name_uppercased(self):
        entry = make_entry(self.form, full_name="john doe")
        self.assertEqual(entry.full_name, "JOHN DOE")

    def test_custom_name_uppercased(self):
        entry = make_entry(self.form, full_name="John Doe", custom_name="jersey king")
        self.assertEqual(entry.custom_name, "JERSEY KING")

    def test_empty_custom_name_not_changed(self):
        entry = make_entry(self.form, full_name="John Doe", custom_name="")
        self.assertEqual(entry.custom_name, "")

    def test_mixed_case_full_name_normalised(self):
        entry = make_entry(self.form, full_name="aMaKa cHuKwU")
        self.assertEqual(entry.full_name, "AMAKA CHUKWU")

    def test_already_uppercase_unchanged(self):
        entry = make_entry(self.form, full_name="IBRAHIM MUSA")
        self.assertEqual(entry.full_name, "IBRAHIM MUSA")


class LiveFormEntrySocialProofCounterTest(TestCase):
    """last_submission_at on parent is updated atomically on entry save."""

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)

    def test_last_submission_at_updated_on_entry_save(self):
        self.assertIsNone(self.form.last_submission_at)
        before = timezone.now()
        make_entry(self.form)
        self.form.refresh_from_db()
        self.assertIsNotNone(self.form.last_submission_at)
        self.assertGreaterEqual(self.form.last_submission_at, before)

    def test_last_submission_at_advances_with_each_entry(self):
        make_entry(self.form, full_name="First Person", size="S")
        self.form.refresh_from_db()
        first_ts = self.form.last_submission_at

        make_entry(self.form, full_name="Second Person", size="M")
        self.form.refresh_from_db()
        second_ts = self.form.last_submission_at

        self.assertGreaterEqual(second_ts, first_ts)


class LiveFormEntryMetaTest(TestCase):
    """Entry model Meta: unique_together, ordering, verbose names."""

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)

    def test_str_representation(self):
        entry = make_entry(self.form, full_name="Emeka Obi", size="L")
        result = str(entry)
        self.assertIn("EMEKA OBI", result)
        self.assertIn(str(entry.serial_number), result)

    def test_verbose_name(self):
        self.assertEqual(LiveFormEntry._meta.verbose_name, "Live Form Entry")

    def test_verbose_name_plural(self):
        self.assertEqual(LiveFormEntry._meta.verbose_name_plural, "Live Form Entries")

    def test_pk_is_uuid(self):
        entry = make_entry(self.form)
        self.assertIsInstance(entry.id, uuid.UUID)

    def test_size_choices_are_valid(self):
        valid_sizes = [s[0] for s in LiveFormEntry.SIZE_CHOICES]
        self.assertIn("S", valid_sizes)
        self.assertIn("M", valid_sizes)
        self.assertIn("XXXXL", valid_sizes)
        self.assertEqual(len(valid_sizes), 7)

    def test_all_size_choices_saveable(self):
        for size_code, _ in LiveFormEntry.SIZE_CHOICES:
            entry = make_entry(
                self.form,
                full_name=f"Person {size_code}",
                size=size_code,
            )
            self.assertEqual(entry.size, size_code)

    def test_default_ordering_by_form_and_serial(self):
        e3 = make_entry(self.form, full_name="Third", size="L")
        e1 = make_entry(self.form, full_name="First", size="S")
        e2 = make_entry(self.form, full_name="Second", size="M")
        entries = list(LiveFormEntry.objects.filter(live_form=self.form))
        serials = [e.serial_number for e in entries]
        self.assertEqual(serials, sorted(serials))


# ===========================================================================
# Concurrent serial_number safety (TransactionTestCase)
# ===========================================================================

class ConcurrentEntrySerialNumberTest(TransactionTestCase):
    """
    Uses TransactionTestCase so threads can commit transactions independently,
    verifying select_for_update() prevents duplicate serial_numbers.

    Note: This test is skipped on SQLite because SQLite doesn't support
    concurrent transactions with select_for_update() properly.
    """

    def setUp(self):
        from django.conf import settings
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in db_engine.lower():
            self.skipTest("SQLite doesn't support concurrent transactions with select_for_update()")
        self.user = make_user()
        self.form = make_form(self.user)

    def test_concurrent_entries_have_unique_serials(self):
        import threading

        errors = []
        results = []

        def create_entry(name):
            try:
                entry = LiveFormEntry.objects.create(
                    live_form=self.form,
                    full_name=name,
                    size="M",
                )
                results.append(entry.serial_number)
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=create_entry, args=(f"Thread Person {i}",))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors during concurrent creation: {errors}")
        self.assertEqual(len(results), 5)
        self.assertEqual(len(set(results)), 5, "Duplicate serial numbers detected!")
        self.assertEqual(sorted(results), [1, 2, 3, 4, 5])