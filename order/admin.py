# order/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from .models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem


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
    """Base admin for all order types"""
    list_display = [
        'order_badge', 'serial_number', 'customer_name', 'email', 
        'phone_number', 'item_count', 'total_cost_display', 'paid_status', 'created'
    ]
    list_filter = ['paid', 'created', 'updated']
    search_fields = ['serial_number', 'first_name', 'last_name', 'email', 'phone_number']
    readonly_fields = ['serial_number', 'user', 'created', 'updated', 'total_cost']
    date_hierarchy = 'created'
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('serial_number', 'user', 'paid'),
            'classes': ('wide',),
        }),
        ('Customer Details', {
            'fields': ('first_name', 'middle_name', 'last_name', 'email', 'phone_number'),
            'classes': ('wide',),
        }),
        ('Order Summary', {
            'fields': ('total_cost', 'created', 'updated'),
            'classes': ('wide',),
        }),
    )
    
    def order_badge(self, obj):
        """Display order type badge"""
        type_name = obj.__class__.__name__
        color_map = {
            'NyscKitOrder': '#064E3B',  # Dark Green
            'NyscTourOrder': '#F59E0B',  # Gold
            'ChurchOrder': '#1F2937',    # Dark Gray
        }
        color = color_map.get(type_name, '#6B7280')
        
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            type_name.replace('Order', '')
        )
    order_badge.short_description = 'Type'
    
    def customer_name(self, obj):
        """Display full customer name"""
        parts = [obj.first_name]
        if obj.middle_name:
            parts.append(obj.middle_name)
        parts.append(obj.last_name)
        return ' '.join(parts)
    customer_name.short_description = 'Customer'
    
    def item_count(self, obj):
        """Display number of items in order"""
        count = obj.items.count()
        return format_html(
            '<span style="background: #FFFBEB; color: #F59E0B; padding: 2px 8px; '
            'border-radius: 8px; font-weight: bold;">{}</span>',
            count
        )
    item_count.short_description = 'Items'
    
    def total_cost_display(self, obj):
        """Display total cost with formatting"""
        cost = float(obj.total_cost) if obj.total_cost else 0
        return format_html(
            '<span style="color: #064E3B; font-weight: bold; font-size: 14px;">₦{}</span>',
            f"{cost:,.2f}"
        )
    total_cost_display.short_description = 'Total'
    
    def paid_status(self, obj):
        """Display paid status with color coding"""
        if obj.paid:
            return format_html(
                '<span style="background: #10B981; color: white; padding: 4px 12px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">PAID</span>'
            )
        return format_html(
            '<span style="background: #EF4444; color: white; padding: 4px 12px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold;">PENDING</span>'
        )
    paid_status.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch"""
        return super().get_queryset(request).prefetch_related('items')


@admin.register(NyscKitOrder)
class NyscKitOrderAdmin(BaseOrderAdmin):
    """Admin for NYSC Kit orders"""
    list_display = BaseOrderAdmin.list_display + ['state', 'local_government']
    list_filter = BaseOrderAdmin.list_filter + ['state']
    
    fieldsets = BaseOrderAdmin.fieldsets[:2] + (
        ('NYSC Kit Details', {
            'fields': ('call_up_number', 'state', 'local_government'),
            'classes': ('wide',),
        }),
    ) + BaseOrderAdmin.fieldsets[2:]


@admin.register(NyscTourOrder)
class NyscTourOrderAdmin(BaseOrderAdmin):
    """Admin for NYSC Tour orders"""
    pass


@admin.register(ChurchOrder)
class ChurchOrderAdmin(BaseOrderAdmin):
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


# Unregister BaseOrder from admin (we only want specific order types)
try:
    admin.site.unregister(BaseOrder)
except admin.sites.NotRegistered:
    pass