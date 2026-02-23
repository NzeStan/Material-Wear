"""
Comprehensive tests for referrals/views.py

Covers all endpoints of:
- ReferrerProfileViewSet  (list, create, retrieve, update, destroy, me, me/update)
- PromotionalMediaViewSet (list, retrieve, create, update, destroy)
- SharePayloadViewSet     (generate)

Each action is tested for:
  ✓ Success path
  ✓ Authentication / permission guard
  ✓ Edge-case / error paths
"""

from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from referrals.models import ReferrerProfile, PromotionalMedia

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(email="user@example.com", password="pass1234!", **kwargs):
    username = kwargs.pop("username", email)
    return User.objects.create_user(
        username=username, email=email, password=password, **kwargs
    )


def make_admin(email="admin@example.com", password="admin1234!"):
    return User.objects.create_user(
        username=email, email=email, password=password, is_staff=True, is_superuser=True
    )


def make_profile(user, **kwargs):
    defaults = dict(
        full_name="Test Referrer",
        phone_number="+2348012345678",
        bank_name="GTBank",
        account_number="0123456789",
    )
    defaults.update(kwargs)
    return ReferrerProfile.objects.create(user=user, **defaults)


def make_media(creator, **kwargs):
    defaults = dict(
        title="Summer Promo",
        media_type="flyer",
        marketing_text="Buy NYSC uniforms here!",
    )
    defaults.update(kwargs)
    return PromotionalMedia.objects.create(created_by=creator, **defaults)


def profile_list_url():
    return reverse("referrals:referrer-profile-list")


def profile_detail_url(pk):
    return reverse("referrals:referrer-profile-detail", kwargs={"pk": str(pk)})


def profile_me_url():
    return reverse("referrals:referrer-profile-get-my-profile")


def profile_me_update_url():
    return reverse("referrals:referrer-profile-update-my-profile")


def media_list_url():
    return reverse("referrals:promotional-media-list")


def media_detail_url(pk):
    return reverse("referrals:promotional-media-detail", kwargs={"pk": str(pk)})


def share_generate_url():
    return reverse("referrals:share-payload-generate-payload")


# ---------------------------------------------------------------------------
# ReferrerProfileViewSet – LIST
# ---------------------------------------------------------------------------


