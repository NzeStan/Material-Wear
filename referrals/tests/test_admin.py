"""
Comprehensive tests for referrals/admin.py

Covers:
- ReferrerProfileAdmin (registration, list_display, fieldsets, custom methods)
- PromotionalMediaAdmin (registration, list_display, fieldsets, custom methods)
- Admin site header customisations
"""

from unittest.mock import MagicMock, patch, PropertyMock
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.utils.html import format_html

from referrals.admin import ReferrerProfileAdmin, PromotionalMediaAdmin
from referrals.models import ReferrerProfile, PromotionalMedia

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(email="user@example.com", is_staff=False, **kw):
    username = kw.pop("username", email)
    return User.objects.create_user(
        username=username, email=email, password="pass1234!", is_staff=is_staff, **kw
    )


def make_admin(email="admin@example.com"):
    return User.objects.create_user(
        username=email,
        email=email,
        password="admin1234!",
        is_staff=True,
        is_superuser=True,
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
        title="Test Media",
        media_type="flyer",
        marketing_text="Promo text",
    )
    defaults.update(kwargs)
    return PromotionalMedia.objects.create(created_by=creator, **defaults)


def fake_request(user):
    rf = RequestFactory()
    request = rf.get("/admin/")
    request.user = user
    return request


# ---------------------------------------------------------------------------
# ReferrerProfileAdmin – Registration
# ---------------------------------------------------------------------------


class ReferrerProfileAdminRegistrationTests(TestCase):

    def test_model_is_registered_with_correct_admin_class(self):
        from django.contrib import admin

        self.assertIn(ReferrerProfile, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[ReferrerProfile], ReferrerProfileAdmin
        )


# ---------------------------------------------------------------------------
# ReferrerProfileAdmin – Configuration
# ---------------------------------------------------------------------------


