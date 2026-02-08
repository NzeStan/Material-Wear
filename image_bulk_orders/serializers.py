# image_bulk_orders/serializers.py
"""
Serializers for image bulk orders with comprehensive validation.

Security Features:
- Image file size validation
- Image format validation
- Image dimension validation
- MIME type checking
- Malicious file detection

Optimizations:
- Efficient Cloudinary uploads with transformations
- Minimal database queries
- Proper error handling
"""
from rest_framework import serializers
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import cloudinary.uploader
import magic  # python-magic for MIME type checking
from PIL import Image as PILImage
from io import BytesIO
import logging
from django.db import transaction

from .models import ImageBulkOrderLink, ImageOrderEntry, ImageCouponCode

logger = logging.getLogger(__name__)


class ImageCouponCodeSerializer(serializers.ModelSerializer):
    """Serializer for coupon codes"""
    bulk_order_name = serializers.CharField(source='bulk_order.organization_name', read_only=True)
    bulk_order_slug = serializers.CharField(source='bulk_order.slug', read_only=True)
    
    class Meta:
        model = ImageCouponCode
        fields = [
            'id', 'bulk_order', 'bulk_order_name', 'bulk_order_slug',
            'code', 'is_used', 'created_at'
        ]
        read_only_fields = ('id', 'is_used', 'created_at')


class ImageBulkOrderLinkSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for nested representations"""
    is_expired = serializers.SerializerMethodField()
    shareable_url = serializers.SerializerMethodField()
    paid_count = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageBulkOrderLink
        fields = [
            'id', 'slug', 'organization_name', 'price_per_item',
            'custom_branding_enabled', 'payment_deadline', 'image_required',
            'max_image_size_mb', 'allowed_image_formats', 'is_expired',
            'shareable_url', 'paid_count', 'total_orders'
        ]
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_shareable_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.get_shareable_url())
        return obj.get_shareable_url()
    
    def get_paid_count(self, obj):
        # Optimized: Use prefetch_related or cached value
        if hasattr(obj, '_paid_count'):
            return obj._paid_count
        return obj.get_paid_count()
    
    def get_total_orders(self, obj):
        # Optimized: Use prefetch_related or cached value
        if hasattr(obj, '_total_orders'):
            return obj._total_orders
        return obj.orders.count()


class ImageBulkOrderLinkSerializer(serializers.ModelSerializer):
    """Full serializer for bulk order links"""
    is_expired = serializers.SerializerMethodField()
    shareable_url = serializers.SerializerMethodField()
    paid_count = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageBulkOrderLink
        fields = [
            'id', 'slug', 'organization_name', 'price_per_item',
            'custom_branding_enabled', 'payment_deadline', 'image_required',
            'max_image_size_mb', 'allowed_image_formats', 'last_generated_at',
            'generation_status', 'generated_zip_url', 'created_by',
            'created_at', 'updated_at', 'is_expired', 'shareable_url',
            'paid_count', 'total_orders', 'total_revenue'
        ]
        read_only_fields = (
            'id', 'slug', 'created_by', 'last_generated_at', 'generation_status',
            'generated_zip_url', 'created_at', 'updated_at'
        )
    
    def get_is_expired(self, obj):
        return obj.is_expired()
    
    def get_shareable_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.get_shareable_url())
        return obj.get_shareable_url()
    
    def get_paid_count(self, obj):
        if hasattr(obj, '_paid_count'):
            return obj._paid_count
        return obj.get_paid_count()
    
    def get_total_orders(self, obj):
        if hasattr(obj, '_total_orders'):
            return obj._total_orders
        return obj.orders.count()
    
    def get_total_revenue(self, obj):
        return float(obj.get_total_revenue())
    
    def create(self, validated_data):
        """Set created_by from request user"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class ImageOrderEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for image order entries with comprehensive validation.
    
    Security:
    - File size validation
    - MIME type validation
    - Image format validation
    - Dimension validation
    - Malicious file detection
    """
    bulk_order = ImageBulkOrderLinkSummarySerializer(read_only=True)
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    custom_name = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(write_only=True, required=True)
    
    # Read-only image metadata
    image_width = serializers.IntegerField(read_only=True)
    image_height = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = ImageOrderEntry
        fields = [
            'id', 'reference', 'bulk_order', 'serial_number', 'email', 'full_name',
            'size', 'custom_name', 'image', 'uploaded_image', 'cloudinary_public_id',
            'image_uploaded_at', 'image_width', 'image_height', 'coupon_used',
            'paid', 'created_at', 'updated_at', 'coupon_code'
        ]
        read_only_fields = (
            'id', 'reference', 'serial_number', 'uploaded_image',
            'cloudinary_public_id', 'image_uploaded_at', 'image_width',
            'image_height', 'coupon_used', 'paid', 'created_at', 'updated_at'
        )
    
    def to_representation(self, instance):
        """Conditionally include custom_name based on bulk_order settings"""
        representation = super().to_representation(instance)
        
        # Only include custom_name if custom branding is enabled
        if not instance.bulk_order.custom_branding_enabled:
            representation.pop('custom_name', None)
        
        return representation
    
    def validate_image(self, value):
        """
        Comprehensive image validation.
        
        Checks:
        1. File size
        2. MIME type
        3. Image format
        4. Image can be opened (not corrupted)
        5. Optional dimension requirements
        """
        bulk_order = self.context.get('bulk_order')
        
        if not bulk_order:
            raise serializers.ValidationError("Bulk order context is required")
        
        # 1. File size validation
        max_size = bulk_order.max_image_size_mb * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Image size must be less than {bulk_order.max_image_size_mb}MB. "
                f"Current size: {value.size / (1024 * 1024):.2f}MB"
            )
        
        # 2. MIME type validation (security check)
        try:
            mime = magic.from_buffer(value.read(2048), mime=True)
            value.seek(0)  # Reset file pointer
            
            allowed_mimes = [
                'image/jpeg', 'image/jpg', 'image/png', 'image/webp'
            ]
            if mime not in allowed_mimes:
                raise serializers.ValidationError(
                    f"Invalid file type: {mime}. Allowed types: JPEG, PNG, WebP"
                )
        except Exception as e:
            logger.error(f"MIME type check failed: {str(e)}")
            raise serializers.ValidationError("Could not verify file type")
        
        # 3. File extension validation
        ext = value.name.split('.')[-1].lower()
        if ext not in bulk_order.allowed_image_formats:
            raise serializers.ValidationError(
                f"Image format must be one of: {', '.join(bulk_order.allowed_image_formats)}. "
                f"Received: {ext}"
            )
        
        # 4. Image integrity check (can it be opened?)
        try:
            img = PILImage.open(value)
            img.verify()  # Verify it's actually an image
            value.seek(0)  # Reset file pointer
            
            # Optional: Check dimensions
            img = PILImage.open(value)  # Re-open after verify
            width, height = img.size
            
            # Minimum dimension requirements (optional)
            min_dimension = 200
            if width < min_dimension or height < min_dimension:
                raise serializers.ValidationError(
                    f"Image dimensions must be at least {min_dimension}x{min_dimension}px. "
                    f"Received: {width}x{height}px"
                )
            
            # Maximum dimension requirements (optional)
            max_dimension = 10000
            if width > max_dimension or height > max_dimension:
                raise serializers.ValidationError(
                    f"Image dimensions must not exceed {max_dimension}x{max_dimension}px. "
                    f"Received: {width}x{height}px"
                )
            
            value.seek(0)  # Reset file pointer
            
        except Exception as e:
            logger.error(f"Image validation failed: {str(e)}")
            raise serializers.ValidationError(
                "Invalid or corrupted image file. Please upload a valid image."
            )
        
        return value
    
    def validate_email(self, value):
        """Normalize and validate email"""
        return value.lower().strip()
    
    def validate(self, attrs):
        """Validate complete order entry"""
        bulk_order = self.context.get('bulk_order')
        
        if not bulk_order:
            raise serializers.ValidationError({"bulk_order": "Bulk order context is required"})
        
        # Check if bulk order has expired
        if bulk_order.is_expired():
            raise serializers.ValidationError({
                "bulk_order": "This bulk order has expired. No new entries are accepted."
            })
        
        # Validate custom_name requirement
        if bulk_order.custom_branding_enabled:
            custom_name = attrs.get('custom_name', '').strip()
            if not custom_name:
                raise serializers.ValidationError({
                    "custom_name": "Custom name is required for this bulk order"
                })
        
        # Validate and process coupon code
        coupon_code_str = attrs.pop('coupon_code', '').strip().upper()
        if coupon_code_str:
            try:
                coupon = ImageCouponCode.objects.select_for_update().get(
                    code=coupon_code_str,
                    bulk_order=bulk_order,
                    is_used=False
                )
                attrs['coupon_used'] = coupon
                attrs['paid'] = True  # Free entry via coupon
            except ImageCouponCode.DoesNotExist:
                raise serializers.ValidationError({
                    "coupon_code": f"Invalid or already used coupon code: {coupon_code_str}"
                })
        
        # Set bulk_order
        attrs['bulk_order'] = bulk_order
        
        return attrs
    
    def create(self, validated_data):
        """
        Create order entry with Cloudinary image upload.
        
        Optimizations:
        - Single transaction
        - Efficient Cloudinary upload with transformations
        - Proper error handling with rollback
        """
        image_file = validated_data.pop('image')
        coupon = validated_data.get('coupon_used')
        bulk_order = validated_data['bulk_order']
        
        try:
            # Upload image to Cloudinary with optimizations
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder=f'image_bulk_orders/{bulk_order.slug}',
                transformation=[
                    {'width': 1200, 'height': 1200, 'crop': 'limit'},
                    {'quality': 'auto:good', 'fetch_format': 'auto'}
                ],
                resource_type='image'
            )
            
            # Extract image metadata
            validated_data['uploaded_image'] = upload_result['secure_url']
            validated_data['cloudinary_public_id'] = upload_result['public_id']
            validated_data['image_width'] = upload_result.get('width')
            validated_data['image_height'] = upload_result.get('height')
            
            # Create order entry
            with transaction.atomic():
                order_entry = super().create(validated_data)
                
                # Mark coupon as used if applicable
                if coupon:
                    coupon.is_used = True
                    coupon.save(update_fields=['is_used'])
            
            logger.info(
                f"ImageOrderEntry created: {order_entry.reference} "
                f"(Image: {order_entry.cloudinary_public_id})"
            )
            
            return order_entry
            
        except Exception as e:
            logger.error(f"Error creating image order entry: {str(e)}")
            
            # Cleanup: Delete uploaded image if order creation fails
            if 'upload_result' in locals() and upload_result.get('public_id'):
                try:
                    cloudinary.uploader.destroy(upload_result['public_id'])
                    logger.info(f"Cleaned up orphaned image: {upload_result['public_id']}")
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup orphaned image: {str(cleanup_error)}")
            
            raise serializers.ValidationError(
                f"Failed to create order entry: {str(e)}"
            )


class ImageOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views"""
    bulk_order_name = serializers.CharField(source='bulk_order.organization_name', read_only=True)
    has_coupon = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageOrderEntry
        fields = [
            'id', 'reference', 'bulk_order_name', 'serial_number',
            'full_name', 'size', 'uploaded_image', 'paid', 'has_coupon',
            'created_at'
        ]
    
    def get_has_coupon(self, obj):
        return obj.coupon_used_id is not None