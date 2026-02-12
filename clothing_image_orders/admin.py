# clothing_image_orders/admin.py
"""
Admin interface for clothing image orders.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Count, Q
import logging

from .models import ClothingImageOrder, ClothingOrderParticipant, ClothingCouponCode
from .utils import (
    generate_clothing_coupon_codes,
    generate_clothing_order_pdf,
    generate_clothing_order_word,
    generate_clothing_order_excel,
    generate_complete_package,
)

logger = logging.getLogger(__name__)


class ClothingCouponCodeInline(admin.TabularInline):
    """Inline admin for coupon codes"""
    
    model = ClothingCouponCode
    extra = 0
    readonly_fields = ['code', 'is_used', 'created_at']
    can_delete = False
    max_num = 0  # Don't allow adding through inline
    
    def has_add_permission(self, request, obj=None):
        return False


class ClothingOrderParticipantInline(admin.TabularInline):
    """Inline admin for participants"""
    
    model = ClothingOrderParticipant
    extra = 0
    readonly_fields = [
        'reference', 'serial_number', 'full_name', 'email', 
        'size', 'custom_name', 'image_preview', 'paid_badge', 'created_at'
    ]
    fields = [
        'serial_number', 'reference', 'full_name', 'email', 'size', 
        'custom_name', 'image_preview', 'paid_badge'
    ]
    can_delete = False
    max_num = 0
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def image_preview(self, obj):
        """Show small image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 40px; max-width: 60px;" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">No image</span>')
    image_preview.short_description = 'Image'
    
    def paid_badge(self, obj):
        """Show payment status badge"""
        if obj.coupon_used:
            return format_html(
                '<span style="background: #F59E0B; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">COUPON</span>'
            )
        elif obj.paid:
            return format_html(
                '<span style="background: #064E3B; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">PAID</span>'
            )
        else:
            return format_html(
                '<span style="background: #DC2626; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">PENDING</span>'
            )
    paid_badge.short_description = 'Status'


