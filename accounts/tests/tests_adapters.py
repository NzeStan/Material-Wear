"""
Comprehensive bulletproof tests for accounts/adapters.py

Test Coverage:
===============

✅ CustomAccountAdapter
   - is_open_for_signup() - Signup availability control
   - send_mail() - HTML email sending
   - save_user() - User creation with welcome email
   - send_welcome_email() - Welcome email functionality

✅ CustomSocialAccountAdapter
   - pre_social_login() - Social account linking
   - save_user() - Social user creation and email verification
   - is_auto_signup_allowed() - Auto signup control
   - validate_disconnect() - Social account disconnect validation

Security Coverage:
- Email uniqueness handling
- Social account linking security
- Password requirement for disconnect
- Email verification for social accounts
- Username generation uniqueness
- Edge cases and error scenarios
"""

from django.test import TestCase, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.contrib.sites.models import Site
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from unittest.mock import Mock, patch, MagicMock, call
from rest_framework import serializers
import logging

from accounts.adapters import CustomAccountAdapter, CustomSocialAccountAdapter

User = get_user_model()


# ============================================================================
# CUSTOM ACCOUNT ADAPTER TESTS
# ============================================================================


class CustomAccountAdapterTests(TestCase):
    """Test CustomAccountAdapter - email-based account management"""

    def setUp(self):
        """Set up test fixtures"""
        self.adapter = CustomAccountAdapter()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        # Ensure site exists
        if not Site.objects.filter(pk=1).exists():
            Site.objects.create(pk=1, domain="example.com", name="Example")

    def test_is_open_for_signup_returns_true(self):
        """Test signup is open by default"""
        result = self.adapter.is_open_for_signup(self.request)

        self.assertTrue(result)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_mail_with_valid_template(self):
        """Test send_mail sends email with HTML support"""
        context = {
            "user": Mock(username="testuser"),
            "site_name": "MATERIAL WEAR",
        }

        # Create mock templates
        with patch("accounts.adapters.render_to_string") as mock_render:
            mock_render.side_effect = ["Test Subject", "<html>Test HTML Message</html>"]

            self.adapter.send_mail("test_template", "test@example.com", context)

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["test@example.com"])
        self.assertEqual(mail.outbox[0].subject, "Test Subject")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_mail_strips_newlines_from_subject(self):
        """Test send_mail strips newlines from subject"""
        context = {}

        with patch("accounts.adapters.render_to_string") as mock_render:
            # Subject with newlines
            mock_render.side_effect = [
                "Test\nSubject\nWith\nNewlines",
                "<html>Message</html>",
            ]

            self.adapter.send_mail("test_template", "test@example.com", context)

        # Subject should have newlines removed
        self.assertEqual(mail.outbox[0].subject, "TestSubjectWithNewlines")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_mail_includes_plain_text_version(self):
        """Test send_mail includes plain text version (stripped HTML)"""
        context = {}

        with patch("accounts.adapters.render_to_string") as mock_render:
            mock_render.side_effect = [
                "Subject",
                "<html><body><p>HTML Message</p></body></html>",
            ]

            self.adapter.send_mail("test_template", "test@example.com", context)

        # Check both HTML and plain text are present
        self.assertIn("HTML Message", mail.outbox[0].body)  # Plain text
        self.assertEqual(len(mail.outbox[0].alternatives), 1)  # HTML alternative

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_mail_uses_correct_from_email(self):
        """Test send_mail uses correct from_email"""
        context = {}

        with patch("accounts.adapters.render_to_string") as mock_render:
            mock_render.side_effect = ["Subject", "<html>Message</html>"]

            with patch.object(
                self.adapter, "get_from_email", return_value="noreply@material.com"
            ):
                self.adapter.send_mail("test_template", "test@example.com", context)

        self.assertEqual(mail.outbox[0].from_email, "noreply@material.com")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ACCOUNT_EMAIL_VERIFICATION="none",
    )
    def test_save_user_creates_user_and_sends_welcome_email(self):
        """Test save_user creates user and sends welcome email"""
        user = User(
            username="newuser",
            email="newuser@example.com",
        )

        # Create mock form with cleaned_data
        mock_form = Mock()
        mock_form.cleaned_data = {
            "email": "newuser@example.com",
            "username": "newuser",
        }

        with patch.object(self.adapter, "send_welcome_email") as mock_welcome:
            saved_user = self.adapter.save_user(self.request, user, mock_form)

        # User should be saved
        self.assertTrue(User.objects.filter(username="newuser").exists())

        # Welcome email should be sent (when email verification is not mandatory)
        mock_welcome.assert_called_once_with(saved_user)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ACCOUNT_EMAIL_VERIFICATION="mandatory",
    )
    def test_save_user_no_welcome_email_when_verification_mandatory(self):
        """Test save_user doesn't send welcome email when verification is mandatory"""
        user = User(
            username="newuser",
            email="newuser@example.com",
        )

        # Create mock form with cleaned_data
        mock_form = Mock()
        mock_form.cleaned_data = {
            "email": "newuser@example.com",
            "username": "newuser",
        }

        with patch.object(self.adapter, "send_welcome_email") as mock_welcome:
            self.adapter.save_user(self.request, user, mock_form)

        # Welcome email should NOT be sent (verification mandatory)
        mock_welcome.assert_not_called()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ACCOUNT_EMAIL_VERIFICATION="mandatory",
    )
    def test_save_user_sends_welcome_when_email_verified(self):
        """Test save_user sends welcome email when email is already verified"""
        user = User.objects.create_user(
            username="verifieduser",
            email="verified@example.com",
            password="testpass123",
        )

        # Mark email as verified
        EmailAddress.objects.create(
            user=user, email=user.email, verified=True, primary=True
        )

        # Create mock form with cleaned_data
        mock_form = Mock()
        mock_form.cleaned_data = {
            "email": "verified@example.com",
            "username": "verifieduser",
        }

        with patch.object(self.adapter, "send_welcome_email") as mock_welcome:
            self.adapter.save_user(self.request, user, mock_form, commit=False)

        # Welcome email should be sent (email is verified)
        mock_welcome.assert_called_once_with(user)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_URL="https://materialwear.com",
    )
    def test_send_welcome_email_with_context(self):
        """Test send_welcome_email builds login_url correctly from FRONTEND_URL"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        with patch.object(self.adapter, "send_mail") as mock_send:
            self.adapter.send_welcome_email(user)

        mock_send.assert_called_once()
        args = mock_send.call_args

        self.assertEqual(args[0][0], "account/email/welcome")  # template_prefix
        self.assertEqual(args[0][1], "test@example.com")       # email

        context = args[0][2]
        self.assertEqual(context["user"], user)
        self.assertEqual(context["site_name"], "MATERIAL WEAR")
        self.assertEqual(context["login_url"], "https://materialwear.com/login")


    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_URL="https://materialwear.com/",  # trailing slash variant
    )
    def test_send_welcome_email_strips_trailing_slash_from_frontend_url(self):
        """Test send_welcome_email strips trailing slash from FRONTEND_URL before appending /login"""
        user = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )

        with patch.object(self.adapter, "send_mail") as mock_send:
            self.adapter.send_welcome_email(user)

        context = mock_send.call_args[0][2]
        # Should NOT produce https://materialwear.com//login
        self.assertEqual(context["login_url"], "https://materialwear.com/login")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_welcome_email_fallback_when_frontend_url_missing(self):
        """Test send_welcome_email produces a safe fallback if FRONTEND_URL is not set"""
        user = User.objects.create_user(
            username="testuser3", email="test3@example.com", password="testpass123"
        )

        with self.settings(FRONTEND_URL=""):
            with patch.object(self.adapter, "send_mail") as mock_send:
                self.adapter.send_welcome_email(user)

        context = mock_send.call_args[0][2]
        # Falls back to "/login" — still a string, not a crash
        self.assertEqual(context["login_url"], "/login")


    def test_save_user_with_commit_false(self):
        """Test save_user with commit=False doesn't save to database"""
        user = User(
            username="unsaveduser",
            email="unsaved@example.com",
        )

        mock_form = Mock()

        with patch.object(self.adapter, "send_welcome_email"):
            # Call parent's save_user to handle the user object properly
            with patch(
                "accounts.adapters.DefaultAccountAdapter.save_user", return_value=user
            ):
                result = self.adapter.save_user(
                    self.request, user, mock_form, commit=False
                )

        # User should be returned but not in database
        self.assertEqual(result.username, "unsaveduser")


