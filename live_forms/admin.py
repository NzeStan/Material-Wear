# live_forms/admin.py
"""
Admin for Live Forms app.

Mirrors bulk_orders/admin.py A-Z:
  - LiveFormEntryInline        ≡  CouponCodeInline  (readonly, tabular)
  - IsExpiredFilter            ≡  HasCouponFilter    (custom SimpleListFilter)
  - LiveFormEntryAdmin         ≡  OrderEntryAdmin
  - LiveFormLinkAdmin          ≡  BulkOrderLinkAdmin
    → download_pdf_action      ≡  download_pdf_action
    → download_word_action     ≡  download_word_action
    → download_excel_action    ≡  download_excel_action
    → copy_link_action         ✦  NEW: copies shareable URL into admin message

custom_name column surfaces in all exports ONLY when
custom_branding_enabled=True — same conditional as bulk_orders.

Shareable link is built using settings.FRONTEND_URL so the URL
always points to the real frontend, not the Django admin host.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
import logging

from .models import LiveFormLink, LiveFormEntry
from .utils import (
    generate_live_form_pdf,
    generate_live_form_word,
    generate_live_form_excel,
)

logger = logging.getLogger(__name__)


def _build_shareable_url(obj):
    """
    Build the absolute shareable URL for a LiveFormLink.
    Uses settings.FRONTEND_URL when available so the link always
    points to the real frontend, not the Django admin host.
    Falls back to the relative path if FRONTEND_URL is not set.
    """
    base = getattr(settings, "FRONTEND_URL", "").rstrip("/")
    if base:
        return f"{base}/live-form/{obj.slug}/"
    return f"/live-form/{obj.slug}/"


# ---------------------------------------------------------------------------
# Inline  (≡ CouponCodeInline)
# ---------------------------------------------------------------------------

class LiveFormEntryInline(admin.TabularInline):
    model = LiveFormEntry
    extra = 0
    readonly_fields = [
        "serial_number",
        "full_name",
        "custom_name",
        "size",
        "created_at",
    ]
    fields = [
        "serial_number",
        "full_name",
        "custom_name",
        "size",
        "created_at",
    ]
    can_delete = False
    max_num = 0
    show_change_link = True
    ordering = ["serial_number"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request)


# ---------------------------------------------------------------------------
# Custom filters  (≡ HasCouponFilter)
# ---------------------------------------------------------------------------

class IsExpiredFilter(admin.SimpleListFilter):
    title = "Expiry Status"
    parameter_name = "is_expired"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Expired"),
            ("no", "Active / Not Yet Expired"),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == "yes":
            return queryset.filter(expires_at__lt=now)
        if self.value() == "no":
            return queryset.filter(expires_at__gte=now)
        return queryset


class HasSubmissionsFilter(admin.SimpleListFilter):
    title = "Submission Status"
    parameter_name = "has_submissions"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Has Submissions"),
            ("no", "No Submissions Yet"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(entry_count__gt=0)
        if self.value() == "no":
            return queryset.filter(entry_count=0)
        return queryset


# ---------------------------------------------------------------------------
# LiveFormEntryAdmin  (≡ OrderEntryAdmin)
# ---------------------------------------------------------------------------

@admin.register(LiveFormEntry)
class LiveFormEntryAdmin(admin.ModelAdmin):
    list_display = [
        "serial_number",
        "full_name",
        "custom_name_display",
        "size",
        "live_form_link",
        "created_at",
    ]
    list_filter = ["size", "live_form", "created_at"]
    search_fields = ["full_name", "custom_name", "live_form__organization_name"]
    readonly_fields = [
        "id",
        "serial_number",
        "live_form",
        "full_name",
        "custom_name",
        "size",
        "created_at",
        "updated_at",
    ]
    ordering = ["live_form", "serial_number"]

    def custom_name_display(self, obj):
        if obj.live_form.custom_branding_enabled and obj.custom_name:
            return obj.custom_name
        return "—"
    custom_name_display.short_description = "Custom Name"

    def live_form_link(self, obj):
        url = reverse("admin:live_forms_liveformlink_change", args=[obj.live_form.id])
        return format_html('<a href="{}">{}</a>', url, obj.live_form.organization_name)
    live_form_link.short_description = "Live Form"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# LiveFormLinkAdmin  (≡ BulkOrderLinkAdmin)
# ---------------------------------------------------------------------------

@admin.register(LiveFormLink)
class LiveFormLinkAdmin(admin.ModelAdmin):
    list_display = [
        "organization_name",
        "shareable_link_display",       # ← replaces raw slug; clickable + copyable
        "entry_count_display",
        "custom_branding_enabled",
        "is_active",
        "expiry_status",
        "expires_at",
        "view_count",
        "last_submission_at",
        "created_by",
        "created_at",
    ]
    list_filter = [
        IsExpiredFilter,
        HasSubmissionsFilter,
        "custom_branding_enabled",
        "is_active",
        "created_at",
    ]
    search_fields = ["organization_name", "slug", "created_by__username"]
    readonly_fields = [
        "id",
        "slug",
        "shareable_link_display",       # ← prominent on the detail page
        "view_count",
        "last_submission_at",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    inlines = [LiveFormEntryInline]
    actions = [
        "copy_link_action",             # ← surfaces the full URL in admin flash message
        "download_pdf_action",
        "download_word_action",
        "download_excel_action",
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(entry_count=Count("entries"))

    # ── Display helpers ──────────────────────────────────────────────────

    def shareable_link_display(self, obj):
        """
        Renders a fully absolute, one-click-openable shareable link.
        On the list page: truncated for column width but still clickable.
        On the detail page: full URL in monospace so it's easy to copy.
        """
        url = _build_shareable_url(obj)
        return format_html(
            '<a href="{url}" target="_blank" rel="noopener noreferrer" '
            'title="Open live form" '
            'style="color:#064E3B; font-weight:600; '
            'font-family:monospace; font-size:11px; '
            'text-decoration:none; word-break:break-all;">'
            '🔗 {url}'
            '</a>',
            url=url,
        )
    shareable_link_display.short_description = "Shareable Link"

    def entry_count_display(self, obj):
        return obj.entry_count
    entry_count_display.short_description = "Entries"
    entry_count_display.admin_order_field = "entry_count"

    def expiry_status(self, obj):
        if not obj.is_active:
            return mark_safe('<span style="color:#6B7280;">⚫ Deactivated</span>')
        if obj.is_expired():
            return mark_safe('<span style="color:#DC2626;">🔴 Expired</span>')
        return mark_safe('<span style="color:#059669;">🟢 Active</span>')
    expiry_status.short_description = "Status"

    # ── Admin actions  (≡ BulkOrderLinkAdmin actions) ────────────────────

    def copy_link_action(self, request, queryset):
        """
        Surfaces the full shareable URL in the admin success message
        so it can be easily copied and sent to participants.
        Works for single or multiple selected forms.
        """
        for live_form in queryset:
            url = _build_shareable_url(live_form)
            self.message_user(
                request,
                format_html(
                    '<strong>{name}</strong> — shareable link: '
                    '<a href="{url}" target="_blank" '
                    'style="font-family:monospace; color:#064E3B;">'
                    '{url}</a>',
                    name=live_form.organization_name,
                    url=url,
                ),
                messages.SUCCESS,
            )

    copy_link_action.short_description = "🔗 Get Shareable Link"

    def download_pdf_action(self, request, queryset):
        """Generate PDF for the selected live form."""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one live form for PDF generation.",
                messages.WARNING,
            )
            return
        live_form = queryset.first()
        return self._generate_pdf(request, live_form)

    download_pdf_action.short_description = "📄 Download PDF"

    def download_word_action(self, request, queryset):
        """Generate Word document for the selected live form."""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one live form for Word generation.",
                messages.WARNING,
            )
            return
        live_form = queryset.first()
        return self._generate_word(request, live_form)

    download_word_action.short_description = "📝 Download Word"

    def download_excel_action(self, request, queryset):
        """Generate Excel spreadsheet for the selected live form."""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one live form for Excel generation.",
                messages.WARNING,
            )
            return
        live_form = queryset.first()
        return self._generate_excel(request, live_form)

    download_excel_action.short_description = "📊 Download Excel"

    # ── Internal generators  (≡ BulkOrderLinkAdmin._generate_*) ─────────

    def _generate_pdf(self, request, live_form):
        try:
            return generate_live_form_pdf(live_form, request)
        except ImportError:
            messages.error(
                request,
                "PDF generation not available. Install GTK+ libraries.",
            )
            return None
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            messages.error(request, f"Error generating PDF: {str(e)}")
            return None

    def _generate_word(self, request, live_form):
        try:
            return generate_live_form_word(live_form)
        except Exception as e:
            logger.error(f"Error generating Word document: {str(e)}")
            messages.error(request, f"Error generating Word document: {str(e)}")
            return None

    def _generate_excel(self, request, live_form):
        try:
            return generate_live_form_excel(live_form)
        except Exception as e:
            logger.error(f"Error generating Excel: {str(e)}")
            messages.error(request, f"Error generating Excel: {str(e)}")
            return None