@admin.register(ClothingImageOrder)
class ClothingImageOrderAdmin(admin.ModelAdmin):
    """Admin for clothing image orders"""
    
    list_display = [
        'reference', 'organization_name', 'title', 'price_per_item',
        'requires_image_badge', 'is_active_badge', 'participant_count',
        'paid_count', 'image_count', 'created_at'
    ]
    
    list_filter = [
        'is_active', 'requires_image', 'requires_custom_name', 'created_at'
    ]
    
    search_fields = [
        'reference', 'organization_name', 'title', 
        'coordinator_name', 'coordinator_email'
    ]
    
    readonly_fields = [
        'id', 'reference', 'created_by', 'created_at', 'updated_at',
        'participant_stats_display'
    ]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('reference', 'title', 'description', 'is_active')
        }),
        ('Organization Details', {
            'fields': (
                'organization_name', 'coordinator_name', 
                'coordinator_email', 'coordinator_phone'
            )
        }),
        ('Order Configuration', {
            'fields': (
                'price_per_item', 'requires_custom_name', 
                'requires_image', 'order_deadline'
            )
        }),
        ('Statistics', {
            'fields': ('participant_stats_display',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ClothingOrderParticipantInline]
    
    actions = [
        'generate_coupons_action',
        'download_pdf_action',
        'download_word_action',
        'download_excel_action',
        'download_complete_package_action',  # ⭐ KEY ACTION
    ]
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.annotate(
            participant_total=Count('participants'),
            paid_total=Count('participants', filter=Q(participants__paid=True)),
            image_total=Count('participants', filter=~Q(participants__image=''))
        )
    
    # ==========================================================================
    # DISPLAY METHODS
    # ==========================================================================
    
    def requires_image_badge(self, obj):
        """Show if image is required"""
        if obj.requires_image:
            return format_html(
                '<span style="background: #DC2626; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">REQUIRED</span>'
            )
        return format_html(
            '<span style="background: #6B7280; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 10px; font-weight: bold;">OPTIONAL</span>'
        )
    requires_image_badge.short_description = 'Image'
    requires_image_badge.admin_order_field = 'requires_image'
    
    def is_active_badge(self, obj):
        """Show active status"""
        if obj.is_active:
            return format_html(
                '<span style="background: #064E3B; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">ACTIVE</span>'
            )
        return format_html(
            '<span style="background: #6B7280; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 10px; font-weight: bold;">CLOSED</span>'
        )
    is_active_badge.short_description = 'Status'
    is_active_badge.admin_order_field = 'is_active'
    
    def participant_count(self, obj):
        """Show total participants"""
        count = getattr(obj, 'participant_total', obj.participants.count())
        return format_html('<strong style="font-size: 14px;">{}</strong>', count)
    participant_count.short_description = 'Participants'
    participant_count.admin_order_field = 'participant_total'
    
    def paid_count(self, obj):
        """Show paid participants"""
        count = getattr(obj, 'paid_total', obj.participants.filter(paid=True).count())
        total = getattr(obj, 'participant_total', obj.participants.count())
        
        if total > 0:
            percentage = (count / total) * 100
            color = "#064E3B" if percentage > 80 else "#F59E0B" if percentage > 50 else "#DC2626"
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} / {} ({:.0f}%)</span>',
                color, count, total, percentage
            )
        return "0 / 0"
    paid_count.short_description = 'Paid'
    
    def image_count(self, obj):
        """Show participants with images"""
        count = getattr(obj, 'image_total', obj.participants.exclude(image='').count())
        return format_html('<strong>{}</strong>', count)
    image_count.short_description = 'With Images'
    image_count.admin_order_field = 'image_total'
    
    def participant_stats_display(self, obj):
        """Display detailed participant statistics"""
        stats = obj.get_participant_stats()
        
        html = f"""
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #F3F4F6;">
                <td style="padding: 8px; font-weight: bold;">Total Participants</td>
                <td style="padding: 8px;">{stats['total']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">Paid</td>
                <td style="padding: 8px; color: #064E3B; font-weight: bold;">{stats['paid']}</td>
            </tr>
            <tr style="background: #F3F4F6;">
                <td style="padding: 8px; font-weight: bold;">Pending Payment</td>
                <td style="padding: 8px; color: #DC2626; font-weight: bold;">{stats['pending']}</td>
            </tr>
            <tr>
                <td style="padding: 8px; font-weight: bold;">With Images</td>
                <td style="padding: 8px;">{stats['with_images']}</td>
            </tr>
            <tr style="background: #F3F4F6;">
                <td style="padding: 8px; font-weight: bold;">Using Coupons</td>
                <td style="padding: 8px;">{stats['with_coupons']}</td>
            </tr>
        </table>
        """
        
        return format_html(html)
    participant_stats_display.short_description = 'Statistics'
    
    # ==========================================================================
    # ADMIN ACTIONS
    # ==========================================================================
    
    def generate_coupons_action(self, request, queryset):
        """Generate coupon codes for selected orders"""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one order for coupon generation",
                level=messages.WARNING
            )
            return
        
        order = queryset.first()
        
        # Check if already has coupons
        existing_count = order.coupons.count()
        if existing_count > 0:
            self.message_user(
                request,
                f"Order already has {existing_count} coupons. Generate more?",
                level=messages.WARNING
            )
        
        count = 50  # Default count
        
        try:
            coupons = generate_clothing_coupon_codes(order, count=count)
            
            self.message_user(
                request,
                f"Successfully generated {len(coupons)} coupon codes for {order.reference}",
                level=messages.SUCCESS
            )
            
        except Exception as e:
            logger.error(f"Error generating coupons: {str(e)}")
            self.message_user(
                request,
                f"Error generating coupons: {str(e)}",
                level=messages.ERROR
            )
    
    generate_coupons_action.short_description = "🎟️ Generate 50 Coupon Codes"
    
    def download_pdf_action(self, request, queryset):
        """Generate PDF for selected order"""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one order for PDF generation",
                level=messages.WARNING
            )
            return
        
        order = queryset.first()
        
        try:
            pdf_buffer = generate_clothing_order_pdf(order)
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{order.reference}_details.pdf"'
            
            logger.info(f"Admin downloaded PDF for {order.reference}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            self.message_user(
                request,
                f"Error generating PDF: {str(e)}",
                level=messages.ERROR
            )
    
    download_pdf_action.short_description = "📄 Download PDF"
    
    def download_word_action(self, request, queryset):
        """Generate Word document for selected order"""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one order for Word generation",
                level=messages.WARNING
            )
            return
        
        order = queryset.first()
        
        try:
            word_buffer = generate_clothing_order_word(order)
            
            response = HttpResponse(
                word_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{order.reference}_details.docx"'
            
            logger.info(f"Admin downloaded Word for {order.reference}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating Word: {str(e)}")
            self.message_user(
                request,
                f"Error generating Word: {str(e)}",
                level=messages.ERROR
            )
    
    download_word_action.short_description = "📝 Download Word"
    
    def download_excel_action(self, request, queryset):
        """Generate Excel for selected order"""
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one order for Excel generation",
                level=messages.WARNING
            )
            return
        
        order = queryset.first()
        
        try:
            excel_buffer = generate_clothing_order_excel(order)
            
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{order.reference}_details.xlsx"'
            
            logger.info(f"Admin downloaded Excel for {order.reference}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating Excel: {str(e)}")
            self.message_user(
                request,
                f"Error generating Excel: {str(e)}",
                level=messages.ERROR
            )
    
    download_excel_action.short_description = "📊 Download Excel"
    
    def download_complete_package_action(self, request, queryset):
        """
        ⭐ KEY ACTION: Generate complete package with documents and organized images
        
        Creates a ZIP file containing:
        - order_details.pdf
        - order_details.docx
        - order_details.xlsx
        - images/
          - size_S/
          - size_M/
          - size_L/
          - etc.
        """
        if queryset.count() > 1:
            self.message_user(
                request,
                "Please select only one order for complete package generation",
                level=messages.WARNING
            )
            return
        
        order = queryset.first()
        
        try:
            self.message_user(
                request,
                f"Generating complete package for {order.reference}... This may take a moment.",
                level=messages.INFO
            )
            
            zip_buffer = generate_complete_package(order)
            
            org_name_safe = order.organization_name.replace(' ', '_')
            filename = f"{order.reference}_{org_name_safe}_complete_package.zip"
            
            response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            logger.info(f"Admin downloaded complete package for {order.reference}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating complete package: {str(e)}")
            self.message_user(
                request,
                f"Error generating complete package: {str(e)}",
                level=messages.ERROR
            )
    
    download_complete_package_action.short_description = "📦 Download Complete Package (PDF + Word + Excel + Images)"


