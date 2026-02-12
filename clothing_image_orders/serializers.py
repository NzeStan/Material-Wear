# clothing_image_orders/serializers.py
"""
Serializers for clothing image orders API.
"""
from rest_framework import serializers
from .models import ClothingImageOrder, ClothingOrderParticipant, ClothingCouponCode
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class ClothingCouponCodeSerializer(serializers.ModelSerializer):
    """Serializer for coupon codes"""
    
    order_reference = serializers.CharField(source='order.reference', read_only=True)
    order_title = serializers.CharField(source='order.title', read_only=True)
    
    class Meta:
        model = ClothingCouponCode
        fields = [
            'id', 'order', 'order_reference', 'order_title', 
            'code', 'is_used', 'created_at'
        ]
        read_only_fields = ['id', 'is_used', 'created_at']


class ClothingImageOrderListSerializer(serializers.ModelSerializer):
    """Serializer for listing clothing image orders"""
    
    is_expired = serializers.SerializerMethodField()
    participant_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = ClothingImageOrder
        fields = [
            'id', 'reference', 'organization_name', 'title',
            'coordinator_name', 'coordinator_email', 'coordinator_phone',
            'price_per_item', 'requires_custom_name', 'requires_image',
            'order_deadline', 'is_active', 'is_expired',
            'participant_stats', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        """Check if order is expired"""
        return obj.is_expired()
    
    def get_participant_stats(self, obj):
        """Get participant statistics"""
        return obj.get_participant_stats()


class ClothingImageOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for clothing image orders"""
    
    is_expired = serializers.SerializerMethodField()
    participant_stats = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()
    
    class Meta:
        model = ClothingImageOrder
        fields = [
            'id', 'reference', 'organization_name', 'title', 'description',
            'coordinator_name', 'coordinator_email', 'coordinator_phone',
            'price_per_item', 'requires_custom_name', 'requires_image',
            'order_deadline', 'is_active', 'is_expired',
            'participant_stats', 'participants',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']
    
    def get_is_expired(self, obj):
        """Check if order is expired"""
        return obj.is_expired()
    
    def get_participant_stats(self, obj):
        """Get participant statistics"""
        return obj.get_participant_stats()
    
    def get_participants(self, obj):
        """Get limited participant data"""
        participants = obj.participants.all().select_related('coupon_used')[:10]
        return ClothingOrderParticipantListSerializer(participants, many=True).data


class ClothingImageOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating clothing image orders"""
    
    class Meta:
        model = ClothingImageOrder
        fields = [
            'organization_name', 'title', 'description',
            'coordinator_name', 'coordinator_email', 'coordinator_phone',
            'price_per_item', 'requires_custom_name', 'requires_image',
            'order_deadline', 'is_active'
        ]
    
    def validate_price_per_item(self, value):
        """Validate price is positive"""
        if value <= Decimal('0'):
            raise serializers.ValidationError("Price must be greater than zero")
        return value
    
    def validate_order_deadline(self, value):
        """Validate deadline is in the future"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Order deadline must be in the future")
        return value
    
    def create(self, validated_data):
        """Create order with current user"""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class ClothingOrderParticipantListSerializer(serializers.ModelSerializer):
    """Serializer for listing participants"""
    
    order_reference = serializers.CharField(source='order.reference', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ClothingOrderParticipant
        fields = [
            'id', 'reference', 'serial_number', 'order_reference',
            'email', 'full_name', 'phone', 'size', 'custom_name',
            'image_url', 'paid', 'payment_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reference', 'serial_number', 'paid', 
            'payment_date', 'created_at', 'updated_at'
        ]
    
    def get_image_url(self, obj):
        """Get image URL if exists"""
        if obj.image:
            return obj.image.url
        return None


class ClothingOrderParticipantDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for participants"""
    
    order = ClothingImageOrderListSerializer(read_only=True)
    coupon_used = ClothingCouponCodeSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    expected_filename = serializers.SerializerMethodField()
    
    class Meta:
        model = ClothingOrderParticipant
        fields = [
            'id', 'reference', 'serial_number', 'order',
            'email', 'full_name', 'phone', 'size', 'custom_name',
            'image', 'image_url', 'expected_filename',
            'paid', 'payment_reference', 'payment_date',
            'coupon_used', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reference', 'serial_number', 'paid',
            'payment_reference', 'payment_date', 
            'created_at', 'updated_at'
        ]
    
    def get_image_url(self, obj):
        """Get image URL if exists"""
        if obj.image:
            return obj.image.url
        return None
    
    def get_expected_filename(self, obj):
        """Get expected filename for this participant"""
        return obj.get_image_filename()


class ClothingOrderParticipantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating participants"""
    
    coupon_code = serializers.CharField(required=False, allow_blank=True, write_only=True)
    
    class Meta:
        model = ClothingOrderParticipant
        fields = [
            'email', 'full_name', 'phone', 'size', 
            'custom_name', 'image', 'coupon_code'
        ]
    
    def validate(self, attrs):
        """Validate participant data"""
        order = self.context.get('order')
        
        if not order:
            raise serializers.ValidationError({"order": "Order context is required"})
        
        # Check if order is active
        if not order.is_active:
            raise serializers.ValidationError({"order": "This order is closed"})
        
        # Check if order is expired
        if order.is_expired():
            raise serializers.ValidationError({"order": "This order has expired"})
        
        # Validate custom_name
        if order.requires_custom_name and not attrs.get('custom_name'):
            raise serializers.ValidationError({
                "custom_name": "Custom name is required for this order"
            })
        
        # Validate image
        if order.requires_image and not attrs.get('image'):
            raise serializers.ValidationError({
                "image": "Image upload is required for this order"
            })
        
        # Validate coupon code if provided
        coupon_code = attrs.pop('coupon_code', None)
        if coupon_code:
            try:
                coupon = ClothingCouponCode.objects.get(
                    code=coupon_code.upper(),
                    order=order
                )
                
                if coupon.is_used:
                    raise serializers.ValidationError({
                        "coupon_code": "This coupon code has already been used"
                    })
                
                attrs['coupon_used'] = coupon
                
            except ClothingCouponCode.DoesNotExist:
                raise serializers.ValidationError({
                    "coupon_code": "Invalid coupon code"
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create participant"""
        order = self.context.get('order')
        validated_data['order'] = order
        
        # Mark coupon as used if present
        coupon = validated_data.get('coupon_used')
        if coupon:
            coupon.is_used = True
            coupon.save()
        
        participant = ClothingOrderParticipant.objects.create(**validated_data)
        
        logger.info(f"Created participant: {participant.reference}")
        
        return participant


class ParticipantPaymentInitializeSerializer(serializers.Serializer):
    """Serializer for payment initialization"""
    
    callback_url = serializers.URLField(
        required=False,
        help_text="Frontend callback URL for payment redirect"
    )


class ParticipantPaymentVerifySerializer(serializers.Serializer):
    """Serializer for payment verification response"""
    
    paid = serializers.BooleanField()
    reference = serializers.CharField()
    full_name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_date = serializers.DateTimeField(allow_null=True)