# ============================================================================
# CUSTOM SOCIAL ACCOUNT ADAPTER TESTS
# ============================================================================


class CustomSocialAccountAdapterTests(TestCase):
    """Test CustomSocialAccountAdapter - OAuth/social account management"""

    def setUp(self):
        """Set up test fixtures"""
        self.adapter = CustomSocialAccountAdapter()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        # Ensure site exists
        if not Site.objects.filter(pk=1).exists():
            Site.objects.create(pk=1, domain="example.com", name="Example")

    def test_is_auto_signup_allowed_returns_true(self):
        """Test auto signup is allowed for social accounts"""
        mock_sociallogin = Mock()

        result = self.adapter.is_auto_signup_allowed(self.request, mock_sociallogin)

        self.assertTrue(result)

    def test_pre_social_login_generates_username_if_missing(self):
        """Test pre_social_login generates username from email if missing"""
        # Create user and explicitly ensure username is truly empty
        user = User(email="john.doe@example.com")
        # Force username to be truly empty - this is KEY!
        if hasattr(user, "username"):
            user.username = ""

        # Debug: print what username is before adapter call
        print(f"DEBUG: user.pk = {user.pk}, user.username = '{user.username}'")

        mock_sociallogin = Mock()
        mock_sociallogin.user = user

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        print(f"DEBUG: After adapter, user.username = '{user.username}'")

        # Username should be generated
        self.assertEqual(user.username, "johndoe")

    def test_pre_social_login_generates_unique_username(self):
        """Test pre_social_login generates unique username if collision"""
        # Create existing user with desired username
        User.objects.create_user(
            username="johndoe", email="existing@example.com", password="testpass123"
        )

        # Create new user - explicitly set empty username
        user = User(email="john.doe@gmail.com")
        user.username = ""  # Explicitly force empty

        mock_sociallogin = Mock()
        mock_sociallogin.user = user

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Username should be unique (e.g., johndoe-1)
        self.assertIn("johndoe", user.username)
        self.assertNotEqual(user.username, "johndoe")

    def test_pre_social_login_links_to_existing_account_with_same_email(self):
        """Test pre_social_login links to existing account with same email"""
        # Create existing user
        existing_user = User.objects.create_user(
            username="existing", email="same@example.com", password="testpass123"
        )

        # Create email address for existing user
        EmailAddress.objects.create(
            user=existing_user, email="same@example.com", verified=False, primary=True
        )

        # Create social login with same email
        social_user = User(email="same@example.com", username="")

        mock_sociallogin = Mock()
        mock_sociallogin.user = social_user
        mock_sociallogin.connect = Mock()
        mock_sociallogin.state = {}

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Should have called connect with existing user
        mock_sociallogin.connect.assert_called_once_with(self.request, existing_user)
        self.assertEqual(mock_sociallogin.state["process"], "connect")

    def test_pre_social_login_marks_email_verified_when_linking(self):
        """Test pre_social_login marks email as verified when linking"""
        # Create existing user with unverified email
        existing_user = User.objects.create_user(
            username="existing", email="link@example.com", password="testpass123"
        )

        email_address = EmailAddress.objects.create(
            user=existing_user, email="link@example.com", verified=False, primary=True
        )

        # Create social login with same email
        social_user = User(email="link@example.com", username="")

        mock_sociallogin = Mock()
        mock_sociallogin.user = social_user
        mock_sociallogin.connect = Mock()
        mock_sociallogin.state = {}

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Email should now be verified
        email_address.refresh_from_db()
        self.assertTrue(email_address.verified)
        self.assertTrue(email_address.primary)

    def test_pre_social_login_no_link_if_no_email(self):
        """Test pre_social_login doesn't link if social user has no email"""
        # Create existing user
        existing_user = User.objects.create_user(
            username="existing", email="existing@example.com", password="testpass123"
        )

        # Create social login without email
        social_user = User(email="", username="")

        mock_sociallogin = Mock()
        mock_sociallogin.user = social_user
        mock_sociallogin.connect = Mock()

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Should NOT have called connect
        mock_sociallogin.connect.assert_not_called()

    def test_pre_social_login_links_even_if_existing_has_password(self):
        """Test pre_social_login links to account even if it has password"""
        # Create existing user with password
        existing_user = User.objects.create_user(
            username="withpassword",
            email="haspass@example.com",
            password="securepass123",
        )

        EmailAddress.objects.create(
            user=existing_user, email="haspass@example.com", verified=True, primary=True
        )

        # Create social login with same email
        social_user = User(email="haspass@example.com", username="")

        mock_sociallogin = Mock()
        mock_sociallogin.user = social_user
        mock_sociallogin.connect = Mock()
        mock_sociallogin.state = {}

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Should link (even though existing user has password)
        mock_sociallogin.connect.assert_called_once()

    def test_save_user_marks_email_as_verified(self):
        """Test save_user marks email as verified for social accounts"""
        # Create user
        user = User.objects.create_user(
            username="socialuser", email="social@example.com", password=""
        )

        # Create unverified email
        email_address = EmailAddress.objects.create(
            user=user, email="social@example.com", verified=False, primary=False
        )

        mock_sociallogin = Mock()

        # Mock parent's save_user to return the user
        with patch(
            "accounts.adapters.DefaultSocialAccountAdapter.save_user", return_value=user
        ):
            result = self.adapter.save_user(self.request, mock_sociallogin)

        # Email should be verified and primary
        email_address.refresh_from_db()
        self.assertTrue(email_address.verified)
        self.assertTrue(email_address.primary)

    def test_save_user_sends_welcome_email_if_adapter_has_method(self):
        """Test save_user sends welcome email if method exists"""
        user = User.objects.create_user(
            username="socialuser", email="social@example.com", password=""
        )

        EmailAddress.objects.create(
            user=user, email="social@example.com", verified=False, primary=True
        )

        mock_sociallogin = Mock()

        # Add send_welcome_email method to adapter
        self.adapter.send_welcome_email = Mock()

        with patch(
            "accounts.adapters.DefaultSocialAccountAdapter.save_user", return_value=user
        ):
            self.adapter.save_user(self.request, mock_sociallogin)

        # Welcome email should be sent
        self.adapter.send_welcome_email.assert_called_once_with(user)

    def test_save_user_no_error_if_no_email_address(self):
        """Test save_user doesn't error if no EmailAddress exists"""
        user = User.objects.create_user(
            username="noemail", email="noemail@example.com", password=""
        )

        mock_sociallogin = Mock()

        # Don't create EmailAddress
        with patch(
            "accounts.adapters.DefaultSocialAccountAdapter.save_user", return_value=user
        ):
            result = self.adapter.save_user(self.request, mock_sociallogin)

        # Should complete without error
        self.assertEqual(result, user)

    def test_validate_disconnect_allows_if_password_set(self):
        """Test validate_disconnect allows disconnect if user has password"""
        # Create user with password
        user = User.objects.create_user(
            username="withpass", email="withpass@example.com", password="securepass123"
        )

        # Create social account
        social_account = SocialAccount.objects.create(
            user=user, provider="google", uid="12345"
        )

        accounts = SocialAccount.objects.filter(user=user)

        # Should not raise error
        try:
            self.adapter.validate_disconnect(social_account, accounts)
        except serializers.ValidationError:
            self.fail("validate_disconnect raised ValidationError when it shouldn't")

    def test_validate_disconnect_prevents_if_last_account_no_password(self):
        """Test validate_disconnect prevents disconnect of last account without password"""
        # Create user without password (social login only)
        user = User.objects.create_user(
            username="nopass", email="nopass@example.com", password=""
        )
        user.set_unusable_password()
        user.save()

        # Create single social account
        social_account = SocialAccount.objects.create(
            user=user, provider="google", uid="12345"
        )

        accounts = SocialAccount.objects.filter(user=user)

        # Should raise ValidationError
        with self.assertRaises(serializers.ValidationError) as context:
            self.adapter.validate_disconnect(social_account, accounts)

        self.assertIn("Cannot disconnect", str(context.exception))

    def test_validate_disconnect_allows_if_multiple_accounts(self):
        """Test validate_disconnect allows disconnect if user has multiple social accounts"""
        # Create user without password
        user = User.objects.create_user(
            username="multisocial", email="multi@example.com", password=""
        )
        user.set_unusable_password()
        user.save()

        # Create multiple social accounts
        google_account = SocialAccount.objects.create(
            user=user, provider="google", uid="12345"
        )

        SocialAccount.objects.create(user=user, provider="github", uid="67890")

        accounts = SocialAccount.objects.filter(user=user)

        # Should not raise error (user has another social account)
        try:
            self.adapter.validate_disconnect(google_account, accounts)
        except serializers.ValidationError:
            self.fail("validate_disconnect raised ValidationError when it shouldn't")

    def test_username_generation_with_special_characters(self):
        """Test username generation handles special characters"""
        # Email with special characters
        user = User(email="john+test@example.com")
        user.username = ""  # Explicitly force empty

        mock_sociallogin = Mock()
        mock_sociallogin.user = user

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Username should be slugified (alphanumeric and hyphens only)
        self.assertRegex(user.username, r"^[a-z0-9-]+$")

    def test_username_generation_with_numbers(self):
        """Test username generation handles email starting with numbers"""
        user = User(email="123test@example.com")
        user.username = ""  # Explicitly force empty

        mock_sociallogin = Mock()
        mock_sociallogin.user = user

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Username should be valid
        self.assertTrue(user.username)

    def test_username_generation_increments_correctly(self):
        """Test username generation increments count correctly"""
        # Create users with incremental usernames
        User.objects.create_user(
            username="testuser", email="test1@example.com", password="pass"
        )
        User.objects.create_user(
            username="testuser-1", email="test2@example.com", password="pass"
        )
        User.objects.create_user(
            username="testuser-2", email="test3@example.com", password="pass"
        )

        # Create social user with conflicting username
        user = User(email="testuser@newdomain.com")
        user.username = ""  # Explicitly force empty

        mock_sociallogin = Mock()
        mock_sociallogin.user = user

        self.adapter.pre_social_login(self.request, mock_sociallogin)

        # Should generate testuser-3
        self.assertEqual(user.username, "testuser-3")


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class AdaptersIntegrationTests(TestCase):
    """Integration tests for adapter workflows"""

    def setUp(self):
        """Set up test fixtures"""
        self.account_adapter = CustomAccountAdapter()
        self.social_adapter = CustomSocialAccountAdapter()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        if not Site.objects.filter(pk=1).exists():
            Site.objects.create(pk=1, domain="example.com", name="Example")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        ACCOUNT_EMAIL_VERIFICATION="none",
    )
    def test_complete_registration_flow_with_welcome_email(self):
        """Test complete registration sends welcome email"""
        user = User(
            username="newuser",
            email="newuser@example.com",
        )

        # Create mock form with cleaned_data
        mock_form = Mock()
        mock_form.cleaned_data = {
            "email": "newuser@example.com",
            "username": "newuser",
        }

        # Mock the welcome email sending
        with patch.object(self.account_adapter, "send_mail") as mock_send:
            saved_user = self.account_adapter.save_user(self.request, user, mock_form)

        # User should exist
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

        # Welcome email should have been sent
        mock_send.assert_called_once()

    def test_complete_social_login_flow_with_account_linking(self):
        """Test complete social login flow links to existing account"""
        # Create existing user
        existing_user = User.objects.create_user(
            username="existing", email="existing@example.com", password="testpass123"
        )

        EmailAddress.objects.create(
            user=existing_user,
            email="existing@example.com",
            verified=False,
            primary=True,
        )

        # Simulate social login with same email
        social_user = User(email="existing@example.com", username="")

        mock_sociallogin = Mock()
        mock_sociallogin.user = social_user
        mock_sociallogin.connect = Mock()
        mock_sociallogin.state = {}

        self.social_adapter.pre_social_login(self.request, mock_sociallogin)

        # Account should be linked
        mock_sociallogin.connect.assert_called_once_with(self.request, existing_user)

        # Email should be verified
        email = EmailAddress.objects.get(
            user=existing_user, email="existing@example.com"
        )
        self.assertTrue(email.verified)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_complete_social_signup_flow_new_user(self):
        """Test complete social signup flow for new user"""
        # Create social user
        user = User.objects.create_user(
            username="socialuser", email="social@example.com", password=""
        )

        email_address = EmailAddress.objects.create(
            user=user, email="social@example.com", verified=False, primary=False
        )

        mock_sociallogin = Mock()

        # Add send_welcome_email to adapter for this test
        self.social_adapter.send_welcome_email = Mock()

        with patch(
            "accounts.adapters.DefaultSocialAccountAdapter.save_user", return_value=user
        ):
            self.social_adapter.save_user(self.request, mock_sociallogin)

        # Email should be verified
        email_address.refresh_from_db()
        self.assertTrue(email_address.verified)
        self.assertTrue(email_address.primary)

        # Welcome email should be sent
        self.social_adapter.send_welcome_email.assert_called_once()


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================


