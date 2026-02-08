# image_bulk_orders/admin.py
"""
Django Admin for Image Bulk Orders.

Features:
- Optimized list views with annotations
- Document generation actions
- Image preview thumbnails
- Color-coded status indicators
- Batch operations
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Count, Q
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from io import BytesIO
import logging

from .models import ImageBulkOrderLink, ImageOrderEntry, ImageCouponCode
from .utils import (
    generate_coupon_codes,
    generate_bulk_documents_with_images,
    download_all_images_zip,
)

logger = logging.getLogger(__name__)


# ============================================================================
# INLINES
# ============================================================================

class ImageCouponCodeInline(admin.TabularInline):
    """Inline display of coupon codes"""
    model = ImageCouponCode
    extra = 0
    readonly_fields = ['code', 'is_used', 'created_at']
    fields = ['code', 'is_used', 'created_at']
    can_delete = False
    max_num = 0
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.order_by('-created_at')


# ============================================================================
# FILTERS
# ============================================================================

class HasCouponFilter(admin.SimpleListFilter):
    """Filter orders by coupon status"""
    title = 'Coupon Status'
    parameter_name = 'has_coupon'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Has Coupon'),
            ('no', 'No Coupon'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(coupon_used__isnull=False)
        if self.value() == 'no':
            return queryset.filter(coupon_used__isnull=True)


class GenerationStatusFilter(admin.SimpleListFilter):
    """Filter by document generation status"""
    title = 'Generation Status'
    parameter_name = 'generation_status'
    
    def lookups(self, request, model_admin):
        return ImageBulkOrderLink.GENERATION_STATUS_CHOICES
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(generation_status=self.value())


# ============================================================================
# ORDER ENTRY ADMIN
# ============================================================================

@admin.register(ImageOrderEntry)
class ImageOrderEntryAdmin(admin.ModelAdmin):
    list_display = [
        'serial_number_display',
        'full_name',
        'email',
        'size',
        'custom_name_display',
        'image_thumbnail',
        'bulk_order_link',
        'paid_status',
        'coupon_status',
        'created_at',
    ]
    
    list_filter = [
        'paid',
        HasCouponFilter,
        'size',
        'bulk_order',
        'created_at',
    ]
    
    search_fields = [
        'reference',
        'full_name',
        'email',
        'custom_name',
        'serial_number',
    ]
    
    readonly_fields = [
        'id',
        'reference',
        'serial_number',
        'uploaded_image',
        'cloudinary_public_id',
        'image_preview',
        'image_width',
        'image_height',
        'image_uploaded_at',
        'created_at',
        'updated_at',
    ]
    
    list_per_page = 50
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'reference', 'bulk_order', 'serial_number')
        }),
        ('Participant Details', {
            'fields': ('email', 'full_name', 'size', 'custom_name')
        }),
        ('Image Information', {
            'fields': (
                'uploaded_image',
                'cloudinary_public_id',
                'image_preview',
                'image_width',
                'image_height',
                'image_uploaded_at',
            )
        }),
        ('Payment Information', {
            'fields': ('coupon_used', 'paid')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def serial_number_display(self, obj):
        """Display serial number with color"""
        return format_html(
            '<span style="font-weight: bold; color: #064E3B;">#{:04d}</span>',
            obj.serial_number
        )
    serial_number_display.short_description = 'Serial #'
    serial_number_display.admin_order_field = 'serial_number'
    
    def custom_name_display(self, obj):
        """Display custom name if enabled"""
        if obj.bulk_order.custom_branding_enabled and obj.custom_name:
            return format_html(
                '<span style="color: #F59E0B; font-weight: bold;">{}</span>',
                obj.custom_name
            )
        return '-'
    custom_name_display.short_description = 'Custom Name'
    
    def image_thumbnail(self, obj):
        """Display image thumbnail in list view"""
        if obj.uploaded_image:
            # Cloudinary transformation for thumbnail
            url = obj.uploaded_image.replace('/upload/', '/upload/w_50,h_50,c_fill/')
            return format_html(
                '<img src="{}" style="border-radius: 4px; border: 2px solid #064E3B;" />',
                url
            )
        return '-'
    image_thumbnail.short_description = 'Image'
    
    def image_preview(self, obj):
        """Display larger image preview in detail view"""
        if obj.uploaded_image:
            # Cloudinary transformation for preview
            url = obj.uploaded_image.replace('/upload/', '/upload/w_300,h_300,c_limit/')
            return format_html(
                '<img src="{}" style="max-width: 300px; border-radius: 8px; border: 3px solid #064E3B;" />',
                url
            )
        return '-'
    image_preview.short_description = 'Image Preview'
    
    def bulk_order_link(self, obj):
        """Link to bulk order"""
        url = reverse('admin:image_bulk_orders_imagebulkorderlink_change', args=[obj.bulk_order.pk])
        return format_html(
            '<a href="{}" style="color: #064E3B; font-weight: bold;">{}</a>',
            url,
            obj.bulk_order.organization_name
        )
    bulk_order_link.short_description = 'Bulk Order'
    
    def paid_status(self, obj):
        """Display paid status with color"""
        if obj.paid:
            return format_html(
                '<span style="background-color: #064E3B; color: #FFFBEB; padding: 4px 12px; '
                'border-radius: 12px; font-weight: bold;">PAID</span>'
            )
        return format_html(
            '<span style="background-color: #DC2626; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-weight: bold;">UNPAID</span>'
        )
    paid_status.short_description = 'Payment'
    
    def coupon_status(self, obj):
        """Display coupon status"""
        if obj.coupon_used:
            return format_html(
                '<span style="background-color: #F59E0B; color: #064E3B; padding: 4px 8px; '
                'border-radius: 8px; font-weight: bold;">{}</span>',
                obj.coupon_used.code
            )
        return '-'
    coupon_status.short_description = 'Coupon'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('bulk_order', 'coupon_used')


# ============================================================================
# BULK ORDER LINK ADMIN
# ============================================================================

@admin.register(ImageBulkOrderLink)
class ImageBulkOrderLinkAdmin(admin.ModelAdmin):
    list_display = [
        'organization_name',
        'slug_display',
        'price_per_item',
        'custom_branding_enabled',
        'image_required',
        'payment_deadline',
        'total_orders',
        'total_paid',
        'coupon_count',
        'generation_status_display',
        'created_at',
    ]
    
    list_filter = [
        'custom_branding_enabled',
        'image_required',
        GenerationStatusFilter,
        'created_at',
        'payment_deadline',
    ]
    
    search_fields = [
        'organization_name',
        'slug',
    ]
    
    readonly_fields = [
        'id',
        'slug',
        'shareable_link',
        'generated_zip_link',
        'last_generated_at',
        'created_at',
        'updated_at',
    ]
    
    list_per_page = 20
    
    actions = [
        'generate_documents_action',
        'download_images_only_action',
        'generate_coupons_action',
    ]
    
    inlines = [ImageCouponCodeInline]
    
    fieldsets = (
        ('Organization Details', {
            'fields': ('id', 'organization_name', 'slug', 'shareable_link', 'created_by')
        }),
        ('Order Configuration', {
            'fields': (
                'price_per_item',
                'custom_branding_enabled',
                'payment_deadline',
                'image_required',
                'max_image_size_mb',
                'allowed_image_formats',
            )
        }),
        ('Document Generation', {
            'fields': (
                'generation_status',
                'last_generated_at',
                'generated_zip_link',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def slug_display(self, obj):
        """Display slug with styling"""
        return format_html(
            '<code style="background-color: #F3F4F6; padding: 4px 8px; '
            'border-radius: 4px; color: #064E3B;">{}</code>',
            obj.slug
        )
    slug_display.short_description = 'Slug'
    slug_display.admin_order_field = 'slug'
    
    def shareable_link(self, obj):
        """Display shareable link"""
        if obj.slug:
            url = obj.get_shareable_url()
            full_url = f"{settings.FRONTEND_URL}{url}" if hasattr(settings, 'FRONTEND_URL') else url
            return format_html(
                '<a href="{}" target="_blank" style="color: #064E3B; font-weight: bold;">{}</a> '
                '<button onclick="navigator.clipboard.writeText(\'{}\'); alert(\'Link copied!\');" '
                'style="background-color: #F59E0B; color: white; border: none; padding: 4px 12px; '
                'border-radius: 4px; cursor: pointer; margin-left: 8px;">📋 Copy</button>',
                full_url,
                full_url,
                full_url
            )
        return '-'
    shareable_link.short_description = 'Shareable Link'
    
    def generated_zip_link(self, obj):
        """Display download link for generated ZIP"""
        if obj.generated_zip_url:
            return format_html(
                '<a href="{}" target="_blank" style="background-color: #064E3B; color: #FFFBEB; '
                'padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: bold;">'
                '📦 Download ZIP</a>',
                obj.generated_zip_url
            )
        return format_html(
            '<span style="color: #9CA3AF;">Not generated yet</span>'
        )
    generated_zip_link.short_description = 'Generated Package'
    
    def generation_status_display(self, obj):
        """Display generation status with color"""
        colors = {
            'pending': '#9CA3AF',
            'processing': '#F59E0B',
            'completed': '#064E3B',
            'failed': '#DC2626',
        }
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-weight: bold; text-transform: uppercase;">{}</span>',
            colors.get(obj.generation_status, '#9CA3AF'),
            obj.get_generation_status_display()
        )
    generation_status_display.short_description = 'Generation'
    generation_status_display.admin_order_field = 'generation_status'
    
    def total_orders(self, obj):
        """Display total orders count"""
        count = obj.orders.count()
        return format_html(
            '<span style="font-weight: bold; color: #064E3B;">{}</span>',
            count
        )
    total_orders.short_description = 'Total Orders'
    
    def total_paid(self, obj):
        """Display total paid orders count"""
        count = obj.orders.filter(paid=True).count()
        return format_html(
            '<span style="font-weight: bold; color: #059669;">{}</span>',
            count
        )
    total_paid.short_description = 'Paid'
    
    def coupon_count(self, obj):
        """Display coupon count"""
        total = obj.coupons.count()
        used = obj.coupons.filter(is_used=True).count()
        return format_html(
            '<span style="color: #F59E0B; font-weight: bold;">{}</span> / {}',
            used,
            total
        )
    coupon_count.short_description = 'Coupons (Used/Total)'
    
    def get_queryset(self, request):
        """Optimize queryset with annotations"""
        qs = super().get_queryset(request)
        return qs.select_related('created_by').annotate(
            _total_orders=Count('orders'),
            _paid_orders=Count('orders', filter=Q(orders__paid=True)),
        )
    
    # ========================================================================
    # ACTIONS
    # ========================================================================
    
    def generate_documents_action(self, request, queryset):
        """
        Generate complete document package with images.
        
        Creates: PDF + Word + Excel + Organized Images in ZIP
        """
        for bulk_order in queryset:
            try:
                # Check if there are paid orders
                if not bulk_order.orders.filter(paid=True).exists():
                    messages.warning(
                        request,
                        f"No paid orders for {bulk_order.organization_name}. Skipping."
                    )
                    continue
                
                # Generate documents
                zip_url = generate_bulk_documents_with_images(bulk_order, request=request)
                
                messages.success(
                    request,
                    format_html(
                        'Documents generated for <strong>{}</strong>. '
                        '<a href="{}" target="_blank" style="color: #064E3B; '
                        'font-weight: bold;">📦 Download ZIP</a>',
                        bulk_order.organization_name,
                        zip_url
                    )
                )
                
            except Exception as e:
                logger.error(f"Error generating documents: {str(e)}")
                messages.error(
                    request,
                    f"Error generating documents for {bulk_order.organization_name}: {str(e)}"
                )
    
    generate_documents_action.short_description = "📦 Generate Complete Package (PDF + Word + Excel + Images)"
    
    def download_images_only_action(self, request, queryset):
        """Quick action to download images only (no documents)"""
        if queryset.count() != 1:
            messages.error(request, "Please select exactly one bulk order")
            return
        
        bulk_order = queryset.first()
        
        try:
            # Check if there are paid orders
            if not bulk_order.orders.filter(paid=True).exists():
                messages.warning(request, "No paid orders with images")
                return
            
            # Generate images ZIP
            zip_buffer = download_all_images_zip(bulk_order)
            
            # Return as download
            response = HttpResponse(
                zip_buffer.read(),
                content_type='application/zip'
            )
            response['Content-Disposition'] = f'attachment; filename="images_{bulk_order.slug}.zip"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error downloading images: {str(e)}")
            messages.error(request, f"Error: {str(e)}")
    
    download_images_only_action.short_description = "🖼️ Download Images Only (ZIP)"
    
    def generate_coupons_action(self, request, queryset):
        """Generate coupon codes"""
        for bulk_order in queryset:
            if bulk_order.coupons.exists():
                messages.warning(
                    request,
                    f"{bulk_order.organization_name} already has {bulk_order.coupons.count()} coupons"
                )
                continue
            
            try:
                count = 50  # Default count
                coupons = generate_coupon_codes(bulk_order, count=count)
                messages.success(
                    request,
                    f"Generated {len(coupons)} coupons for {bulk_order.organization_name}"
                )
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
    
    generate_coupons_action.short_description = "🎟️ Generate Coupons (50 codes)"


# ============================================================================
# COUPON CODE ADMIN
# ============================================================================

@admin.register(ImageCouponCode)
class ImageCouponCodeAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'bulk_order_link',
        'is_used_display',
        'created_at',
    ]
    
    list_filter = [
        'is_used',
        'bulk_order',
        'created_at',
    ]
    
    search_fields = [
        'code',
        'bulk_order__organization_name',
    ]
    
    readonly_fields = [
        'id',
        'code',
        'created_at',
    ]
    
    list_per_page = 50
    
    def bulk_order_link(self, obj):
        """Link to bulk order"""
        url = reverse('admin:image_bulk_orders_imagebulkorderlink_change', args=[obj.bulk_order.pk])
        return format_html(
            '<a href="{}" style="color: #064E3B; font-weight: bold;">{}</a>',
            url,
            obj.bulk_order.organization_name
        )
    bulk_order_link.short_description = 'Bulk Order'
    
    def is_used_display(self, obj):
        """Display usage status with color"""
        if obj.is_used:
            return format_html(
                '<span style="background-color: #DC2626; color: white; padding: 4px 12px; '
                'border-radius: 12px; font-weight: bold;">USED</span>'
            )
        return format_html(
            '<span style="background-color: #059669; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-weight: bold;">AVAILABLE</span>'
        )
    is_used_display.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('bulk_order')