# image_bulk_orders/serializers.py
"""
Serializers for Image Bulk Orders app.

EXACT CLONE of bulk_orders serializers with image field handling added.
"""
from rest_framework import serializers
from .models import ImageBulkOrderLink, ImageCouponCode, ImageOrderEntry
from typing import Any, Optional
import magic
import logging

logger = logging.getLogger(__name__)


class ImageCouponCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for coupon codes.
    IDENTICAL to CouponCodeSerializer from bulk_orders.
    """
    
    bulk_order_name = serializers.CharField(source='bulk_order.organization_name', read_only=True)
    bulk_order_slug = serializers.CharField(source='bulk_order.slug', read_only=True)
    
    class Meta:
        model = ImageCouponCode
        fields = ['id', 'bulk_order', 'bulk_order_name', 'bulk_order_slug', 'code', 'is_used', 'created_at']
        read_only_fields = ('id', 'is_used', 'created_at')


class ImageBulkOrderLinkSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer for bulk order links.
    IDENTICAL to BulkOrderLinkSummarySerializer from bulk_orders.
    """
    
    is_expired = serializers.SerializerMethodField()
    shareable_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageBulkOrderLink
        fields = [
            'id',
            'slug',
            'organization_name',
            'price_per_item',
            'custom_branding_enabled',
            'payment_deadline',
            'is_expired',
            'shareable_url',
        ]

    def get_is_expired(self, obj: 'ImageBulkOrderLink') -> bool:
        """Check if bulk order link has expired"""
        return obj.is_expired()
    
    def get_shareable_url(self, obj: 'ImageBulkOrderLink') -> str:
        """Get shareable URL for bulk order"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/image-bulk-order/{obj.slug}/')
        return f'/image-bulk-order/{obj.slug}/'


class ImageOrderEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for order entries.
    IDENTICAL to OrderEntrySerializer from bulk_orders BUT with optional image field.
    """
    
    bulk_order = ImageBulkOrderLinkSummarySerializer(read_only=True)
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    custom_name = serializers.CharField(required=False, allow_blank=True)
    
    # ✅ NEW: Image field (optional, write-only for upload)
    image = serializers.ImageField(required=False, allow_null=True, write_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ImageOrderEntry
        fields = [
            'id', 'reference', 'bulk_order', 'serial_number', 'email', 'full_name', 'size',
            'custom_name', 'image', 'image_url', 'coupon_used', 'paid', 'created_at', 'updated_at', 'coupon_code'
        ]
        read_only_fields = (
            'id', 'reference', 'bulk_order', 'serial_number',
            'coupon_used', 'paid', 'created_at', 'updated_at', 'image_url'
        )

    def get_image_url(self, obj: 'ImageOrderEntry') -> Optional[str]:
        """Get Cloudinary URL for uploaded image"""
        if obj.image:
            return obj.image.url
        return None

    def to_representation(self, instance):
        """Conditionally include custom_name based on bulk_order settings"""
        representation = super().to_representation(instance)
        
        # Only include custom_name if custom branding is enabled
        if not instance.bulk_order.custom_branding_enabled:
            representation.pop('custom_name', None)
        
        return representation

    def validate_image(self, value):
        """
        Validate uploaded image using python-magic for proper MIME type checking.
        
        Allowed formats: JPEG, PNG, GIF, WebP
        Max size: 10MB
        """
        if value is None:
            return value
        
        # Check file size (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Image file size ({value.size / 1024 / 1024:.2f}MB) exceeds maximum allowed size (10MB)"
            )
        
        # Use python-magic for robust MIME type checking
        try:
            mime = magic.from_buffer(value.read(1024), mime=True)
            value.seek(0)  # Reset file pointer
            
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if mime not in allowed_types:
                raise serializers.ValidationError(
                    f"Invalid image type '{mime}'. Allowed types: JPEG, PNG, GIF, WebP"
                )
            
            logger.info(f"Image validated successfully: {mime}, size: {value.size / 1024:.2f}KB")
            return value
            
        except Exception as e:
            logger.error(f"Error validating image: {str(e)}")
            raise serializers.ValidationError(f"Error validating image: {str(e)}")

    def validate(self, attrs):
        """Validate coupon code and payment deadline"""
        # Get bulk_order from context (passed from ViewSet)
        bulk_order = self.context.get('bulk_order')
        
        if not bulk_order:
            raise serializers.ValidationError({"bulk_order": "Bulk order context is required."})
        
        # Check if deadline has passed
        if bulk_order.is_expired():
            raise serializers.ValidationError(
                {"payment_deadline": "This bulk order has expired and is no longer accepting submissions."}
            )
        
        # Validate coupon code if provided
        coupon_code = attrs.get('coupon_code', '').strip()
        if coupon_code:
            try:
                coupon = ImageCouponCode.objects.get(
                    bulk_order=bulk_order,
                    code=coupon_code.upper()
                )
                if coupon.is_used:
                    raise serializers.ValidationError(
                        {"coupon_code": "This coupon code has already been used."}
                    )
                # Store coupon object for save method
                attrs['coupon_obj'] = coupon
            except ImageCouponCode.DoesNotExist:
                raise serializers.ValidationError(
                    {"coupon_code": "Invalid coupon code for this bulk order."}
                )
        
        # Validate custom_name only if custom branding is enabled
        custom_name = attrs.get('custom_name', '').strip()
        if custom_name and not bulk_order.custom_branding_enabled:
            raise serializers.ValidationError(
                {"custom_name": "Custom branding is not enabled for this bulk order."}
            )
        
        return attrs

    def create(self, validated_data):
        """Create order entry with proper coupon handling and Cloudinary image upload"""
        bulk_order = self.context.get('bulk_order')
        coupon_obj = validated_data.pop('coupon_obj', None)
        validated_data.pop('coupon_code', None)  # Remove the code string
        
        # Extract image before creating (Cloudinary will handle upload)
        image = validated_data.pop('image', None)
        
        # Create order entry
        order_entry = ImageOrderEntry.objects.create(
            bulk_order=bulk_order,
            coupon_used=coupon_obj,
            **validated_data
        )
        
        # Upload image to Cloudinary if provided (organized by slug and size)
        if image:
            folder_path = f"image_bulk_orders/{bulk_order.slug}/{order_entry.size}"
            
            # Determine filename
            if order_entry.custom_name:
                filename = order_entry.custom_name.replace(' ', '_')
            else:
                filename = f"{order_entry.serial_number}_{order_entry.full_name.replace(' ', '_')}"
            
            order_entry.image = image
            order_entry.image.folder = folder_path
            order_entry.image.public_id = filename
            order_entry.save(update_fields=['image'])
            
            logger.info(f"Image uploaded to Cloudinary: {folder_path}/{filename}")
        
        # Mark coupon as used if provided
        if coupon_obj:
            coupon_obj.is_used = True
            coupon_obj.save(update_fields=['is_used'])
            logger.info(f"Coupon marked as used: {coupon_obj.code}")
        
        return order_entry


class ImageBulkOrderLinkSerializer(serializers.ModelSerializer):
    """
    Full serializer for bulk order links.
    IDENTICAL to BulkOrderLinkSerializer from bulk_orders.
    """
    
    created_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    is_expired = serializers.SerializerMethodField()
    shareable_url = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    coupon_count = serializers.SerializerMethodField()

    class Meta:
        model = ImageBulkOrderLink
        fields = [
            'id', 'slug', 'organization_name', 'price_per_item',
            'custom_branding_enabled', 'payment_deadline', 'created_by',
            'created_at', 'updated_at', 'is_expired', 'shareable_url',
            'total_orders', 'total_paid', 'coupon_count'
        ]
        read_only_fields = ('id', 'slug', 'created_at', 'updated_at')

    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_shareable_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/image-bulk-order/{obj.slug}/')
        return f'/image-bulk-order/{obj.slug}/'
    
    def get_total_orders(self, obj):
        return obj.orders.count()
    
    def get_total_paid(self, obj):
        return obj.orders.filter(paid=True).count()
    
    def get_coupon_count(self, obj):
        return obj.coupons.count()
