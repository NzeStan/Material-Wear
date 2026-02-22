from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ReferrerProfile, PromotionalMedia


@admin.register(ReferrerProfile)
class ReferrerProfileAdmin(admin.ModelAdmin):
    """Custom admin for ReferrerProfile with brand styling"""
    
    list_display = [
        "id",
        'colored_full_name',
        'referral_code_display',
        'user_email',
        'phone_number',
        'bank_name',
        'account_number',
        'status_badge',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'created_at',
        'bank_name',
    ]
    
    search_fields = [
        'full_name',
        'referral_code',
        'user__email',
        'phone_number',
        'account_number',
    ]
    
    readonly_fields = [
        'referral_code',
        'user',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'referral_code', 'full_name', 'phone_number')
        }),
        ('Banking Information', {
            'fields': ('bank_name', 'account_number')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def colored_full_name(self, obj):
        """Display full name with brand color"""
        return format_html(
            '<span style="color: #064E3B; font-weight: bold;">{}</span>',
            obj.full_name
        )
    colored_full_name.short_description = 'Full Name'
    
    def referral_code_display(self, obj):
        """Display referral code in a badge"""
        return format_html(
            '<span style="background-color: #F59E0B; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-weight: bold; font-family: monospace;">{}</span>',
            obj.referral_code
        )
    referral_code_display.short_description = 'Referral Code'
    
    def user_email(self, obj):
        """Display user email"""
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        if obj.is_active:
            color = '#064E3B'  # Dark Green
            text = 'ACTIVE'
        else:
            color = '#EF4444'  # Red
            text = 'INACTIVE'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color, text
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'is_active'
    
    def has_add_permission(self, request):
        """Users create their own profiles via API"""
        return False
    


@admin.register(PromotionalMedia)
class PromotionalMediaAdmin(admin.ModelAdmin):
    """Custom admin for PromotionalMedia with brand styling and media preview"""
    
    list_display = [
        "id",
        'media_thumbnail',
        'colored_title',
        'media_type_badge',
        'status_badge',
        'order',
        'created_by_display',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'media_type',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'marketing_text',
    ]
    
    readonly_fields = [
        'created_by',
        'created_at',
        'updated_at',
        'media_preview',
    ]
    
    fieldsets = (
        ('Media Information', {
            'fields': ('title', 'media_type', 'media_file', 'media_preview')
        }),
        ('Content', {
            'fields': ('marketing_text',)
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user if not set"""
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def colored_title(self, obj):
        """Display title with brand color"""
        return format_html(
            '<span style="color: #064E3B; font-weight: bold;">{}</span>',
            obj.title
        )
    colored_title.short_description = 'Title'
    
    def media_type_badge(self, obj):
        """Display media type with colored badge"""
        colors = {
            'flyer': '#F59E0B',  # Gold
            'video': '#8B5CF6',  # Purple
        }
        color = colors.get(obj.media_type, '#6B7280')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.get_media_type_display().upper()
        )
    media_type_badge.short_description = 'Media Type'
    media_type_badge.admin_order_field = 'media_type'
    
    def status_badge(self, obj):
        """Display status with colored badge"""
        if obj.is_active:
            color = '#064E3B'  # Dark Green
            text = 'ACTIVE'
        else:
            color = '#EF4444'  # Red
            text = 'INACTIVE'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; '
            'border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color, text
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'is_active'
    
    def created_by_display(self, obj):
        """Display creator name"""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return '-'
    created_by_display.short_description = 'Created By'
    created_by_display.admin_order_field = 'created_by'
    
    def media_thumbnail(self, obj):
        """Display media thumbnail in list view"""
        if obj.media_file:
            if obj.media_type == 'flyer':
                return format_html(
                    '<img src="{}" style="width: 60px; height: 60px; object-fit: cover; '
                    'border-radius: 4px; border: 2px solid #064E3B;" />',
                    obj.media_file.url
                )
            elif obj.media_type == 'video':
                return format_html(
                    '<div style="width: 60px; height: 60px; background-color: #064E3B; '
                    'border-radius: 4px; display: flex; align-items: center; justify-content: center;">'
                    '<span style="color: white; font-size: 24px;">▶</span>'
                    '</div>'
                )
        return '-'
    media_thumbnail.short_description = 'Preview'
    
    def media_preview(self, obj):
        """Display full media preview in detail view"""
        if obj.media_file:
            if obj.media_type == 'flyer':
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<img src="{}" style="max-width: 400px; max-height: 400px; '
                    'border-radius: 8px; border: 3px solid #064E3B;" />'
                    '<p style="margin-top: 10px;"><a href="{}" target="_blank" '
                    'style="color: #F59E0B; font-weight: bold;">View Full Size</a></p>'
                    '</div>',
                    obj.media_file.url,
                    obj.media_file.url
                )
            elif obj.media_type == 'video':
                return format_html(
                    '<div style="margin: 10px 0;">'
                    '<video controls style="max-width: 400px; border-radius: 8px; '
                    'border: 3px solid #064E3B;">'
                    '<source src="{}" type="video/mp4">'
                    'Your browser does not support the video tag.'
                    '</video>'
                    '<p style="margin-top: 10px;"><a href="{}" target="_blank" '
                    'style="color: #F59E0B; font-weight: bold;">View Full Size</a></p>'
                    '</div>',
                    obj.media_file.url,
                    obj.media_file.url
                )
        return 'No media uploaded'
    media_preview.short_description = 'Media Preview'
    

# Custom admin site styling
admin.site.site_header = "Material Wear Admin Panel"
admin.site.site_title = "Material Wear Admin"
admin.site.index_title = "Welcome to Material Wear Administration"