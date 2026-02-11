"""
Comprehensive tests for referrals/signals.py

Covers:
- ensure_unique_referral_code (pre_save): code auto-generated when blank
- log_referrer_profile_creation (post_save): print on creation, not on update
- log_promotional_media_creation (post_save): print on creation, not on update
"""

from unittest.mock import patch, call
from django.test import TestCase
from django.contrib.auth import get_user_model

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


def _profile_data():
    return dict(
        full_name="Signal Tester",
        phone_number="+2348012345678",
        bank_name="Access Bank",
        account_number="0123456789",
    )


def _media_data():
    return dict(
        title="Signal Media",
        media_type="flyer",
        marketing_text="Check this out!",
    )


# ---------------------------------------------------------------------------
# ensure_unique_referral_code (pre_save)
# ---------------------------------------------------------------------------

class EnsureUniqueReferralCodeSignalTests(TestCase):

    def test_referral_code_generated_on_create(self):
        """A new profile should receive a referral code via the pre_save signal."""
        user = make_user()
        profile = ReferrerProfile(**{"user": user, **_profile_data()})
        profile.referral_code = ""       # simulate missing code
        profile.save()
        profile.refresh_from_db()
        self.assertTrue(profile.referral_code)
        self.assertEqual(len(profile.referral_code), 8)

    def test_existing_referral_code_not_overwritten(self):
        """If a code is already set, the signal must NOT overwrite it."""
        user = make_user()
        profile = ReferrerProfile.objects.create(user=user, **_profile_data())
        original_code = profile.referral_code

        # Update some unrelated field; code must stay the same
        profile.full_name = "Updated Name"
        profile.save()
        profile.refresh_from_db()
        self.assertEqual(profile.referral_code, original_code)

    def test_code_generated_uses_generate_referral_code_function(self):
        """When referral_code is blank, generate_referral_code is invoked."""
        user = make_user()
        with patch(
            "referrals.models.generate_referral_code",
            return_value="SIGTEST1",
        ) as mock_gen:
            profile = ReferrerProfile(user=user, **_profile_data())
            profile.referral_code = ""
            profile.save()
        mock_gen.assert_called_once()

    def test_collision_resolved_by_uniqueness_loop(self):
        """
        generate_referral_code() retries until unique.
        We verify this end-to-end: two profiles saved with a blank code
        both receive distinct, valid 8-char codes.
        (Patching generate_referral_code entirely would bypass its own
        while-loop, causing a real DB collision — so we exercise the real path.)
        """
        user1 = make_user(email="u1@test.com")
        user2 = make_user(email="u2@test.com")

        p1 = ReferrerProfile(user=user1, **_profile_data())
        p1.referral_code = ""
        p1.save()

        p2_data = {**_profile_data(), "full_name": "Second User"}
        p2 = ReferrerProfile(user=user2, **p2_data)
        p2.referral_code = ""
        p2.save()

        p1.refresh_from_db()
        p2.refresh_from_db()
        self.assertTrue(p1.referral_code)
        self.assertTrue(p2.referral_code)
        self.assertEqual(len(p1.referral_code), 8)
        self.assertEqual(len(p2.referral_code), 8)
        self.assertNotEqual(p1.referral_code, p2.referral_code)


# ---------------------------------------------------------------------------
# log_referrer_profile_creation (post_save)
# ---------------------------------------------------------------------------