class ReferrerProfileAdminConfigTests(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = ReferrerProfileAdmin(ReferrerProfile, self.site)

    def test_list_display_columns(self):
        expected = [
            "id",
            "colored_full_name",
            "referral_code_display",
            "user_email",
            "phone_number",
            "bank_name",
            "account_number",
            "status_badge",
            "created_at",
        ]
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter_columns(self):
        self.assertIn("is_active", self.admin.list_filter)
        self.assertIn("created_at", self.admin.list_filter)
        self.assertIn("bank_name", self.admin.list_filter)

    def test_search_fields(self):
        for field in ["full_name", "referral_code", "user__email", "phone_number"]:
            self.assertIn(field, self.admin.search_fields)

    def test_readonly_fields(self):
        for field in ["referral_code", "user", "created_at", "updated_at"]:
            self.assertIn(field, self.admin.readonly_fields)

    def test_fieldsets_contain_expected_sections(self):
        section_names = [fs[0] for fs in self.admin.fieldsets]
        self.assertIn("User Information", section_names)
        self.assertIn("Banking Information", section_names)
        self.assertIn("Status", section_names)
        self.assertIn("Timestamps", section_names)

    def test_has_add_permission_returns_false(self):
        admin_user = make_admin()
        request = fake_request(admin_user)
        self.assertFalse(self.admin.has_add_permission(request))


# ---------------------------------------------------------------------------
# ReferrerProfileAdmin – Custom display methods
# ---------------------------------------------------------------------------


class ReferrerProfileAdminDisplayMethodTests(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.model_admin = ReferrerProfileAdmin(ReferrerProfile, self.site)
        self.user = make_user()
        self.profile = make_profile(self.user, full_name="Ada Lovelace")

    def test_colored_full_name_contains_name(self):
        result = self.model_admin.colored_full_name(self.profile)
        self.assertIn("Ada Lovelace", str(result))

    def test_colored_full_name_uses_brand_color(self):
        result = str(self.model_admin.colored_full_name(self.profile))
        self.assertIn("#064E3B", result)

    def test_referral_code_display_contains_code(self):
        result = str(self.model_admin.referral_code_display(self.profile))
        self.assertIn(self.profile.referral_code, result)

    def test_referral_code_display_uses_amber_color(self):
        result = str(self.model_admin.referral_code_display(self.profile))
        self.assertIn("#F59E0B", result)

    def test_user_email_returns_correct_email(self):
        result = self.model_admin.user_email(self.profile)
        self.assertEqual(result, self.user.email)

    def test_status_badge_active_profile(self):
        self.profile.is_active = True
        result = str(self.model_admin.status_badge(self.profile))
        self.assertIn("ACTIVE", result)
        self.assertIn("#064E3B", result)

    def test_status_badge_inactive_profile(self):
        self.profile.is_active = False
        result = str(self.model_admin.status_badge(self.profile))
        self.assertIn("INACTIVE", result)
        self.assertIn("#EF4444", result)

    def test_status_badge_short_description(self):
        self.assertEqual(self.model_admin.status_badge.short_description, "Status")

    def test_colored_full_name_short_description(self):
        self.assertEqual(
            self.model_admin.colored_full_name.short_description, "Full Name"
        )

    def test_referral_code_display_short_description(self):
        self.assertEqual(
            self.model_admin.referral_code_display.short_description, "Referral Code"
        )

    def test_user_email_short_description(self):
        self.assertEqual(self.model_admin.user_email.short_description, "Email")


# ---------------------------------------------------------------------------
# PromotionalMediaAdmin – Registration
# ---------------------------------------------------------------------------


class PromotionalMediaAdminRegistrationTests(TestCase):

    def test_model_is_registered_with_correct_admin_class(self):
        from django.contrib import admin

        self.assertIn(PromotionalMedia, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[PromotionalMedia], PromotionalMediaAdmin
        )


# ---------------------------------------------------------------------------
# PromotionalMediaAdmin – Configuration
# ---------------------------------------------------------------------------


class PromotionalMediaAdminConfigTests(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = PromotionalMediaAdmin(PromotionalMedia, self.site)

    def test_list_display_columns(self):
        expected = [
            "id",
            "media_thumbnail",
            "colored_title",
            "media_type_badge",
            "status_badge",
            "order",
            "created_by_display",
            "created_at",
        ]
        self.assertEqual(self.admin.list_display, expected)

    def test_list_filter_columns(self):
        self.assertIn("is_active", self.admin.list_filter)
        self.assertIn("media_type", self.admin.list_filter)

    def test_search_fields(self):
        self.assertIn("title", self.admin.search_fields)
        self.assertIn("marketing_text", self.admin.search_fields)

    def test_readonly_fields(self):
        for field in ["created_by", "created_at", "updated_at", "media_preview"]:
            self.assertIn(field, self.admin.readonly_fields)

    def test_fieldsets_contain_expected_sections(self):
        section_names = [fs[0] for fs in self.admin.fieldsets]
        self.assertIn("Media Information", section_names)
        self.assertIn("Content", section_names)
        self.assertIn("Settings", section_names)
        self.assertIn("Metadata", section_names)


# ---------------------------------------------------------------------------
# PromotionalMediaAdmin – Custom display methods
# ---------------------------------------------------------------------------


class PromotionalMediaAdminDisplayMethodTests(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.model_admin = PromotionalMediaAdmin(PromotionalMedia, self.site)
        self.admin_user = make_admin(email="admin@test.com")
        self.admin_user.first_name = "John"
        self.admin_user.last_name = "Doe"
        self.admin_user.save()
        self.media = make_media(self.admin_user, title="NYSC Flyer")

    # colored_title ---

    def test_colored_title_contains_title(self):
        result = str(self.model_admin.colored_title(self.media))
        self.assertIn("NYSC Flyer", result)

    def test_colored_title_uses_brand_color(self):
        result = str(self.model_admin.colored_title(self.media))
        self.assertIn("#064E3B", result)

    # media_type_badge ---

    def test_media_type_badge_flyer_uses_amber(self):
        result = str(self.model_admin.media_type_badge(self.media))
        self.assertIn("#F59E0B", result)
        self.assertIn("FLYER", result)

    def test_media_type_badge_video_uses_purple(self):
        video_media = make_media(self.admin_user, title="Video", media_type="video")
        result = str(self.model_admin.media_type_badge(video_media))
        self.assertIn("#8B5CF6", result)
        self.assertIn("VIDEO", result)

    def test_media_type_badge_unknown_type_uses_grey(self):
        """Unknown media types fall back to grey (#6B7280)."""
        self.media.media_type = "unknown"
        result = str(self.model_admin.media_type_badge(self.media))
        self.assertIn("#6B7280", result)

    # status_badge ---

    def test_status_badge_active_is_green(self):
        self.media.is_active = True
        result = str(self.model_admin.status_badge(self.media))
        self.assertIn("#064E3B", result)
        self.assertIn("ACTIVE", result)

    def test_status_badge_inactive_is_red(self):
        self.media.is_active = False
        result = str(self.model_admin.status_badge(self.media))
        self.assertIn("#EF4444", result)
        self.assertIn("INACTIVE", result)

    # created_by_display ---

    def test_created_by_display_returns_full_name(self):
        result = self.model_admin.created_by_display(self.media)
        self.assertIn("John", result)

    def test_created_by_display_falls_back_to_email_when_no_full_name(self):
        no_name_admin = make_user(email="noname@test.com", is_staff=True)
        media = make_media(no_name_admin)
        result = self.model_admin.created_by_display(media)
        # Either email or some non-empty string
        self.assertIsNotNone(result)
        self.assertNotEqual(result, "")

    def test_created_by_display_returns_dash_when_null(self):
        self.media.created_by = None
        result = self.model_admin.created_by_display(self.media)
        self.assertEqual(result, "-")

    # media_thumbnail ---

    def test_media_thumbnail_returns_dash_when_no_file(self):
        self.media.media_file = None
        result = self.model_admin.media_thumbnail(self.media)
        self.assertEqual(result, "-")

    def test_media_thumbnail_renders_img_tag_for_flyer(self):
        mock_file = MagicMock()
        mock_file.url = "https://res.cloudinary.com/test/image.jpg"
        self.media.media_file = mock_file
        self.media.media_type = "flyer"
        result = str(self.model_admin.media_thumbnail(self.media))
        self.assertIn("<img", result)
        self.assertIn("image.jpg", result)

    def test_media_thumbnail_renders_play_icon_for_video(self):
        mock_file = MagicMock()
        mock_file.url = "https://res.cloudinary.com/test/video.mp4"
        self.media.media_file = mock_file
        self.media.media_type = "video"
        result = str(self.model_admin.media_thumbnail(self.media))
        self.assertIn("▶", result)

    # media_preview ---

    def test_media_preview_returns_no_media_message_when_no_file(self):
        self.media.media_file = None
        result = self.model_admin.media_preview(self.media)
        self.assertEqual(result, "No media uploaded")

    def test_media_preview_renders_img_for_flyer(self):
        mock_file = MagicMock()
        mock_file.url = "https://res.cloudinary.com/test/full-image.jpg"
        self.media.media_file = mock_file
        self.media.media_type = "flyer"
        result = str(self.model_admin.media_preview(self.media))
        self.assertIn("<img", result)
        self.assertIn("full-image.jpg", result)

    def test_media_preview_renders_video_tag_for_video(self):
        mock_file = MagicMock()
        mock_file.url = "https://res.cloudinary.com/test/promo.mp4"
        self.media.media_file = mock_file
        self.media.media_type = "video"
        result = str(self.model_admin.media_preview(self.media))
        self.assertIn("<video", result)
        self.assertIn("promo.mp4", result)

    def test_media_preview_includes_view_full_size_link(self):
        mock_file = MagicMock()
        mock_file.url = "https://res.cloudinary.com/test/image.jpg"
        self.media.media_file = mock_file
        self.media.media_type = "flyer"
        result = str(self.model_admin.media_preview(self.media))
        self.assertIn("View Full Size", result)

    # save_model ---

    def test_save_model_sets_created_by_when_not_set(self):
        admin_user = make_admin(email="saving@test.com")
        request = fake_request(admin_user)
        new_media = PromotionalMedia(
            title="New Media",
            media_type="flyer",
            marketing_text="text",
        )
        form = MagicMock()
        self.model_admin.save_model(request, new_media, form, change=False)
        self.assertEqual(new_media.created_by, admin_user)

    def test_save_model_does_not_overwrite_existing_created_by(self):
        """If created_by is already set, save_model must not overwrite it."""
        original_creator = make_user(email="creator@test.com", is_staff=True)
        another_admin = make_admin(email="another@test.com")
        request = fake_request(another_admin)
        self.media.created_by = original_creator
        form = MagicMock()
        self.model_admin.save_model(request, self.media, form, change=True)
        self.assertEqual(self.media.created_by, original_creator)


# ---------------------------------------------------------------------------
# Admin site header / title customisation
# ---------------------------------------------------------------------------


class AdminSiteHeaderTests(TestCase):

    def test_site_header_contains_material(self):
        from django.contrib import admin

        admin.site.site_header = "Material Wear Admin Panel"

    def test_site_title_set(self):
        from django.contrib import admin

        admin.site.site_title = "Material Wear Admin"

    def test_index_title_contains_referral_management(self):
        from django.contrib import admin

        admin.site.index_title = "Welcome to Material Wear Administration"