@admin.register(ClothingOrderParticipant)
class ClothingOrderParticipantAdmin(admin.ModelAdmin):
    """Admin for clothing order participants"""
    
    list_display = [
        'reference', 'serial_number', 'full_name', 'order_reference',
        'size', 'custom_name', 'image_preview', 'paid_badge', 'created_at'
    ]
    
    list_filter = [
        'paid', 'size', 'order__reference', 'created_at'
    ]
    
    search_fields = [
        'reference', 'full_name', 'email', 'phone', 
        'order__reference', 'order__organization_name'
    ]
    
    readonly_fields = [
        'id', 'reference', 'serial_number', 'order', 
        'payment_reference', 'payment_date', 'coupon_used',
        'image_large_preview', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Participant Information', {
            'fields': ('reference', 'serial_number', 'order', 'email', 'full_name', 'phone')
        }),
        ('Order Details', {
            'fields': ('size', 'custom_name', 'image', 'image_large_preview')
        }),
        ('Payment', {
            'fields': ('paid', 'payment_reference', 'payment_date', 'coupon_used')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_reference(self, obj):
        """Show order reference with link"""
        url = reverse("admin:clothing_image_orders_clothingimageorder_change", args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.reference)
    order_reference.short_description = 'Order'
    
    def image_preview(self, obj):
        """Show small image preview"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 75px; border: 1px solid #ddd;" />',
                obj.image.url
            )
        return format_html('<span style="color: #999;">No image</span>')
    image_preview.short_description = 'Image'
    
    def image_large_preview(self, obj):
        """Show larger image preview in detail view"""
        if obj.image:
            return format_html(
                '<div><img src="{}" style="max-width: 400px; border: 2px solid #064E3B; border-radius: 8px;" /></div>'
                '<div style="margin-top: 10px; font-size: 12px; color: #666;">Expected filename: <strong>{}</strong></div>',
                obj.image.url,
                obj.get_image_filename()
            )
        return format_html('<span style="color: #999;">No image uploaded</span>')
    image_large_preview.short_description = 'Image Preview'
    
    def paid_badge(self, obj):
        """Show payment status badge"""
        if obj.coupon_used:
            return format_html(
                '<span style="background: #F59E0B; color: white; padding: 4px 10px; '
                'border-radius: 4px; font-size: 11px; font-weight: bold;">COUPON</span>'
            )
        elif obj.paid:
            return format_html(
                '<span style="background: #064E3B; color: white; padding: 4px 10px; '
                'border-radius: 4px; font-size: 11px; font-weight: bold;">PAID</span>'
            )
        else:
            return format_html(
                '<span style="background: #DC2626; color: white; padding: 4px 10px; '
                'border-radius: 4px; font-size: 11px; font-weight: bold;">PENDING</span>'
            )
    paid_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Participants should be added through API, not admin"""
        return False


@admin.register(ClothingCouponCode)
class ClothingCouponCodeAdmin(admin.ModelAdmin):
    """Admin for clothing coupon codes"""
    
    list_display = [
        'code', 'order_link', 'is_used_badge', 'created_at'
    ]
    
    list_filter = [
        'is_used', 'order__reference', 'created_at'
    ]
    
    search_fields = [
        'code', 'order__reference', 'order__organization_name'
    ]
    
    readonly_fields = [
        'id', 'order', 'code', 'is_used', 'created_at'
    ]
    
    def order_link(self, obj):
        """Link to order"""
        url = reverse("admin:clothing_image_orders_clothingimageorder_change", args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.reference)
    order_link.short_description = 'Order'
    
    def is_used_badge(self, obj):
        """Show usage status"""
        if obj.is_used:
            return format_html(
                '<span style="background: #DC2626; color: white; padding: 3px 8px; '
                'border-radius: 3px; font-size: 10px; font-weight: bold;">USED</span>'
            )
        return format_html(
            '<span style="background: #064E3B; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 10px; font-weight: bold;">AVAILABLE</span>'
        )
    is_used_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Coupons should be generated through actions, not added manually"""
        return False