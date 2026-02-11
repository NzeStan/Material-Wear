"""
Comprehensive tests for referrals/models.py

Covers:
- generate_referral_code() function
- ReferrerProfile model (creation, constraints, validation, __str__, save logic)
- PromotionalMedia model (creation, choices, media_url property, __str__)
"""

import uuid
import string
from unittest.mock import patch, MagicMock, PropertyMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.utils import DataError

from referrals.models import ReferrerProfile, PromotionalMedia, generate_referral_code

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email="user@example.com", password="pass1234!", **kwargs):
    username = kwargs.pop("username", email)
    return User.objects.create_user(username=username, email=email, password=password, **kwargs)


def make_profile(user, **kwargs):
    defaults = dict(
        full_name="Test Referrer",
        phone_number="+2348012345678",
        bank_name="Access Bank",
        account_number="0123456789",
    )
    defaults.update(kwargs)
    return ReferrerProfile.objects.create(user=user, **defaults)


def make_media(admin_user, **kwargs):
    defaults = dict(
        title="Summer Promo",
        media_type="flyer",
        marketing_text="Buy NYSC uniforms here!",
    )
    defaults.update(kwargs)
    return PromotionalMedia.objects.create(created_by=admin_user, **defaults)


# ---------------------------------------------------------------------------
# generate_referral_code()
# ---------------------------------------------------------------------------

class GenerateReferralCodeTests(TestCase):

    def test_code_is_8_characters(self):
        code = generate_referral_code()
        self.assertEqual(len(code), 8)

    def test_code_is_uppercase_alphanumeric(self):
        allowed = set(string.ascii_uppercase + string.digits)
        for _ in range(50):
            code = generate_referral_code()
            self.assertTrue(set(code).issubset(allowed),
                            f"Code '{code}' contains invalid characters.")

    def test_codes_are_unique_across_multiple_calls(self):
        codes = {generate_referral_code() for _ in range(200)}
        # Statistically impossible to get fewer than 190 unique codes in 200 calls
        self.assertGreater(len(codes), 190)

    def test_code_regenerated_when_duplicate_exists(self):
        """
        If the first generated code already exists, a new one should be produced.
        We force a collision on the first call, verify the loop retries.
        """
        user = make_user()
        existing = make_profile(user)  # creates a profile with a real code
        collision_code = existing.referral_code

        call_count = {"n": 0}
        original_choice = __import__("secrets").choice

        def fake_choice(seq):
            # Force the first 8 calls (one code attempt) to spell the existing code
            call_count["n"] += 1
            idx = (call_count["n"] - 1) % 8
            if call_count["n"] <= 8:
                return collision_code[idx]
            return original_choice(seq)

        with patch("referrals.models.secrets.choice", side_effect=fake_choice):
            new_code = generate_referral_code()

        # The new code must NOT equal the collision code
        self.assertNotEqual(new_code, collision_code)


# ---------------------------------------------------------------------------
# ReferrerProfile — creation & fields
# ---------------------------------------------------------------------------

class ReferrerProfileCreationTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_create_profile_succeeds_with_valid_data(self):
        profile = make_profile(self.user)
        self.assertIsNotNone(profile.pk)
        self.assertIsInstance(profile.id, uuid.UUID)

    def test_referral_code_auto_generated(self):
        profile = make_profile(self.user)
        self.assertTrue(profile.referral_code)
        self.assertEqual(len(profile.referral_code), 8)

    def test_referral_code_is_unique_constraint(self):
        user2 = make_user(email="user2@example.com")
        profile1 = make_profile(self.user)
        profile2 = make_profile(user2)
        self.assertNotEqual(profile1.referral_code, profile2.referral_code)

    def test_duplicate_referral_code_raises_integrity_error(self):
        profile = make_profile(self.user)
        user2 = make_user(email="user2@example.com")
        with self.assertRaises(IntegrityError):
            ReferrerProfile.objects.create(
                user=user2,
                referral_code=profile.referral_code,  # duplicate!
                full_name="Another",
                phone_number="+2348011111111",
                bank_name="GT Bank",
                account_number="0987654321",
            )

    def test_one_to_one_user_constraint(self):
        make_profile(self.user)
        with self.assertRaises(IntegrityError):
            ReferrerProfile.objects.create(
                user=self.user,  # same user — violates OneToOneField
                full_name="Duplicate",
                phone_number="+2348099999999",
                bank_name="Zenith",
                account_number="1111111111",
            )

    def test_cascade_delete_when_user_deleted(self):
        profile_pk = make_profile(self.user).pk
        self.user.delete()
        self.assertFalse(ReferrerProfile.objects.filter(pk=profile_pk).exists())

    def test_is_active_defaults_to_true(self):
        profile = make_profile(self.user)
        self.assertTrue(profile.is_active)

    def test_can_deactivate_profile(self):
        profile = make_profile(self.user, is_active=False)
        self.assertFalse(profile.is_active)

    def test_created_at_and_updated_at_auto_set(self):
        profile = make_profile(self.user)
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)

    def test_str_representation(self):
        profile = make_profile(self.user, full_name="Ada Lovelace")
        expected = f"Ada Lovelace ({profile.referral_code})"
        self.assertEqual(str(profile), expected)

    def test_ordering_is_newest_first(self):
        user2 = make_user(email="u2@example.com")
        user3 = make_user(email="u3@example.com")
        p1 = make_profile(self.user)
        p2 = make_profile(user2)
        p3 = make_profile(user3)
        profiles = list(ReferrerProfile.objects.all())
        # newest created first
        self.assertEqual(profiles[0].pk, p3.pk)
        self.assertEqual(profiles[2].pk, p1.pk)

    def test_meta_verbose_names(self):
        self.assertEqual(ReferrerProfile._meta.verbose_name, "Referrer Profile")
        self.assertEqual(ReferrerProfile._meta.verbose_name_plural, "Referrer Profiles")

    def test_save_generates_code_if_missing(self):
        """Model.save() should generate a code even if one wasn't provided."""
        profile = ReferrerProfile(
            user=self.user,
            full_name="NoCode User",
            phone_number="+2348000000001",
            bank_name="Fidelity",
            account_number="5555555555",
        )
        # Force the code to be empty before save
        profile.referral_code = ""
        profile.save()
        self.assertTrue(profile.referral_code)

    def test_full_name_max_length(self):
        long_name = "A" * 256  # one over the 255 limit
        profile = ReferrerProfile(
            user=self.user,
            full_name=long_name,
            phone_number="+2348000000001",
            bank_name="Bank",
            account_number="1234567890",
        )
        with self.assertRaises(Exception):
            profile.full_clean()

    def test_account_number_max_length(self):
        profile = ReferrerProfile(
            user=self.user,
            full_name="Test",
            phone_number="+2348000000001",
            bank_name="Bank",
            account_number="1" * 21,  # one over the 20-char limit
        )
        with self.assertRaises(Exception):
            profile.full_clean()


