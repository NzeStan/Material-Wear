from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from .models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem

# ✅ ADD THIS IMPORT
from orderitem_generation.admin import (
    OrderItemGenerationAdminMixin,
    get_nysc_kit_pdf_context,
    get_nysc_tour_pdf_context,
    get_church_pdf_context
)


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items with product thumbnails"""
    model = OrderItem
    extra = 0
    readonly_fields = ['product_thumbnail', 'content_type', 'object_id', 'price', 'quantity', 'item_cost']
    fields = ['product_thumbnail', 'content_type', 'object_id', 'price', 'quantity', 'extra_fields', 'item_cost']
    can_delete = False
    
    def product_thumbnail(self, obj):
        """Display product image thumbnail"""
        if obj.product and hasattr(obj.product, 'image') and obj.product.image:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; '
                'border-radius: 4px; border: 2px solid #064E3B;" />',
                obj.product.image.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; background: #F3F4F6; '
            'border-radius: 4px; display: flex; align-items: center; '
            'justify-content: center; color: #9CA3AF; font-size: 10px;">No Img</div>'
        )
    product_thumbnail.short_description = 'Image'
    
    def item_cost(self, obj):
        """Display total cost for this item"""
        cost = float(obj.get_cost()) if obj.get_cost() else 0
        return format_html(
            '<span style="color: #064E3B; font-weight: bold;">₦{}</span>',
            f"{cost:,.2f}"
        )
    item_cost.short_description = 'Total'


class BaseOrderAdmin(admin.ModelAdmin):
    """Base admin configuration for all order types"""
    list_display = [
        'serial_number', 'full_name_display', 'email', 
        'phone', 'order_total', 'paid_status', 'created'
    ]
    list_filter = ['paid', 'created']
    search_fields = ['serial_number', 'email', 'first_name', 'last_name', 'phone']
    readonly_fields = [
        'serial_number', 'user', 'created', 'updated',
        'order_total', 'items_count'
    ]
    date_hierarchy = 'created'
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('serial_number', 'user', 'paid', 'created', 'updated'),
            'classes': ('wide',),
        }),
        ('Personal Information', {
            'fields': ('first_name', 'middle_name', 'last_name', 'email', 'phone'),
            'classes': ('wide',),
        }),
        ('Order Summary', {
            'fields': ('order_total', 'items_count'),
            'classes': ('wide',),
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
                '<span style="color: #10B981; font-weight: bold;">✓ Paid</span>'
            )
        return format_html(
            '<span style="color: #EF4444; font-weight: bold;">✗ Unpaid</span>'
        )
    paid_status.short_description = 'Status'
    
    def order_total(self, obj):
        """Display order total"""
        total = obj.get_total_cost()
        return format_html(
            '<span style="color: #F59E0B; font-weight: bold;">₦{}</span>',
            f"{total:,.2f}"
        )
    order_total.short_description = 'Total'
    
    def items_count(self, obj):
        """Display number of items"""
        count = obj.items.count()
        return format_html(
            '<span style="background: #064E3B; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-weight: bold;">{} items</span>',
            count
        )
    items_count.short_description = 'Items'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch"""
        return super().get_queryset(request).prefetch_related('items')


# ✅ UPDATED: Added OrderItemGenerationAdminMixin as first parent
@admin.register(NyscKitOrder)
class NyscKitOrderAdmin(OrderItemGenerationAdminMixin, BaseOrderAdmin):
    """Admin for NYSC Kit orders"""
    list_display = BaseOrderAdmin.list_display + ['state', 'local_government']
    list_filter = BaseOrderAdmin.list_filter + ['state']
    
    fieldsets = BaseOrderAdmin.fieldsets[:2] + (
        ('NYSC Kit Details', {
            'fields': ('call_up_number', 'state', 'local_government'),
            'classes': ('wide',),
        }),
    ) + BaseOrderAdmin.fieldsets[2:]
    
    # ✅ ADDED: PDF generation context method
    def get_pdf_context(self, request):
        """Provide context for PDF generation"""
        return get_nysc_kit_pdf_context(self, request)


# ✅ UPDATED: Added OrderItemGenerationAdminMixin as first parent
@admin.register(NyscTourOrder)
class NyscTourOrderAdmin(OrderItemGenerationAdminMixin, BaseOrderAdmin):
    """Admin for NYSC Tour orders"""
    
    # ✅ ADDED: PDF generation context method
    def get_pdf_context(self, request):
        """Provide context for PDF generation"""
        return get_nysc_tour_pdf_context(self, request)


# ✅ UPDATED: Added OrderItemGenerationAdminMixin as first parent
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
    
    # ✅ ADDED: PDF generation context method
    def get_pdf_context(self, request):
        """Provide context for PDF generation"""
        return get_church_pdf_context(self, request)


# Unregister BaseOrder from admin (we only want specific order types)
try:
    admin.site.unregister(BaseOrder)
except admin.sites.NotRegistered:
    pass
