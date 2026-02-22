# products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils.text import slugify
from django import forms
from .models import Category, NyscKit, NyscTour, Church
from .constants import NYSC_KIT_PRODUCT_NAME, STATES, CHURCH_PRODUCT_NAME


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_type', 'product_count']
    list_filter = ['product_type']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'description']
    
    def product_count(self, obj):
        """Display product count for this category"""
        model_map = {
            'nysc_kit': NyscKit,
            'nysc_tour': NyscTour,
            'church': Church,
        }
        model = model_map.get(obj.product_type)
        if model:
            count = model.objects.filter(category=obj).count()
            return format_html('<span style="color: #064E3B; font-weight: bold;">{}</span>', count)
        return 0
    product_count.short_description = 'Products'


class BaseProductAdmin(admin.ModelAdmin):
    """Base admin for all product types with thumbnails"""
    list_display = ['thumbnail_preview', 'id', 'name', 'category', 'price', 'available', 
                    'out_of_stock', 'created']
    list_filter = ['available', 'out_of_stock', 'created', 'updated', 'category']
    list_editable = ['price', 'available', 'out_of_stock']
    search_fields = ['name', 'description']
    date_hierarchy = 'created'
    readonly_fields = ['created', 'updated', 'large_thumbnail_preview']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description'),
            'classes': ('wide',),
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'available', 'out_of_stock'),
            'classes': ('wide',),
        }),
        ('Images', {
            'fields': ('large_thumbnail_preview', 'image', 'image_1', 'image_2', 'image_3'),
            'classes': ('wide',),
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make slug readonly after creation"""
        fields = list(self.readonly_fields)
        if obj:  # Editing existing object
            fields.append('slug')
        return fields
    
    def thumbnail_preview(self, obj):
        """Display thumbnail in list view"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; '
                'border-radius: 4px; border: 2px solid #064E3B;" />',
                obj.image.url
            )
        return format_html(
            '<div style="width: 50px; height: 50px; background: #F3F4F6; '
            'border-radius: 4px; display: flex; align-items: center; '
            'justify-content: center; color: #9CA3AF;">No Image</div>'
        )
    thumbnail_preview.short_description = 'Image'
    
    def large_thumbnail_preview(self, obj):
        """Display larger thumbnail in detail view"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; height: auto; '
                'border-radius: 8px; border: 3px solid #064E3B;" />',
                obj.image.url
            )
        return format_html(
            '<div style="width: 300px; height: 300px; background: #F3F4F6; '
            'border-radius: 8px; display: flex; align-items: center; '
            'justify-content: center; color: #9CA3AF; font-size: 18px;">No Image Available</div>'
        )
    large_thumbnail_preview.short_description = 'Current Image'


@admin.register(NyscKit)
class NyscKitAdmin(BaseProductAdmin):
    """Admin for NYSC Kit products"""
    list_display = BaseProductAdmin.list_display + ['type']
    list_filter = BaseProductAdmin.list_filter + ['type']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'type', 'category', 'description'),
            'classes': ('wide',),
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'available', 'out_of_stock'),
            'classes': ('wide',),
        }),
        ('Images', {
            'fields': ('large_thumbnail_preview', 'image', 'image_1', 'image_2', 'image_3'),
            'classes': ('wide',),
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',),
        }),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        """Use select widget for name choices"""
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'name':
            formfield.widget = forms.Select(choices=NYSC_KIT_PRODUCT_NAME)
        return formfield


@admin.register(NyscTour)
class NyscTourAdmin(BaseProductAdmin):
    """Admin for NYSC Tour products"""
    
    def formfield_for_dbfield(self, db_field, **kwargs):
        """Use select widget for name (states)"""
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'name':
            formfield.widget = forms.Select(choices=STATES)
        return formfield


@admin.register(Church)
class ChurchAdmin(BaseProductAdmin):
    """Admin for Church merchandise products"""
    list_display = BaseProductAdmin.list_display + ['church']
    list_filter = BaseProductAdmin.list_filter + ['church']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'church', 'category', 'description'),
            'classes': ('wide',),
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'available', 'out_of_stock'),
            'classes': ('wide',),
        }),
        ('Images', {
            'fields': ('large_thumbnail_preview', 'image', 'image_1', 'image_2', 'image_3'),
            'classes': ('wide',),
        }),
        ('Metadata', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',),
        }),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        """Use select widget for name choices"""
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'name':
            formfield.widget = forms.Select(choices=CHURCH_PRODUCT_NAME)
        return formfield


# Customize admin site header and title with brand colors
admin.site.site_header = "Material Wear Admin Panel"
admin.site.site_title = "Material Wear Admin"
admin.site.index_title = "Welcome to Material Wear Administration"