class LogReferrerProfileCreationSignalTests(TestCase):

    def test_print_called_on_profile_creation(self):
        user = make_user()
        with patch("builtins.print") as mock_print:
            profile = ReferrerProfile.objects.create(user=user, **_profile_data())
        # Verify print was called at least once during creation
        mock_print.assert_called()
        # Verify the print message references the profile
        printed_args = " ".join(str(a) for call in mock_print.call_args_list for a in call[0])
        self.assertIn(profile.referral_code, printed_args)

    def test_print_not_called_on_profile_update(self):
        user = make_user()
        profile = ReferrerProfile.objects.create(user=user, **_profile_data())

        with patch("builtins.print") as mock_print:
            profile.full_name = "Updated"
            profile.save()

        # The signal guard is `if created:`, so print should NOT fire on update
        # Collect any creation-related prints
        creation_prints = [
            c for c in mock_print.call_args_list
            if "referrer profile created" in str(c).lower()
        ]
        self.assertEqual(len(creation_prints), 0)

    def test_creation_signal_includes_full_name(self):
        user = make_user()
        with patch("builtins.print") as mock_print:
            ReferrerProfile.objects.create(user=user, **_profile_data())
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn("Signal Tester", all_output)

    def test_signal_fires_once_per_creation(self):
        """Signal fires exactly once — verified via print side-effects.
        (Django holds a weak ref to the original function at connect() time,
        so patching the module-level name cannot intercept dispatch. The
        observable consequence — one 'profile created' print — is checked.)
        """
        user = make_user()
        with patch("builtins.print") as mock_print:
            ReferrerProfile.objects.create(user=user, **_profile_data())
        creation_prints = [
            c for c in mock_print.call_args_list
            if "New referrer profile created" in str(c)
        ]
        self.assertEqual(len(creation_prints), 1)


# ---------------------------------------------------------------------------
# log_promotional_media_creation (post_save)
# ---------------------------------------------------------------------------

class LogPromotionalMediaCreationSignalTests(TestCase):

    def setUp(self):
        self.admin = make_user(email="admin@example.com", is_staff=True)

    def test_print_called_on_media_creation(self):
        with patch("builtins.print") as mock_print:
            media = PromotionalMedia.objects.create(
                created_by=self.admin, **_media_data()
            )
        mock_print.assert_called()
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        self.assertIn(media.title, all_output)

    def test_print_not_called_on_media_update(self):
        media = PromotionalMedia.objects.create(
            created_by=self.admin, **_media_data()
        )
        with patch("builtins.print") as mock_print:
            media.title = "Updated Title"
            media.save()

        creation_prints = [
            c for c in mock_print.call_args_list
            if "promotional media created" in str(c).lower()
        ]
        self.assertEqual(len(creation_prints), 0)

    def test_signal_fires_once_per_creation(self):
        """Signal fires exactly once — verified via print side-effects."""
        with patch("builtins.print") as mock_print:
            PromotionalMedia.objects.create(
                created_by=self.admin, **_media_data()
            )
        creation_prints = [
            c for c in mock_print.call_args_list
            if "New promotional media created" in str(c)
        ]
        self.assertEqual(len(creation_prints), 1)

    def test_media_type_included_in_print(self):
        with patch("builtins.print") as mock_print:
            PromotionalMedia.objects.create(
                created_by=self.admin, **_media_data()
            )
        all_output = " ".join(str(c) for c in mock_print.call_args_list)
        # The signal print uses media_type
        self.assertIn("flyer", all_output.lower())


# ---------------------------------------------------------------------------
# Signal registration (app ready)
# ---------------------------------------------------------------------------

class SignalRegistrationTests(TestCase):

    def test_pre_save_signal_connected(self):
        """ensure_unique_referral_code must be connected to pre_save of ReferrerProfile."""
        from django.db.models.signals import pre_save
        from referrals.signals import ensure_unique_referral_code

        receivers = [
            r[1]() for r in pre_save.receivers
            if r[1]() is not None
        ]
        # Check that our function is among the connected receivers
        # (Django stores weak refs — resolve and compare)
        pre_save_funcs = [getattr(r, "__name__", "") for r in receivers]
        self.assertIn("ensure_unique_referral_code", pre_save_funcs)

    def test_post_save_signals_connected(self):
        """Both post_save signals must be registered."""
        from django.db.models.signals import post_save
        from referrals.signals import (
            log_referrer_profile_creation,
            log_promotional_media_creation,
        )

        receivers = [r[1]() for r in post_save.receivers if r[1]() is not None]
        post_save_funcs = [getattr(r, "__name__", "") for r in receivers]
        self.assertIn("log_referrer_profile_creation", post_save_funcs)
        self.assertIn("log_promotional_media_creation", post_save_funcs)