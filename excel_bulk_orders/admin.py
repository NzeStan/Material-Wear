# excel_bulk_orders/admin.py
"""
Django Admin for Excel Bulk Orders.

Features:
- List/filter bulk orders
- View participants
- Generate documents (PDF, Word, Excel)
- Download templates and uploaded files
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
import logging

from .models import ExcelBulkOrder, ExcelParticipant, ExcelCouponCode
from .utils import (
    generate_participants_pdf,
    generate_participants_word,
    generate_participants_excel,
    generate_excel_coupon_codes,
)

logger = logging.getLogger(__name__)


class ExcelCouponCodeInline(admin.TabularInline):
    """Inline display of coupon codes"""
    model = ExcelCouponCode
    extra = 0
    readonly_fields = ['code', 'is_used', 'created_at']
    fields = ['code', 'is_used', 'created_at']
    can_delete = False
    max_num = 0
    show_change_link = True
    
    def has_add_permission(self, request, obj=None):
        return False


class ExcelParticipantInline(admin.TabularInline):
    model = ExcelParticipant
    extra = 0
    readonly_fields = ['full_name', 'size', 'custom_name', 'coupon_code', 'is_coupon_applied', 'row_number', 'created_at']
    fields = ['row_number', 'full_name', 'size', 'custom_name', 'coupon_code', 'is_coupon_applied']
    can_delete = False
    max_num = 0
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ExcelBulkOrder)
class ExcelBulkOrderAdmin(admin.ModelAdmin):
    list_display = [
        'reference',
        'title',
        'coordinator_name',
        'coordinator_email',
        'price_per_participant',
        'participant_count',
        'couponed_count',
        'total_amount',
        'validation_status_display',
        'payment_status_badge',
        'created_at',
    ]
    
    list_filter = [
        'validation_status',
        'payment_status',
        'requires_custom_name',
        'created_at',
    ]
    
    search_fields = [
        'reference',
        'title',
        'coordinator_name',
        'coordinator_email',
        'coordinator_phone',
    ]
    
    readonly_fields = [
        'id',
        'reference',
        'template_file_link',
        'uploaded_file_link',
        'validation_errors_display',
        'payment_breakdown',
        'created_by',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Campaign Details', {
            'fields': (
                'id',
                'reference',
                'title',
                'price_per_participant',
                'requires_custom_name',
            )
        }),
        ('Coordinator Information', {
            'fields': (
                'coordinator_name',
                'coordinator_email',
                'coordinator_phone',
            )
        }),
        ('Files', {
            'fields': (
                'template_file_link',
                'uploaded_file_link',
            )
        }),
        ('Validation', {
            'fields': (
                'validation_status',
                'validation_errors_display',
            )
        }),
        ('Payment', {
            'fields': (
                'total_amount',
                'payment_status',
                'paystack_reference',
                'payment_breakdown',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ExcelCouponCodeInline, ExcelParticipantInline]
    
    actions = [
        'generate_coupons_action',
        'download_pdf_action',
        'download_word_action',
        'download_excel_action',
    ]
    
    def participant_count(self, obj):
        """Total participants"""
        return obj.participants.count()
    participant_count.short_description = 'Participants'
    
    def couponed_count(self, obj):
        """Participants with coupons"""
        count = obj.participants.filter(is_coupon_applied=True).count()
        if count > 0:
            return format_html('<span style="color: green;">✓ {}</span>', count)
        return count
    couponed_count.short_description = 'Couponed'
    
    def validation_status_display(self, obj):
        """Colored validation status"""
        colors = {
            'pending': '#6B7280',
            'uploaded': '#3B82F6',
            'valid': '#10B981',
            'invalid': '#EF4444',
            'processing': '#F59E0B',
            'completed': '#059669',
        }
        color = colors.get(obj.validation_status, '#6B7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_validation_status_display()
        )
    validation_status_display.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        """Payment status badge"""
        if obj.payment_status:
            return format_html(
                '<span style="background: #10B981; color: white; padding: 3px 8px; '
                'border-radius: 4px; font-size: 11px;">PAID</span>'
            )
        return format_html(
            '<span style="background: #EF4444; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px;">UNPAID</span>'
        )
    payment_status_badge.short_description = 'Payment'
    
    def template_file_link(self, obj):
        """Template file download link"""
        if obj.template_file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3B82F6;">📥 Download Template</a>',
                obj.template_file
            )
        return "Not generated"
    template_file_link.short_description = 'Template File'
    
    def uploaded_file_link(self, obj):
        """Uploaded file download link"""
        if obj.uploaded_file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3B82F6;">📥 Download Uploaded File</a>',
                obj.uploaded_file
            )
        return "Not uploaded"
    uploaded_file_link.short_description = 'Uploaded File'
    
    def validation_errors_display(self, obj):
        """Display validation errors in readable format"""
        if not obj.validation_errors:
            return format_html('<span style="color: #10B981;">No errors</span>')
        
        summary = obj.get_validation_summary()
        if not summary:
            return "No validation data"
        
        html = f'<div style="max-height: 300px; overflow-y: auto; border: 1px solid #E5E7EB; padding: 10px; border-radius: 4px;">'
        html += f'<p><strong>Summary:</strong> {summary["error_rows"]} errors in {summary["total_rows"]} rows</p>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        html += '<tr style="background: #F3F4F6;"><th>Row</th><th>Field</th><th>Error</th><th>Value</th></tr>'
        
        for error in summary['errors'][:10]:  # Show first 10 errors
            html += f'<tr style="border-bottom: 1px solid #E5E7EB;">'
            html += f'<td>{error["row"]}</td>'
            html += f'<td><strong>{error["field"]}</strong></td>'
            html += f'<td>{error["error"]}</td>'
            html += f'<td><code>{error.get("current_value", "")}</code></td>'
            html += '</tr>'
        
        if len(summary['errors']) > 10:
            html += f'<tr><td colspan="4" style="text-align: center; padding: 10px; color: #6B7280;">... and {len(summary["errors"]) - 10} more errors</td></tr>'
        
        html += '</table></div>'
        return format_html(html)
    validation_errors_display.short_description = 'Validation Errors'
    
    def payment_breakdown(self, obj):
        """Show payment breakdown"""
        total = obj.participants.count()
        couponed = obj.participants.filter(is_coupon_applied=True).count()
        chargeable = total - couponed
        
        html = '<table style="width: 100%; border-collapse: collapse;">'
        html += f'<tr><td>Total Participants:</td><td><strong>{total}</strong></td></tr>'
        html += f'<tr><td>With Valid Coupons:</td><td><strong style="color: #10B981;">{couponed}</strong></td></tr>'
        html += f'<tr><td>Chargeable:</td><td><strong>{chargeable}</strong></td></tr>'
        html += f'<tr><td>Price per Participant:</td><td>₦{obj.price_per_participant:,.2f}</td></tr>'
        html += f'<tr style="border-top: 2px solid #1F2937;"><td><strong>Total Amount:</strong></td><td><strong style="color: #064E3B;">₦{obj.total_amount:,.2f}</strong></td></tr>'
        html += '</table>'
        
        return format_html(html)
    payment_breakdown.short_description = 'Payment Breakdown'
    
    # Admin Actions
    def generate_coupons_action(self, request, queryset):
        """Generate coupon codes for selected bulk orders"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one bulk order.", level='error')
            return
        
        bulk_order = queryset.first()
        
        # Check if already has coupons
        existing_count = bulk_order.coupons.count()
        if existing_count > 0:
            self.message_user(
                request,
                f"This bulk order already has {existing_count} coupons. Generate more?",
                level='warning'
            )
        
        # Default count
        count = 50
        
        # TODO: In production, add a form to let admin choose the count
        # For now, generate 50 coupons by default
        
        try:
            coupons = generate_excel_coupon_codes(bulk_order, count=count)
            
            self.message_user(
                request,
                f"Successfully generated {len(coupons)} coupon codes for {bulk_order.reference}.",
                level='success'
            )
            
            logger.info(f"Admin generated {len(coupons)} coupons for {bulk_order.reference}")
            
        except Exception as e:
            logger.error(f"Error generating coupons: {str(e)}")
            self.message_user(request, f"Error generating coupons: {str(e)}", level='error')
    
    generate_coupons_action.short_description = "Generate 50 coupon codes for selected bulk order"
    
    def download_pdf_action(self, request, queryset):
        """Generate PDF for selected bulk orders"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one bulk order.", level='error')
            return
        
        bulk_order = queryset.first()
        
        if not bulk_order.payment_status:
            self.message_user(request, "PDF can only be generated after payment.", level='error')
            return
        
        try:
            pdf_buffer = generate_participants_pdf(bulk_order)
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{bulk_order.reference}_participants.pdf"'
            
            logger.info(f"Admin downloaded PDF for {bulk_order.reference}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            self.message_user(request, f"Error generating PDF: {str(e)}", level='error')
    
    download_pdf_action.short_description = "Download PDF (Paid orders only)"
    
    def download_word_action(self, request, queryset):
        """Generate Word document for selected bulk orders"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one bulk order.", level='error')
            return
        
        bulk_order = queryset.first()
        
        if not bulk_order.payment_status:
            self.message_user(request, "Word document can only be generated after payment.", level='error')
            return
        
        try:
            word_buffer = generate_participants_word(bulk_order)
            
            response = HttpResponse(
                word_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            response['Content-Disposition'] = f'attachment; filename="{bulk_order.reference}_participants.docx"'
            
            logger.info(f"Admin downloaded Word for {bulk_order.reference}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating Word: {str(e)}")
            self.message_user(request, f"Error generating Word: {str(e)}", level='error')
    
    download_word_action.short_description = "Download Word (Paid orders only)"
    
    def download_excel_action(self, request, queryset):
        """Generate Excel for selected bulk orders"""
        if queryset.count() != 1:
            self.message_user(request, "Please select exactly one bulk order.", level='error')
            return
        
        bulk_order = queryset.first()
        
        if not bulk_order.payment_status:
            self.message_user(request, "Excel can only be generated after payment.", level='error')
            return
        
        try:
            excel_buffer = generate_participants_excel(bulk_order)
            
            response = HttpResponse(
                excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{bulk_order.reference}_participants.xlsx"'
            
            logger.info(f"Admin downloaded Excel for {bulk_order.reference}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating Excel: {str(e)}")
            self.message_user(request, f"Error generating Excel: {str(e)}", level='error')
    
    download_excel_action.short_description = "Download Excel (Paid orders only)"


@admin.register(ExcelCouponCode)
class ExcelCouponCodeAdmin(admin.ModelAdmin):
    """Admin for Excel coupon codes"""
    
    list_display = [
        'code',
        'bulk_order_link',
        'is_used_badge',
        'created_at',
    ]
    
    list_filter = [
        'is_used',
        'created_at',
    ]
    
    search_fields = [
        'code',
        'bulk_order__reference',
        'bulk_order__title',
    ]
    
    readonly_fields = [
        'id',
        'bulk_order',
        'code',
        'is_used',
        'created_at',
    ]
    
    def bulk_order_link(self, obj):
        """Link to bulk order"""
        url = reverse('admin:excel_bulk_orders_excelbulkorder_change', args=[obj.bulk_order.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.bulk_order.reference
        )
    bulk_order_link.short_description = 'Bulk Order'
    
    def is_used_badge(self, obj):
        """Display usage status"""
        if obj.is_used:
            return format_html(
                '<span style="background: #EF4444; color: white; padding: 3px 8px; '
                'border-radius: 4px; font-size: 11px;">USED</span>'
            )
        return format_html(
            '<span style="background: #10B981; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px;">AVAILABLE</span>'
        )
    is_used_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Coupons can only be generated via bulk order admin"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of coupons"""
        return False


@admin.register(ExcelParticipant)
class ExcelParticipantAdmin(admin.ModelAdmin):
    list_display = [
        'row_number',
        'full_name',
        'size',
        'custom_name',
        'bulk_order_link',
        'coupon_status',
        'created_at',
    ]
    
    list_filter = [
        'size',
        'is_coupon_applied',
        'created_at',
    ]
    
    search_fields = [
        'full_name',
        'custom_name',
        'bulk_order__reference',
        'bulk_order__title',
    ]
    
    readonly_fields = [
        'id',
        'bulk_order',
        'full_name',
        'size',
        'custom_name',
        'coupon_code',
        'coupon',
        'is_coupon_applied',
        'row_number',
        'created_at',
    ]
    
    def bulk_order_link(self, obj):
        """Link to bulk order"""
        url = reverse('admin:excel_bulk_orders_excelbulkorder_change', args=[obj.bulk_order.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.bulk_order.reference
        )
    bulk_order_link.short_description = 'Bulk Order'
    
    def coupon_status(self, obj):
        """Coupon status display"""
        if obj.is_coupon_applied:
            return format_html(
                '<span style="color: #10B981; font-weight: bold;">✓ {}</span>',
                obj.coupon_code
            )
        elif obj.coupon_code:
            return format_html(
                '<span style="color: #EF4444;">✗ {}</span>',
                obj.coupon_code
            )
        return "-"
    coupon_status.short_description = 'Coupon'
    
    def has_add_permission(self, request):
        """Participants can only be created through Excel upload"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of participants"""
        return False