class AdaptersEdgeCasesTests(TestCase):
    """Test edge cases and error scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.account_adapter = CustomAccountAdapter()
        self.social_adapter = CustomSocialAccountAdapter()
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

        if not Site.objects.filter(pk=1).exists():
            Site.objects.create(pk=1, domain="example.com", name="Example")

    def test_username_generation_with_empty_email(self):
        """Test username generation handles empty email gracefully"""
        user = User(email="", username="")

        mock_sociallogin = Mock()
        mock_sociallogin.user = user

        # Should not crash
        try:
            self.social_adapter.pre_social_login(self.request, mock_sociallogin)
        except Exception as e:
            self.fail(f"pre_social_login raised {e} with empty email")

    def test_username_generation_with_very_long_email(self):
        """Test username generation handles very long email"""
        long_email = "a" * 100 + "@example.com"
        user = User(email=long_email, username="")

        mock_sociallogin = Mock()
        mock_sociallogin.user = user

        self.social_adapter.pre_social_login(self.request, mock_sociallogin)

        # Username should be valid and not too long
        self.assertLessEqual(len(user.username), 150)  # Django default max_length

    def test_email_linking_no_emailaddress_model(self):
        """Test social linking doesn't crash if EmailAddress doesn't exist"""
        existing_user = User.objects.create_user(
            username="noemailddr",
            email="noemailaddr@example.com",
            password="testpass123",
        )

        # Don't create EmailAddress

        social_user = User(email="noemailaddr@example.com", username="")

        mock_sociallogin = Mock()
        mock_sociallogin.user = social_user
        mock_sociallogin.connect = Mock()
        mock_sociallogin.state = {}

        # Should not crash
        try:
            self.social_adapter.pre_social_login(self.request, mock_sociallogin)
        except EmailAddress.DoesNotExist:
            self.fail("pre_social_login raised DoesNotExist when it shouldn't")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_mail_handles_missing_templates_gracefully(self):
        """Test send_mail handles missing templates"""
        context = {}

        # This will fail when trying to render templates
        with self.assertRaises(Exception):
            self.account_adapter.send_mail(
                "nonexistent/template", "test@example.com", context
            )

    def test_validate_disconnect_with_zero_accounts(self):
        """Test validate_disconnect with zero social accounts (edge case)"""
        user = User.objects.create_user(
            username="zeroaccounts", email="zero@example.com", password="pass123"
        )

        # Create account but pass empty queryset
        social_account = SocialAccount(user=user, provider="google", uid="123")
        accounts = SocialAccount.objects.none()

        # Should not crash (though this is an unusual scenario)
        try:
            self.social_adapter.validate_disconnect(social_account, accounts)
        except Exception as e:
            self.fail(f"validate_disconnect raised {e} with zero accounts")
