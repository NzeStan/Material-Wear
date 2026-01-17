# order/admin.py
"""
UPDATED: Added generation tracking to admin interface
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem
from orderitem_generation.admin import (
    OrderItemGenerationAdminMixin,
    get_nysc_kit_pdf_context,
    get_nysc_tour_pdf_context,
    get_church_pdf_context
)


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items"""
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ['product_display', 'quantity', 'price', 'item_cost']
    fields = ['product_display', 'quantity', 'price', 'item_cost']

    def product_display(self, obj):
        """Display product with thumbnail or placeholder"""

        # Handle missing product
        if not obj.product:
            return format_html(
                '<span style="color: #9CA3AF; font-style: italic;">No Product</span>'
            )

        # Product exists with image
        image = getattr(obj.product, "image", None)
        if image:
            return format_html(
                '<div style="display: flex; align-items: center; gap: 10px;">'
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; '
                'border-radius: 4px; border: 2px solid #064E3B;" />'
                '<span style="font-weight: bold;">{}</span>'
                '</div>',
                image.url,
                obj.product.name
            )

        # Product exists but no image - show SVG placeholder
        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<div style="width: 50px; height: 50px; background: #F9FAFB; '
            'border-radius: 6px; border: 2px dashed #D1D5DB; '
            'display: flex; align-items: center; justify-content: center; '
            'flex-shrink: 0;">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
            'viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>'
            '<circle cx="8.5" cy="8.5" r="1.5"/>'
            '<path d="M21 15l-5-5L5 21"/>'
            '</svg>'
            '</div>'
            '<span style="font-weight: 600;">{}</span>'
            '</div>',
            obj.product.name
        )

    product_display.short_description = "Product"

    
    def has_add_permission(self, request, obj=None):
        return False
    
    def item_cost(self, obj):
        """Display total cost for this item"""
        cost = obj.get_cost()  # ✅ Use the model's get_cost() method
        return format_html(
            '<span style="color: #064E3B; font-weight: bold;">₦{}</span>',
            f"{cost:,.2f}"
        )
    item_cost.short_description = 'Total'


class BaseOrderAdmin(admin.ModelAdmin):
    """Base admin configuration for all order types"""
    list_display = [
        'serial_number', 'full_name_display', 'email', 
        'phone_number', 'order_total', 'paid_status', 
        'generation_status', 'created'  # ✅ NEW: Added generation_status
    ]
    list_filter = ['paid', 'items_generated', 'created']  # ✅ NEW: Added items_generated filter
    search_fields = ['serial_number', 'email', 'first_name', 'last_name', 'phone_number']
    readonly_fields = [
        'serial_number', 'user', 'created', 'updated',
        'order_total', 'items_count', 'generated_at', 'generated_by'  # ✅ NEW: Added generation fields
    ]
    date_hierarchy = 'created'
    inlines = [OrderItemInline]
    
    # ✅ NEW: Admin action to reset generation status
    actions = ['reset_generation_status']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('serial_number', 'user', 'paid', 'created', 'updated'),
            'classes': ('wide',),
        }),
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'email', 'phone_number'),
            'classes': ('wide',),
        }),
        ('Order Summary', {
            'fields': ('order_total', 'items_count'),
            'classes': ('wide',),
        }),
        # ✅ NEW: Generation tracking section
        ('Generation Tracking', {
            'fields': ('items_generated', 'generated_at', 'generated_by'),
            'classes': ('collapse',),  # Collapsed by default
        }),
    )
    
    def full_name_display(self, obj):
        """Display full name with styling"""
        full_name = f"{obj.first_name} {obj.middle_name} {obj.last_name}".strip()
        return format_html(
            '<span style="font-weight: bold; color: #064E3B;">{}</span>',
            full_name
        )
    full_name_display.short_description = 'Full Name'
    
    def paid_status(self, obj):
        """Display paid status with color coding"""
        if obj.paid:
            return format_html(
                '<span style="background-color: #D1FAE5; color: #065F46; padding: 4px 12px; '
                'border-radius: 12px; font-weight: bold; font-size: 11px;">PAID</span>'
            )
        return format_html(
            '<span style="background-color: #FEE2E2; color: #991B1B; padding: 4px 12px; '
            'border-radius: 12px; font-weight: bold; font-size: 11px;">UNPAID</span>'
        )
    paid_status.short_description = 'Payment Status'
    
    # ✅ NEW: Generation status display
    def generation_status(self, obj):
        """Display generation status with color coding"""
        if obj.items_generated:
            generated_date = obj.generated_at.strftime('%b %d, %Y') if obj.generated_at else 'Unknown'
            generated_by = obj.generated_by.username if obj.generated_by else 'Unknown'
            return format_html(
                '<span style="background-color: #DBEAFE; color: #1E40AF; padding: 4px 12px; '
                'border-radius: 12px; font-weight: bold; font-size: 11px;" '
                'title="Generated on {} by {}">GENERATED ✓</span>',
                generated_date,
                generated_by
            )
        return format_html(
            '<span style="background-color: #FEF3C7; color: #92400E; padding: 4px 12px; '
            'border-radius: 12px; font-weight: bold; font-size: 11px;">PENDING</span>'
        )
    generation_status.short_description = 'Generation Status'
    
    def order_total(self, obj):
        """Display total cost with currency formatting"""
        return format_html(
            '<span style="color: #064E3B; font-weight: bold;">₦{}</span>',
            f"{obj.total_cost:,.2f}"
        )
    order_total.short_description = 'Total Cost'
    
    def items_count(self, obj):
        """Display count of items in order"""
        count = obj.items.count()
        return format_html(
            '<span style="background-color: #F3F4F6; color: #374151; padding: 2px 8px; '
            'border-radius: 8px; font-weight: bold;">{} items</span>',
            count
        )
    items_count.short_description = 'Items'
    
    # ✅ NEW: Admin action to reset generation status
    @admin.action(description='Reset generation status (allow re-generation)')
    def reset_generation_status(self, request, queryset):
        """Reset generation status for selected orders"""
        updated = queryset.update(
            items_generated=False,
            generated_at=None,
            generated_by=None
        )
        self.message_user(
            request,
            f'Successfully reset generation status for {updated} order(s). '
            f'These orders can now be included in new PDF generations.'
        )


