"""
Comprehensive tests for referrals/serializers.py

Covers:
- ReferrerProfileSerializer (create, update, duplicate prevention, read-only fields)
- PromotionalMediaSerializer (get_created_by_name fallback chain, media_url)
- SharePayloadSerializer (field presence and types)
"""

from unittest.mock import MagicMock, patch
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory

from referrals.models import ReferrerProfile, PromotionalMedia
from referrals.serializers import (
    ReferrerProfileSerializer,
    PromotionalMediaSerializer,
    SharePayloadSerializer,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(email="user@example.com", password="pass1234!", **kwargs):
    username = kwargs.pop("username", email)
    return User.objects.create_user(username=username, email=email, password=password, **kwargs)


def make_profile(user, **kwargs):
    defaults = dict(
        full_name="Test User",
        phone_number="+2348012345678",
        bank_name="GTBank",
        account_number="0123456789",
    )
    defaults.update(kwargs)
    return ReferrerProfile.objects.create(user=user, **defaults)


def make_media(admin, **kwargs):
    defaults = dict(
        title="Promo",
        media_type="flyer",
        marketing_text="Buy now!",
    )
    defaults.update(kwargs)
    return PromotionalMedia.objects.create(created_by=admin, **defaults)


def fake_request(user):
    """Return a minimal mock request carrying a user."""
    rf = APIRequestFactory()
    req = rf.get("/")
    req.user = user
    return req


# ---------------------------------------------------------------------------
# ReferrerProfileSerializer
# ---------------------------------------------------------------------------

class ReferrerProfileSerializerCreateTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.request = fake_request(self.user)

    def _valid_data(self):
        return {
            "full_name": "Ada Lovelace",
            "phone_number": "+2348012345678",
            "bank_name": "Zenith Bank",
            "account_number": "1234567890",
        }

    def test_creates_profile_for_authenticated_user(self):
        serializer = ReferrerProfileSerializer(
            data=self._valid_data(),
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        profile = serializer.save()
        self.assertEqual(profile.user, self.user)

    def test_referral_code_is_auto_generated_on_create(self):
        serializer = ReferrerProfileSerializer(
            data=self._valid_data(),
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid())
        profile = serializer.save()
        self.assertEqual(len(profile.referral_code), 8)

    def test_duplicate_profile_raises_validation_error(self):
        make_profile(self.user)  # first profile already exists
        serializer = ReferrerProfileSerializer(
            data=self._valid_data(),
            context={"request": self.request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)

    def test_missing_required_full_name_raises_error(self):
        data = self._valid_data()
        data.pop("full_name")
        serializer = ReferrerProfileSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("full_name", serializer.errors)

    def test_missing_phone_number_raises_error(self):
        data = self._valid_data()
        data.pop("phone_number")
        serializer = ReferrerProfileSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

    def test_missing_bank_name_raises_error(self):
        data = self._valid_data()
        data.pop("bank_name")
        serializer = ReferrerProfileSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("bank_name", serializer.errors)

    def test_missing_account_number_raises_error(self):
        data = self._valid_data()
        data.pop("account_number")
        serializer = ReferrerProfileSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("account_number", serializer.errors)

    def test_invalid_phone_number_rejected(self):
        data = self._valid_data()
        data["phone_number"] = "not-a-number"
        serializer = ReferrerProfileSerializer(
            data=data, context={"request": self.request}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

    def test_read_only_fields_ignored_on_input(self):
        """Supplying id, referral_code, created_at in input should be silently ignored."""
        data = self._valid_data()
        data["referral_code"] = "HARDCODE"
        data["id"] = "00000000-0000-0000-0000-000000000000"
        serializer = ReferrerProfileSerializer(
            data=data, context={"request": self.request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        profile = serializer.save()
        self.assertNotEqual(str(profile.id), "00000000-0000-0000-0000-000000000000")
        self.assertNotEqual(profile.referral_code, "HARDCODE")

    def test_user_field_in_output(self):
        profile = make_profile(self.user)
        serializer = ReferrerProfileSerializer(
            profile, context={"request": self.request}
        )
        # user field is read-only on output
        self.assertEqual(serializer.data["user_email"], self.user.email)

    def test_output_contains_expected_fields(self):
        profile = make_profile(self.user)
        serializer = ReferrerProfileSerializer(
            profile, context={"request": self.request}
        )
        expected_fields = {
            "id", "user", "user_email", "referral_code", "full_name",
            "phone_number", "bank_name", "account_number", "is_active",
            "created_at", "updated_at",
        }
        self.assertEqual(set(serializer.data.keys()), expected_fields)


class ReferrerProfileSerializerUpdateTests(TestCase):

    def setUp(self):
        self.user = make_user()
        self.profile = make_profile(self.user)
        self.request = fake_request(self.user)

    def test_partial_update_allows_missing_fields(self):
        serializer = ReferrerProfileSerializer(
            self.profile,
            data={"full_name": "Updated Name"},
            partial=True,
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated = serializer.save()
        self.assertEqual(updated.full_name, "Updated Name")

    def test_full_update_requires_all_fields(self):
        serializer = ReferrerProfileSerializer(
            self.profile,
            data={"full_name": "Updated"},  # missing phone, bank, account
            partial=False,
            context={"request": self.request},
        )
        self.assertFalse(serializer.is_valid())

    def test_update_does_not_trigger_duplicate_check(self):
        """validate() should skip the duplicate check for existing instances."""
        serializer = ReferrerProfileSerializer(
            self.profile,
            data={
                "full_name": "Same User Updated",
                "phone_number": "+2348000000001",
                "bank_name": "New Bank",
                "account_number": "9999999999",
            },
            partial=False,
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_referral_code_unchanged_after_update(self):
        original_code = self.profile.referral_code
        serializer = ReferrerProfileSerializer(
            self.profile,
            data={"bank_name": "New Bank"},
            partial=True,
            context={"request": self.request},
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.referral_code, original_code)


# ---------------------------------------------------------------------------
# PromotionalMediaSerializer
# ---------------------------------------------------------------------------

class PromotionalMediaSerializerTests(TestCase):

    def setUp(self):
        self.admin = make_user(
            email="admin@example.com",
            is_staff=True,
            first_name="John",
            last_name="Admin",
        )

    def test_output_contains_expected_fields(self):
        media = make_media(self.admin)
        serializer = PromotionalMediaSerializer(media)
        expected = {
            "id", "title", "media_type", "media_file", "media_url",
            "marketing_text", "is_active", "order", "created_at",
            "updated_at", "created_by_name",
        }
        self.assertEqual(set(serializer.data.keys()), expected)

    def test_get_created_by_name_returns_full_name(self):
        media = make_media(self.admin)
        serializer = PromotionalMediaSerializer(media)
        self.assertEqual(serializer.data["created_by_name"], "John Admin")

    def test_get_created_by_name_falls_back_to_username(self):
        """When get_full_name() is blank but username exists."""
        user = make_user(email="noname@example.com", is_staff=True)
        # email-based user model may not have username; use email fallback
        media = make_media(user)
        serializer = PromotionalMediaSerializer(media)
        name = serializer.data["created_by_name"]
        self.assertIsNotNone(name)
        self.assertGreater(len(name), 0)

    def test_get_created_by_name_returns_none_when_no_creator(self):
        media = make_media(self.admin)
        media.created_by = None
        media.save()
        serializer = PromotionalMediaSerializer(media)
        self.assertIsNone(serializer.data["created_by_name"])

    def test_media_url_is_none_when_no_file(self):
        media = make_media(self.admin, media_file=None)
        serializer = PromotionalMediaSerializer(media)
        # media_url is a read-only CharField; None serializes to null
        self.assertIsNone(serializer.data["media_url"])

    def test_media_type_choices_flyer_valid(self):
        request = fake_request(self.admin)
        data = {
            "title": "Test",
            "media_type": "flyer",
            "marketing_text": "text",
            "is_active": True,
            "order": 0,
        }
        serializer = PromotionalMediaSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_media_type_choices_video_valid(self):
        data = {
            "title": "Test",
            "media_type": "video",
            "marketing_text": "text",
        }
        serializer = PromotionalMediaSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_media_type_rejected(self):
        data = {
            "title": "Test",
            "media_type": "audio",  # invalid
            "marketing_text": "text",
        }
        serializer = PromotionalMediaSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("media_type", serializer.errors)

    def test_read_only_fields_not_writable(self):
        """id, created_at, updated_at, media_url should be ignored on write."""
        data = {
            "id": "00000000-0000-0000-0000-000000000000",
            "title": "Test",
            "media_type": "flyer",
            "marketing_text": "text",
            "media_url": "https://fake.url/image.jpg",
        }
        serializer = PromotionalMediaSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        # media_url should not appear in validated_data
        self.assertNotIn("media_url", serializer.validated_data)


# ---------------------------------------------------------------------------
# SharePayloadSerializer
# ---------------------------------------------------------------------------

class SharePayloadSerializerTests(TestCase):

    def _make_payload(self, **kwargs):
        defaults = {
            "promotional_media": [],
            "referral_code": "ABC12345",
            "whatsapp_link": "https://wa.me/2348012345678?text=Hello",
            "share_message": "Buy stuff! Use code ABC12345",
        }
        defaults.update(kwargs)
        return defaults

    def test_serializer_accepts_valid_payload(self):
        serializer = SharePayloadSerializer(data=self._make_payload())
        # SharePayloadSerializer is read-only; its fields are all read_only
        # so it is mainly used for output — validate the shape when used as output
        payload = self._make_payload()
        serializer = SharePayloadSerializer(payload)
        self.assertIn("referral_code", serializer.data)
        self.assertIn("whatsapp_link", serializer.data)
        self.assertIn("share_message", serializer.data)
        self.assertIn("promotional_media", serializer.data)

    def test_referral_code_present(self):
        payload = self._make_payload(referral_code="XYZXYZ12")
        serializer = SharePayloadSerializer(payload)
        self.assertEqual(serializer.data["referral_code"], "XYZXYZ12")

    def test_whatsapp_link_present(self):
        link = "https://wa.me/2348099999999?text=Hello%20World"
        payload = self._make_payload(whatsapp_link=link)
        serializer = SharePayloadSerializer(payload)
        self.assertEqual(serializer.data["whatsapp_link"], link)

    def test_share_message_present(self):
        msg = "Special offer! Use my code: TEST1234"
        payload = self._make_payload(share_message=msg)
        serializer = SharePayloadSerializer(payload)
        self.assertEqual(serializer.data["share_message"], msg)

    def test_promotional_media_list_present(self):
        payload = self._make_payload(promotional_media=[])
        serializer = SharePayloadSerializer(payload)
        self.assertEqual(serializer.data["promotional_media"], [])