# ---------------------------------------------------------------------------
# Phone Number Validation
# ---------------------------------------------------------------------------

class PhoneNumberValidationTests(TestCase):

    def setUp(self):
        self.user = make_user()

    def _make(self, phone):
        return ReferrerProfile(
            user=self.user,
            full_name="Test",
            phone_number=phone,
            bank_name="Bank",
            account_number="0123456789",
        )

    def test_valid_phone_with_plus(self):
        obj = self._make("+2348012345678")
        obj.full_clean()  # should not raise

    def test_valid_phone_digits_only(self):
        obj = self._make("08012345678")
        obj.full_clean()

    def test_invalid_phone_too_short(self):
        obj = self._make("+123")
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_invalid_phone_with_letters(self):
        obj = self._make("080ABCDEFGH")
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_invalid_phone_with_spaces(self):
        obj = self._make("+234 801 234 5678")
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_invalid_phone_too_long(self):
        # 18 chars: +1 + 16 digits. Regex allows max 15 trailing digits after \+?1?,
        # and max_length=17 also rejects anything >= 18 chars.
        obj = self._make("+12345678901234567")
        with self.assertRaises(ValidationError):
            obj.full_clean()


# ---------------------------------------------------------------------------
# PromotionalMedia model
# ---------------------------------------------------------------------------

class PromotionalMediaCreationTests(TestCase):

    def setUp(self):
        self.admin = make_user(email="admin@example.com", is_staff=True)

    def test_create_flyer(self):
        media = make_media(self.admin)
        self.assertIsNotNone(media.pk)
        self.assertIsInstance(media.id, uuid.UUID)
        self.assertEqual(media.media_type, "flyer")

    def test_create_video(self):
        media = make_media(self.admin, media_type="video")
        self.assertEqual(media.media_type, "video")

    def test_str_representation(self):
        media = make_media(self.admin, title="NYSC Flyer")
        self.assertIn("NYSC Flyer", str(media))
        self.assertIn("Flyer", str(media))

    def test_is_active_defaults_to_true(self):
        media = make_media(self.admin)
        self.assertTrue(media.is_active)

    def test_order_defaults_to_zero(self):
        media = make_media(self.admin)
        self.assertEqual(media.order, 0)

    def test_ordering_by_order_then_created_at(self):
        m1 = make_media(self.admin, title="B", order=2)
        m2 = make_media(self.admin, title="A", order=1)
        m3 = make_media(self.admin, title="C", order=0)
        items = list(PromotionalMedia.objects.all())
        self.assertEqual(items[0].pk, m3.pk)  # order=0 first
        self.assertEqual(items[1].pk, m2.pk)  # order=1 second

    def test_created_by_set_null_on_user_delete(self):
        admin2 = make_user(email="admin2@example.com", is_staff=True)
        media = make_media(admin2)
        admin2.delete()
        media.refresh_from_db()
        self.assertIsNone(media.created_by)

    def test_media_url_property_returns_none_when_no_file(self):
        media = make_media(self.admin, media_file=None)
        self.assertIsNone(media.media_url)

    def test_media_url_property_returns_url_when_file_set(self):
        media = make_media(self.admin)
        mock_file = MagicMock()
        mock_file.url = "https://res.cloudinary.com/test/image/upload/v1/test.jpg"
        media.media_file = mock_file
        self.assertEqual(media.media_url, mock_file.url)

    def test_meta_verbose_names(self):
        self.assertEqual(PromotionalMedia._meta.verbose_name, "Promotional Media")
        self.assertEqual(PromotionalMedia._meta.verbose_name_plural, "Promotional Media")

    def test_invalid_media_type_raises_on_clean(self):
        media = PromotionalMedia(
            title="Bad type",
            media_type="pdf",  # not a valid choice
            marketing_text="text",
            created_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            media.full_clean()

    def test_title_max_length(self):
        media = PromotionalMedia(
            title="T" * 256,
            media_type="flyer",
            marketing_text="text",
            created_by=self.admin,
        )
        with self.assertRaises(Exception):
            media.full_clean()

    def test_created_at_updated_at_auto_populated(self):
        media = make_media(self.admin)
        self.assertIsNotNone(media.created_at)
        self.assertIsNotNone(media.updated_at)

    def test_can_have_multiple_media_by_different_admins(self):
        admin2 = make_user(email="admin2@example.com", is_staff=True)
        m1 = make_media(self.admin)
        m2 = make_media(admin2)
        self.assertEqual(PromotionalMedia.objects.count(), 2)
        self.assertNotEqual(m1.pk, m2.pk)