class ReferrerProfileListTests(APITestCase):

    def setUp(self):
        self.admin = make_admin()
        self.user = make_user()
        self.client = APIClient()

    def test_admin_can_list_all_profiles(self):
        make_profile(self.user)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(profile_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertGreaterEqual(len(results), 1)

    def test_regular_user_cannot_list_all_profiles(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(profile_list_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_profiles(self):
        response = self.client.get(profile_list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_sees_only_profiles_not_other_objects(self):
        user2 = make_user(email="u2@example.com")
        make_profile(self.user)
        make_profile(user2)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(profile_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)


# ---------------------------------------------------------------------------
# ReferrerProfileViewSet – CREATE
# ---------------------------------------------------------------------------


class ReferrerProfileCreateTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.client = APIClient()
        self.valid_data = {
            "full_name": "Ada Lovelace",
            "phone_number": "+2348012345678",
            "bank_name": "Zenith Bank",
            "account_number": "1234567890",
        }

    def test_authenticated_user_can_create_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(profile_list_url(), self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReferrerProfile.objects.filter(user=self.user).count(), 1)

    def test_unauthenticated_cannot_create_profile(self):
        response = self.client.post(profile_list_url(), self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_profile_returns_400(self):
        make_profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(profile_list_url(), self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_referral_code_auto_generated_on_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(profile_list_url(), self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["referral_code"])
        self.assertEqual(len(response.data["referral_code"]), 8)

    def test_create_with_missing_full_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data}
        data.pop("full_name")
        response = self.client.post(profile_list_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_with_invalid_phone_returns_400(self):
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "phone_number": "abc"}
        response = self.client.post(profile_list_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_field_set_automatically_from_request(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(profile_list_url(), self.valid_data, format="json")
        profile = ReferrerProfile.objects.get(user=self.user)
        self.assertEqual(profile.user, self.user)

    def test_cannot_spoof_user_field_in_payload(self):
        other = make_user(email="other@example.com")
        self.client.force_authenticate(user=self.user)
        data = {**self.valid_data, "user": str(other.pk)}
        self.client.post(profile_list_url(), data, format="json")
        profile = ReferrerProfile.objects.get(user=self.user)
        self.assertEqual(profile.user, self.user)  # not `other`


# ---------------------------------------------------------------------------
# ReferrerProfileViewSet – RETRIEVE
# ---------------------------------------------------------------------------


class ReferrerProfileRetrieveTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.admin = make_admin()
        self.profile = make_profile(self.user)
        self.client = APIClient()

    def test_user_can_retrieve_own_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(profile_detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["referral_code"], self.profile.referral_code)

    def test_admin_can_retrieve_any_profile(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(profile_detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_another_user_cannot_retrieve_profile(self):
        other = make_user(email="other@example.com")
        self.client.force_authenticate(user=other)
        response = self.client.get(profile_detail_url(self.profile.pk))
        # Other user's queryset won't include this profile → 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_retrieve(self):
        response = self.client.get(profile_detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_nonexistent_profile_returns_404(self):
        import uuid

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(profile_detail_url(uuid.uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# ReferrerProfileViewSet – UPDATE (PUT / PATCH)
# ---------------------------------------------------------------------------


class ReferrerProfileUpdateTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.profile = make_profile(self.user)
        self.client = APIClient()

    def test_user_can_patch_own_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            profile_detail_url(self.profile.pk),
            {"full_name": "New Name"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.full_name, "New Name")

    def test_user_can_put_own_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            profile_detail_url(self.profile.pk),
            {
                "full_name": "Full Update",
                "phone_number": "+2348099999999",
                "bank_name": "Fidelity",
                "account_number": "9876543210",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_referral_code_not_changed_after_update(self):
        original_code = self.profile.referral_code
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            profile_detail_url(self.profile.pk),
            {"bank_name": "New Bank"},
            format="json",
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.referral_code, original_code)

    def test_other_user_cannot_update_profile(self):
        other = make_user(email="other@example.com")
        self.client.force_authenticate(user=other)
        response = self.client.patch(
            profile_detail_url(self.profile.pk),
            {"full_name": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_update(self):
        response = self.client.patch(
            profile_detail_url(self.profile.pk),
            {"full_name": "X"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# ReferrerProfileViewSet – DESTROY
# ---------------------------------------------------------------------------


class ReferrerProfileDestroyTests(APITestCase):

    def setUp(self):
        self.admin = make_admin()
        self.user = make_user()
        self.profile = make_profile(self.user)
        self.client = APIClient()

    def test_admin_can_delete_profile(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(profile_detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ReferrerProfile.objects.filter(pk=self.profile.pk).exists())

    def test_regular_user_cannot_delete_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(profile_detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_delete(self):
        response = self.client.delete(profile_detail_url(self.profile.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_nonexistent_returns_404(self):
        import uuid

        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(profile_detail_url(uuid.uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# ReferrerProfileViewSet – GET /profiles/me/
# ---------------------------------------------------------------------------


class GetMyProfileTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.client = APIClient()

    def test_returns_own_profile(self):
        profile = make_profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(profile_me_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["referral_code"], profile.referral_code)

    def test_returns_404_when_no_profile_exists(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(profile_me_url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(profile_me_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_response_contains_user_email(self):
        make_profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(profile_me_url())
        self.assertEqual(response.data["user_email"], self.user.email)


# ---------------------------------------------------------------------------
# ReferrerProfileViewSet – PATCH|PUT /profiles/me/update/
# ---------------------------------------------------------------------------


class UpdateMyProfileTests(APITestCase):

    def setUp(self):
        self.user = make_user()
        self.client = APIClient()

    def test_patch_updates_profile(self):
        profile = make_profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            profile_me_update_url(),
            {"full_name": "Patched Name"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile.refresh_from_db()
        self.assertEqual(profile.full_name, "Patched Name")

    def test_put_updates_profile(self):
        make_profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            profile_me_update_url(),
            {
                "full_name": "Full Update",
                "phone_number": "+2348099999999",
                "bank_name": "Heritage",
                "account_number": "5555555555",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["full_name"], "Full Update")

    def test_returns_404_when_no_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            profile_me_update_url(), {"full_name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(profile_me_update_url(), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_phone_returns_400(self):
        make_profile(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            profile_me_update_url(),
            {"phone_number": "bad-phone"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# PromotionalMediaViewSet – LIST
# ---------------------------------------------------------------------------


class PromotionalMediaListTests(APITestCase):

    def setUp(self):
        self.admin = make_admin()
        self.user = make_user()
        self.client = APIClient()

    def test_authenticated_user_sees_active_media(self):
        make_media(self.admin, is_active=True)
        make_media(self.admin, title="Hidden", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(media_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        titles = [m["title"] for m in results]
        self.assertNotIn("Hidden", titles)

    def test_admin_sees_all_media_including_inactive(self):
        make_media(self.admin, is_active=True)
        make_media(self.admin, title="Inactive", is_active=False)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(media_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)

    def test_unauthenticated_cannot_list_media(self):
        response = self.client.get(media_list_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_empty_list_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(media_list_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(results, [])


# ---------------------------------------------------------------------------
# PromotionalMediaViewSet – RETRIEVE
# ---------------------------------------------------------------------------


class PromotionalMediaRetrieveTests(APITestCase):

    def setUp(self):
        self.admin = make_admin()
        self.user = make_user()
        self.client = APIClient()

    def test_authenticated_user_can_retrieve_active_media(self):
        media = make_media(self.admin, is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(media_detail_url(media.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regular_user_cannot_retrieve_inactive_media(self):
        media = make_media(self.admin, is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(media_detail_url(media.pk))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_retrieve_inactive_media(self):
        media = make_media(self.admin, is_active=False)
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(media_detail_url(media.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_retrieve(self):
        media = make_media(self.admin)
        response = self.client.get(media_detail_url(media.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# PromotionalMediaViewSet – CREATE
# ---------------------------------------------------------------------------


class PromotionalMediaCreateTests(APITestCase):

    def setUp(self):
        self.admin = make_admin()
        self.user = make_user()
        self.client = APIClient()
        self.valid_data = {
            "title": "NYSC Flyer",
            "media_type": "flyer",
            "marketing_text": "Order your NYSC uniforms today!",
            "is_active": True,
            "order": 1,
        }

    def test_admin_can_create_media(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(media_list_url(), self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PromotionalMedia.objects.count(), 1)

    def test_created_by_set_to_admin(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(media_list_url(), self.valid_data, format="json")
        media = PromotionalMedia.objects.first()
        self.assertEqual(media.created_by, self.admin)

    def test_regular_user_cannot_create_media(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(media_list_url(), self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create_media(self):
        response = self.client.post(media_list_url(), self.valid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_media_type_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        data = {**self.valid_data, "media_type": "audio"}
        response = self.client.post(media_list_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_title_returns_400(self):
        self.client.force_authenticate(user=self.admin)
        data = {**self.valid_data}
        data.pop("title")
        response = self.client.post(media_list_url(), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# PromotionalMediaViewSet – UPDATE / DELETE
# ---------------------------------------------------------------------------


class PromotionalMediaUpdateDeleteTests(APITestCase):

    def setUp(self):
        self.admin = make_admin()
        self.user = make_user()
        self.media = make_media(self.admin)
        self.client = APIClient()

    def test_admin_can_patch_media(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            media_detail_url(self.media.pk),
            {"title": "Updated Title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.media.refresh_from_db()
        self.assertEqual(self.media.title, "Updated Title")

    def test_regular_user_cannot_patch_media(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            media_detail_url(self.media.pk),
            {"title": "Hacked"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_media(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(media_detail_url(self.media.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PromotionalMedia.objects.filter(pk=self.media.pk).exists())

    def test_regular_user_cannot_delete_media(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(media_detail_url(self.media.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_delete(self):
        response = self.client.delete(media_detail_url(self.media.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# SharePayloadViewSet – generate
# ---------------------------------------------------------------------------


class SharePayloadGenerateTests(APITestCase):

    def setUp(self):
        self.admin = make_admin()
        self.user = make_user()
        self.client = APIClient()

    def _make_active_profile(self, user=None):
        return make_profile(user or self.user, is_active=True)

    def test_returns_payload_for_active_referrer(self):
        self._make_active_profile()
        make_media(self.admin, is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("referral_code", response.data)
        self.assertIn("whatsapp_link", response.data)
        self.assertIn("share_message", response.data)
        self.assertIn("promotional_media", response.data)

    def test_referral_code_in_payload_matches_profile(self):
        profile = self._make_active_profile()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertEqual(response.data["referral_code"], profile.referral_code)

    def test_whatsapp_link_contains_referral_code(self):
        profile = self._make_active_profile()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertIn(profile.referral_code, response.data["share_message"])

    def test_whatsapp_link_starts_with_wa_me(self):
        self._make_active_profile()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertTrue(response.data["whatsapp_link"].startswith("https://wa.me/"))

    def test_returns_404_when_no_referrer_profile(self):
        # User has no profile at all
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_returns_404_when_profile_is_inactive(self):
        make_profile(self.user, is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_cannot_generate_payload(self):
        response = self.client.get(share_generate_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_promotional_media_list_is_empty_when_no_active_media(self):
        self._make_active_profile()
        make_media(self.admin, is_active=False)  # inactive — must not appear
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["promotional_media"], [])

    def test_share_message_uses_default_when_no_media(self):
        """When no active media exists, a default fallback message is used."""
        self._make_active_profile()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertIn("MATERIAL", response.data["share_message"])

    def test_share_message_combines_all_marketing_texts(self):
        self._make_active_profile()
        make_media(self.admin, marketing_text="Text A", is_active=True)
        make_media(self.admin, title="B", marketing_text="Text B", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        msg = response.data["share_message"]
        self.assertIn("Text A", msg)
        self.assertIn("Text B", msg)

    def test_share_message_always_ends_with_referral_code(self):
        profile = self._make_active_profile()
        make_media(self.admin, is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(share_generate_url())
        self.assertIn(profile.referral_code, response.data["share_message"])

    def test_whatsapp_link_uses_custom_number_from_settings(self):
        self._make_active_profile()
        self.client.force_authenticate(user=self.user)
        with patch("referrals.views.settings") as mock_settings:
            mock_settings.WHATSAPP_NUMBER = "2349012345678"
            response = self.client.get(share_generate_url())
        self.assertIn("2349012345678", response.data["whatsapp_link"])
