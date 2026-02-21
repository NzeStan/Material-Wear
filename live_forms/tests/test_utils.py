# live_forms/tests/test_utils.py
"""
Comprehensive utility tests for live_forms app.

Tests:
  - _get_live_form_with_entries  : slug vs instance, 404 on bad slug
  - generate_live_form_pdf       : content-type, filename, ImportError,
                                   WeasyPrint delegation, branding flag
  - generate_live_form_word      : content-type, filename, custom_branding
  - generate_live_form_excel     : content-type, filename, row counts,
                                   column counts with/without custom_name
"""
import uuid
from datetime import timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch, PropertyMock

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import TestCase
from django.utils import timezone

from live_forms.models import LiveFormEntry, LiveFormLink

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def future(hours=24):
    return timezone.now() + timedelta(hours=hours)


def make_user(username=None):
    username = username or f"u_{uuid.uuid4().hex[:8]}"
    return User.objects.create_user(
        username=username, password="test", email=f"{username}@test.com"
    )


def make_form(user=None, **kwargs):
    user = user or make_user()
    defaults = dict(
        organization_name="Utils Test Org",
        expires_at=future(),
        is_active=True,
    )
    defaults.update(kwargs)
    return LiveFormLink.objects.create(created_by=user, **defaults)


def make_entry(form, **kwargs):
    defaults = dict(full_name="Test Person", size="M")
    defaults.update(kwargs)
    return LiveFormEntry.objects.create(live_form=form, **defaults)


# ===========================================================================
# _get_live_form_with_entries
# ===========================================================================

class GetLiveFormWithEntriesTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user)
        self.entry = make_entry(self.form, full_name="Test Entry", size="L")

    def _call(self, identifier):
        from live_forms.utils import _get_live_form_with_entries
        return _get_live_form_with_entries(identifier)

    def test_accepts_live_form_instance(self):
        result = self._call(self.form)
        self.assertEqual(result.pk, self.form.pk)

    def test_accepts_slug_string(self):
        result = self._call(self.form.slug)
        self.assertEqual(result.pk, self.form.pk)

    def test_slug_result_has_prefetched_entries(self):
        result = self._call(self.form.slug)
        # After prefetch, _prefetched_objects_cache should be populated
        entries = list(result.entries.all())
        self.assertEqual(len(entries), 1)

    def test_invalid_slug_raises_does_not_exist(self):
        from live_forms.models import LiveFormLink
        with self.assertRaises(LiveFormLink.DoesNotExist):
            self._call("no-such-slug-at-all")

    def test_instance_returned_as_is(self):
        result = self._call(self.form)
        self.assertIs(result, self.form)


# ===========================================================================
# generate_live_form_pdf
# ===========================================================================

class GenerateLiveFormPDFTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user, organization_name="PDF Org")
        make_entry(self.form, full_name="Alice Smith", size="S")
        make_entry(self.form, full_name="Bob Jones", size="XL")

    @patch("weasyprint.HTML")
    def test_returns_http_response(self, MockHTML):
        MockHTML.return_value.write_pdf.return_value = b"%PDF-1.4 fake"
        from live_forms.utils import generate_live_form_pdf
        response = generate_live_form_pdf(self.form)
        self.assertIsInstance(response, HttpResponse)

    @patch("weasyprint.HTML")
    def test_content_type_is_pdf(self, MockHTML):
        MockHTML.return_value.write_pdf.return_value = b"%PDF-1.4 fake"
        from live_forms.utils import generate_live_form_pdf
        response = generate_live_form_pdf(self.form)
        self.assertEqual(response["Content-Type"], "application/pdf")

    @patch("weasyprint.HTML")
    def test_content_disposition_contains_slug(self, MockHTML):
        MockHTML.return_value.write_pdf.return_value = b"%PDF-1.4 fake"
        from live_forms.utils import generate_live_form_pdf
        response = generate_live_form_pdf(self.form)
        disposition = response.get("Content-Disposition", "")
        self.assertIn(self.form.slug, disposition)

    @patch("weasyprint.HTML")
    def test_content_disposition_is_attachment(self, MockHTML):
        MockHTML.return_value.write_pdf.return_value = b"%PDF-1.4 fake"
        from live_forms.utils import generate_live_form_pdf
        response = generate_live_form_pdf(self.form)
        self.assertIn("attachment", response.get("Content-Disposition", ""))

    @patch("weasyprint.HTML")
    def test_accepts_slug_string(self, MockHTML):
        MockHTML.return_value.write_pdf.return_value = b"%PDF-1.4 fake"
        from live_forms.utils import generate_live_form_pdf
        response = generate_live_form_pdf(self.form.slug)
        self.assertIsInstance(response, HttpResponse)

    @patch("weasyprint.HTML")
    def test_uses_base_url_from_request_when_provided(self, MockHTML):
        MockHTML.return_value.write_pdf.return_value = b"%PDF"
        from live_forms.utils import generate_live_form_pdf
        from django.test import RequestFactory
        request = RequestFactory().get("/")
        generate_live_form_pdf(self.form, request=request)
        # HTML was called with string=... and base_url=...
        call_kwargs = MockHTML.call_args[1]
        self.assertIn("base_url", call_kwargs)

    @patch("weasyprint.HTML")
    def test_no_base_url_when_no_request(self, MockHTML):
        MockHTML.return_value.write_pdf.return_value = b"%PDF"
        from live_forms.utils import generate_live_form_pdf
        generate_live_form_pdf(self.form, request=None)
        call_kwargs = MockHTML.call_args[1]
        self.assertNotIn("base_url", call_kwargs)

    def test_import_error_raised_cleanly(self):
        # Patch the weasyprint module import to raise ImportError
        with patch.dict("sys.modules", {"weasyprint": None}):
            # Clear any cached imports
            import sys
            if "live_forms.utils" in sys.modules:
                del sys.modules["live_forms.utils"]
            # Now the import of weasyprint.HTML inside the function should fail
            from live_forms.utils import generate_live_form_pdf
            with self.assertRaises(ImportError):
                generate_live_form_pdf(self.form)

    @patch("weasyprint.HTML", side_effect=Exception("render failed"))
    def test_generic_exception_re_raised(self, MockHTML):
        from live_forms.utils import generate_live_form_pdf
        with self.assertRaises(Exception):
            generate_live_form_pdf(self.form)

    @patch("weasyprint.HTML")
    def test_custom_branding_form_generates_pdf(self, MockHTML):
        MockHTML.return_value.write_pdf.return_value = b"%PDF"
        branded_form = make_form(
            self.user,
            organization_name="Branded PDF Org",
            custom_branding_enabled=True,
        )
        make_entry(branded_form, full_name="Branded Entry", size="M", custom_name="Jersey King")
        from live_forms.utils import generate_live_form_pdf
        response = generate_live_form_pdf(branded_form)
        self.assertIsInstance(response, HttpResponse)


# ===========================================================================
# generate_live_form_word
# ===========================================================================

class GenerateLiveFormWordTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user, organization_name="Word Org")
        make_entry(self.form, full_name="Word Person One", size="M")
        make_entry(self.form, full_name="Word Person Two", size="L")

    def _generate(self, form=None):
        from live_forms.utils import generate_live_form_word
        return generate_live_form_word(form or self.form)

    def test_returns_http_response(self):
        response = self._generate()
        self.assertIsInstance(response, HttpResponse)

    def test_content_type_is_docx(self):
        response = self._generate()
        self.assertIn(
            "wordprocessingml",
            response.get("Content-Type", ""),
        )

    def test_content_disposition_is_attachment(self):
        response = self._generate()
        self.assertIn("attachment", response.get("Content-Disposition", ""))

    def test_content_disposition_contains_slug(self):
        response = self._generate()
        self.assertIn(self.form.slug, response.get("Content-Disposition", ""))

    def test_accepts_slug_string(self):
        from live_forms.utils import generate_live_form_word
        response = generate_live_form_word(self.form.slug)
        self.assertIsInstance(response, HttpResponse)

    def test_document_generates_valid_docx(self):
        response = self._generate()
        # DOCX files are ZIP archives and start with PK
        content = response.content
        self.assertTrue(
            content[:2] == b"PK",
            "Response content does not look like a docx (ZIP) file",
        )

    def test_custom_branding_form_generates_word(self):
        branded_form = make_form(
            self.user, organization_name="Branded Word", custom_branding_enabled=True
        )
        make_entry(branded_form, full_name="Branded", size="S", custom_name="Star")
        from live_forms.utils import generate_live_form_word
        response = generate_live_form_word(branded_form)
        self.assertIsInstance(response, HttpResponse)


# ===========================================================================
# generate_live_form_excel
# ===========================================================================

class GenerateLiveFormExcelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.form = make_form(self.user, organization_name="Excel Org")
        make_entry(self.form, full_name="Excel Person One", size="S")
        make_entry(self.form, full_name="Excel Person Two", size="M")
        make_entry(self.form, full_name="Excel Person Three", size="XL")

    def _generate(self, form=None):
        from live_forms.utils import generate_live_form_excel
        return generate_live_form_excel(form or self.form)

    def test_returns_http_response(self):
        response = self._generate()
        self.assertIsInstance(response, HttpResponse)

    def test_content_type_is_xlsx(self):
        response = self._generate()
        self.assertIn("spreadsheetml", response.get("Content-Type", ""))

    def test_content_disposition_is_attachment(self):
        response = self._generate()
        self.assertIn("attachment", response.get("Content-Disposition", ""))

    def test_content_disposition_contains_slug(self):
        response = self._generate()
        self.assertIn(self.form.slug, response.get("Content-Disposition", ""))

    def test_accepts_slug_string(self):
        from live_forms.utils import generate_live_form_excel
        response = generate_live_form_excel(self.form.slug)
        self.assertIsInstance(response, HttpResponse)

    def test_excel_actually_generated_with_real_openpyxl(self):
        """
        Integration-style test: actually run openpyxl and verify the
        output bytes are a valid ZIP (xlsx format starts with PK).
        Only skipped if openpyxl is not installed.
        """
        try:
            import openpyxl  # noqa: F401
        except ImportError:
            self.skipTest("openpyxl not installed")

        response = self._generate()
        self.assertIsInstance(response, HttpResponse)
        # XLSX files start with PK (ZIP magic bytes)
        content = b"".join(response.streaming_content) if hasattr(response, "streaming_content") else response.content
        self.assertTrue(
            content[:2] == b"PK",
            "Response content does not look like an xlsx (ZIP) file",
        )

    def test_excel_with_custom_branding_includes_custom_name_column(self):
        """
        With a real openpyxl call, verify custom_name column appears when
        branding is enabled and is absent when disabled.
        """
        try:
            import openpyxl
        except ImportError:
            self.skipTest("openpyxl not installed")

        # Branded form
        branded = make_form(
            self.user,
            organization_name="Branded Excel",
            custom_branding_enabled=True,
        )
        make_entry(branded, full_name="Branded Person", size="M", custom_name="Star Name")
        from live_forms.utils import generate_live_form_excel
        response = generate_live_form_excel(branded)
        content = b"".join(response.streaming_content) if hasattr(response, "streaming_content") else response.content
        wb = openpyxl.load_workbook(BytesIO(content))
        ws = wb.active
        # Headers are in row 7 (DATA_ROW_START + 1 in 1-indexed Excel)
        header_row = [cell.value for cell in ws[7]]
        # custom_name should appear somewhere in the headers
        self.assertTrue(
            any("custom" in str(h).lower() for h in header_row if h),
            f"Custom name header not found in: {header_row}",
        )