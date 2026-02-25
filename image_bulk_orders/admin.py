# image_bulk_orders/admin.py
"""
Admin interface for Image Bulk Orders.
IDENTICAL to bulk_orders admin with package download action.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Count, Q
from django.contrib import messages
import logging

from .models import ImageBulkOrderLink, ImageOrderEntry, ImageCouponCode
from .utils import (
    generate_coupon_codes_image,
    generate_image_bulk_order_pdf,
    generate_image_bulk_order_word,
    generate_image_bulk_order_excel,
    generate_admin_package_with_images,
)

logger = logging.getLogger(__name__)


class ImageCouponCodeInline(admin.TabularInline):
    model = ImageCouponCode
    extra = 0
    readonly_fields = ["code", "is_used", "created_at"]
    fields = ["code", "is_used", "created_at"]
    can_delete = False
    max_num = 0

    def has_add_permission(self, request, obj=None):
        return False


class HasCouponFilter(admin.SimpleListFilter):
    title = "Coupon Status"
    parameter_name = "has_coupon"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Has Coupon"),
            ("no", "No Coupon"),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(coupon_used__isnull=False)
        if self.value() == "no":
            return queryset.filter(coupon_used__isnull=True)


@admin.register(ImageOrderEntry)
class ImageOrderEntryAdmin(admin.ModelAdmin):
    list_display = [
        "serial_number",
        "full_name",
        "email",
        "size",
        "custom_name_display",
        "image_thumbnail",
        "bulk_order_link",
        "paid_status",
        "coupon_status",
        "created_at",
    ]
    list_filter = ["paid", "size", HasCouponFilter, "bulk_order", "created_at"]
    search_fields = ["full_name", "email", "reference"]
    readonly_fields = ["reference", "serial_number", "created_at", "updated_at", "image_preview"]
    list_per_page = 50

    fieldsets = (
        ("Order Information", {
            "fields": ("reference", "serial_number", "bulk_order", "created_at", "updated_at")
        }),
        ("Participant Details", {
            "fields": ("email", "full_name", "size", "custom_name")
        }),
        ("Image", {
            "fields": ("image", "image_preview")
        }),
        ("Payment Status", {
            "fields": ("paid", "coupon_used")
        }),
    )

    def bulk_order_link(self, obj):
        url = reverse("admin:image_bulk_orders_imagebulkorderlink_change", args=[obj.bulk_order.id])
        return format_html('<a href="{}">{}</a>', url, obj.bulk_order.organization_name)
    bulk_order_link.short_description = "Bulk Order"

    def paid_status(self, obj):
        if obj.paid:
            return mark_safe('<span style="color: green; font-weight: bold;">✓ Paid</span>')
        return mark_safe('<span style="color: orange;">⏳ Pending</span>')
    paid_status.short_description = "Payment"

    def coupon_status(self, obj):
        if obj.coupon_used:
            return format_html('<span style="color: blue;">🎟️ {}</span>', obj.coupon_used.code)
        return mark_safe('<span style="color: gray;">—</span>')
    coupon_status.short_description = "Coupon"

    def custom_name_display(self, obj):
        if obj.custom_name:
            return obj.custom_name
        return mark_safe('<span style="color: gray;">—</span>')
    custom_name_display.short_description = "Custom Name"

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return mark_safe('<span style="color: gray;">No image</span>')
    image_thumbnail.short_description = "Image"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border-radius: 8px;" />',
                obj.image.url
            )
        return "No image uploaded"
    image_preview.short_description = "Image Preview"


@admin.register(ImageBulkOrderLink)
class ImageBulkOrderLinkAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "organization_name",
        "slug",
        "price_per_item",
        "custom_branding_enabled",
        "payment_deadline",
        "total_orders",
        "total_paid",
        "coupon_count",
        "created_at",
    ]
    list_filter = ["custom_branding_enabled", "created_at", "payment_deadline"]
    search_fields = ["organization_name", "slug"]
    readonly_fields = ["created_at", "updated_at", "slug", "shareable_link"]
    list_per_page = 20
    actions = [
        'download_package_action',
        'download_pdf_action',
        'download_word_action',
        'download_excel_action',
        'generate_coupons_action'
    ]

    inlines = [ImageCouponCodeInline]

    fieldsets = (
        ("Organization Details", {
            "fields": ("organization_name", "slug", "shareable_link", "created_by")
        }),
        ("Order Configuration", {
            "fields": ("price_per_item", "custom_branding_enabled", "payment_deadline")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def shareable_link(self, obj):
        if obj.slug:
            url = obj.get_shareable_url()
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "—"
    shareable_link.short_description = "Shareable Link"

    def total_orders(self, obj):
        count = obj.orders.count()
        return format_html('<strong>{}</strong>', count)
    total_orders.short_description = "Orders"
    total_orders.admin_order_field = "orders__count"

    def total_paid(self, obj):
        count = obj.orders.filter(paid=True).count()
        return format_html('<span style="color: green;">{}</span>', count)
    total_paid.short_description = "Paid"

    def coupon_count(self, obj):
        return obj.coupons.count()
    coupon_count.short_description = "Coupons"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(order_count=Count('orders'))

    def download_package_action(self, request, queryset):
        """Download complete package: PDF + Word + Excel + Images"""
        if queryset.count() > 1:
            self.message_user(request, "Please select only one bulk order.", messages.WARNING)
            return
        
        bulk_order = queryset.first()
        try:
            return generate_admin_package_with_images(bulk_order.id)
        except Exception as e:
            logger.error(f"Error generating package: {str(e)}")
            messages.error(request, f"Error generating package: {str(e)}")
    
    download_package_action.short_description = "📦 Download Complete Package (PDF+Word+Excel+Images)"

    def download_pdf_action(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one bulk order.", messages.WARNING)
            return
        return generate_image_bulk_order_pdf(queryset.first(), request)
    
    download_pdf_action.short_description = "📄 Download PDF"

    def download_word_action(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one bulk order.", messages.WARNING)
            return
        return generate_image_bulk_order_word(queryset.first())
    
    download_word_action.short_description = "📝 Download Word"

    def download_excel_action(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Please select only one bulk order.", messages.WARNING)
            return
        return generate_image_bulk_order_excel(queryset.first())
    
    download_excel_action.short_description = "📊 Download Excel"

    def generate_coupons_action(self, request, queryset):
        count = 0
        for bulk_order in queryset:
            if bulk_order.coupons.count() == 0:
                generate_coupon_codes_image(bulk_order, count=50)
                count += 1
        
        if count > 0:
            self.message_user(
                request,
                f"Successfully generated coupons for {count} bulk order(s).",
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                "No bulk orders needed coupon generation.",
                messages.WARNING
            )
    
    generate_coupons_action.short_description = "🎟️ Generate Coupons (50 per order)"


@admin.register(ImageCouponCode)
class ImageCouponCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'bulk_order_link', 'is_used', 'created_at']
    list_filter = ['is_used', 'bulk_order', 'created_at']
    search_fields = ['code', 'bulk_order__organization_name']
    readonly_fields = ['code', 'created_at']

    def bulk_order_link(self, obj):
        url = reverse("admin:image_bulk_orders_imagebulkorderlink_change", args=[obj.bulk_order.id])
        return format_html('<a href="{}">{}</a>', url, obj.bulk_order.organization_name)
    bulk_order_link.short_description = "Bulk Order"

    def has_add_permission(self, request):
        return False