# ✅ UPDATED: NyscKitOrderAdmin with generation tracking
@admin.register(NyscKitOrder)
class NyscKitOrderAdmin(OrderItemGenerationAdminMixin, BaseOrderAdmin):
    """Admin for NYSC Kit orders"""
    list_display = BaseOrderAdmin.list_display + ['state', 'local_government']
    list_filter = BaseOrderAdmin.list_filter + ['state']  # ✅ FIXED: Use 'state' not 'pickup_on_camp'
    
    fieldsets = BaseOrderAdmin.fieldsets[:2] + (
        ('NYSC Kit Details', {
            'fields': ('call_up_number', 'state', 'local_government'),  # ✅ FIXED: Correct fields
            'classes': ('wide',),
        }),
    ) + BaseOrderAdmin.fieldsets[2:]
    
    def get_pdf_context(self, request):
        """Provide context for PDF generation"""
        return get_nysc_kit_pdf_context(self, request)


# ✅ UPDATED: NyscTourOrderAdmin with generation tracking
@admin.register(NyscTourOrder)
class NyscTourOrderAdmin(OrderItemGenerationAdminMixin, BaseOrderAdmin):
    """Admin for NYSC Tour orders"""
    
    def get_pdf_context(self, request):
        """Provide context for PDF generation"""
        return get_nysc_tour_pdf_context(self, request)


# ✅ UPDATED: ChurchOrderAdmin with generation tracking
@admin.register(ChurchOrder)
class ChurchOrderAdmin(OrderItemGenerationAdminMixin, BaseOrderAdmin):
    """Admin for Church orders"""
    list_display = BaseOrderAdmin.list_display + ['pickup_on_camp', 'delivery_location']
    list_filter = BaseOrderAdmin.list_filter + ['pickup_on_camp', 'delivery_state']
    
    fieldsets = BaseOrderAdmin.fieldsets[:2] + (
        ('Delivery Details', {
            'fields': ('pickup_on_camp', 'delivery_state', 'delivery_lga'),
            'classes': ('wide',),
        }),
    ) + BaseOrderAdmin.fieldsets[2:]
    
    def delivery_location(self, obj):
        """Display delivery location"""
        if obj.pickup_on_camp:
            return format_html(
                '<span style="color: #10B981; font-weight: bold;">Pickup on Camp</span>'
            )
        return f"{obj.delivery_state}, {obj.delivery_lga}"
    delivery_location.short_description = 'Delivery'
    
    def get_pdf_context(self, request):
        """Provide context for PDF generation"""
        return get_church_pdf_context(self, request)


# Unregister BaseOrder from admin (we only want specific order types)
try:
    admin.site.unregister(BaseOrder)
except admin.sites.NotRegistered:
    pass