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

    bulk_order_name = serializers.CharField(
        source="bulk_order.organization_name", read_only=True
    )
    bulk_order_slug = serializers.CharField(source="bulk_order.slug", read_only=True)

    class Meta:
        model = ImageCouponCode
        fields = [
            "id",
            "bulk_order",
            "bulk_order_name",
            "bulk_order_slug",
            "code",
            "is_used",
            "created_at",
        ]
        read_only_fields = ("id", "is_used", "created_at")


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
            "id",
            "slug",
            "organization_name",
            "price_per_item",
            "custom_branding_enabled",
            "payment_deadline",
            "is_expired",
            "shareable_url",
        ]

    def get_is_expired(self, obj: "ImageBulkOrderLink") -> bool:
        """Check if bulk order link has expired"""
        return obj.is_expired()

    def get_shareable_url(self, obj: "ImageBulkOrderLink") -> str:
        """Get shareable URL for bulk order"""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/image-bulk-order/{obj.slug}/")
        return f"/image-bulk-order/{obj.slug}/"


class ImageOrderEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for order entries.
    IDENTICAL to OrderEntrySerializer from bulk_orders BUT with optional image field.
    """

    bulk_order = ImageBulkOrderLinkSummarySerializer(read_only=True)
    coupon_code = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    custom_name = serializers.CharField(required=False, allow_blank=True)

    # ✅ NEW: Image field (optional, write-only for upload)
    image = serializers.ImageField(required=False, allow_null=True, write_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ImageOrderEntry
        fields = [
            "id",
            "reference",
            "bulk_order",
            "serial_number",
            "email",
            "full_name",
            "size",
            "custom_name",
            "image",
            "image_url",
            "coupon_used",
            "paid",
            "created_at",
            "updated_at",
            "coupon_code",
        ]
        read_only_fields = (
            "id",
            "reference",
            "bulk_order",
            "serial_number",
            "coupon_used",
            "paid",
            "created_at",
            "updated_at",
            "image_url",
        )

    def get_image_url(self, obj: "ImageOrderEntry") -> Optional[str]:
        """Get Cloudinary URL for uploaded image"""
        if obj.image:
            return obj.image.url
        return None

    def to_representation(self, instance):
        """Conditionally include custom_name based on bulk_order settings"""
        representation = super().to_representation(instance)

        # Only include custom_name if custom branding is enabled
        if not instance.bulk_order.custom_branding_enabled:
            representation.pop("custom_name", None)

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

            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if mime not in allowed_types:
                raise serializers.ValidationError(
                    f"Invalid image type '{mime}'. Allowed types: JPEG, PNG, GIF, WebP"
                )

            logger.info(
                f"Image validated successfully: {mime}, size: {value.size / 1024:.2f}KB"
            )
            return value

        except Exception as e:
            logger.error(f"Error validating image: {str(e)}")
            raise serializers.ValidationError(f"Error validating image: {str(e)}")

    def validate(self, attrs):
        """Validate coupon code and payment deadline"""
        # Get bulk_order from context (passed from ViewSet)
        bulk_order = self.context.get("bulk_order")

        if not bulk_order:
            raise serializers.ValidationError(
                {"bulk_order": "Bulk order context is required."}
            )

        # Check if deadline has passed
        if bulk_order.is_expired():
            raise serializers.ValidationError(
                {
                    "payment_deadline": "This bulk order has expired and is no longer accepting submissions."
                }
            )

        # ✅ FIX: Validate custom_name only if branding is enabled
        if not bulk_order.custom_branding_enabled:
            attrs.pop("custom_name", None)  # Remove custom_name if not enabled

        # ✅ FIX: Validate coupon belongs to THIS specific bulk_order
        coupon_code_str = attrs.pop("coupon_code", None)
        if coupon_code_str:
            try:
                coupon = ImageCouponCode.objects.get(
                    code=coupon_code_str.upper(),
                    bulk_order=bulk_order,  # ✅ Must match THIS bulk order
                    is_used=False,
                )
                attrs["coupon_used"] = coupon
                # ✅ FIX: When coupon is used, automatically mark as paid
                attrs["paid"] = True
            except ImageCouponCode.DoesNotExist:
                raise serializers.ValidationError(
                    {
                        "coupon_code": f"Invalid coupon code or coupon does not belong to {bulk_order.organization_name}. Please check your code."
                    }
                )

        return attrs

    def create(self, validated_data):
        """Create order entry with proper coupon handling and Cloudinary image upload"""
        bulk_order = self.context.get("bulk_order")
        coupon_used = validated_data.get("coupon_used")

        # Extract image before creating (Cloudinary will handle upload)
        image = validated_data.pop("image", None)

        # Create order entry
        order_entry = ImageOrderEntry.objects.create(
            bulk_order=bulk_order, **validated_data
        )

        # Upload image to Cloudinary if provided (organized by slug and size)
        if image:
            folder_path = f"image_bulk_orders/{bulk_order.slug}/{order_entry.size}"

            # Determine filename
            if order_entry.custom_name:
                filename = order_entry.custom_name.replace(" ", "_")
            else:
                filename = f"{order_entry.serial_number}_{order_entry.full_name.replace(' ', '_')}"

            order_entry.image = image
            order_entry.image.folder = folder_path
            order_entry.image.public_id = filename
            order_entry.save(update_fields=["image"])

            logger.info(f"Image uploaded to Cloudinary: {folder_path}/{filename}")

        # Mark coupon as used if provided
        if coupon_used:
            coupon_used.is_used = True
            coupon_used.save(update_fields=["is_used"])
            logger.info(f"Coupon marked as used: {coupon_used.code}")

        # ✅ SEND ORDER CONFIRMATION EMAIL
        from material.background_utils import send_image_order_confirmation_email

        send_image_order_confirmation_email(order_entry)

        return order_entry


class ImageBulkOrderLinkSerializer(serializers.ModelSerializer):
    """
    Full serializer for bulk order links.
    IDENTICAL to BulkOrderLinkSerializer from bulk_orders.
    """

    orders = ImageOrderEntrySerializer(many=True, read_only=True)
    order_count = serializers.IntegerField(source="orders.count", read_only=True)
    paid_count = serializers.SerializerMethodField()
    coupon_count = serializers.IntegerField(source="coupons.count", read_only=True)
    shareable_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageBulkOrderLink
        fields = [
            "id",
            "slug",
            "organization_name",
            "price_per_item",
            "custom_branding_enabled",
            "payment_deadline",
            "created_by",
            "created_at",
            "updated_at",
            "orders",
            "order_count",
            "paid_count",
            "coupon_count",
            "shareable_url",
        ]
        read_only_fields = ("created_by", "created_at", "updated_at", "slug")
        lookup_field = "slug"

    def get_paid_count(self, obj: "ImageBulkOrderLink") -> int:
        """Get count of paid orders"""
        return obj.orders.filter(paid=True).count()

    def get_shareable_url(self, obj: "ImageBulkOrderLink") -> str:
        """Get shareable URL for bulk order"""
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/image-bulk-order/{obj.slug}/")
        return f"/image-bulk-order/{obj.slug}/"

    def create(self, validated_data):
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)
