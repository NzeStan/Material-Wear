# order/serializers.py
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from products.constants import STATES
from products.models import NyscKit, NyscTour, Church
from .models import OrderItem, NyscKitOrder, NyscTourOrder, ChurchOrder


class OrderItemSerializer(serializers.Serializer):
    """Serializer for order items"""
    id = serializers.UUIDField(read_only=True)
    product_type = serializers.CharField(read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    extra_fields = serializers.DictField(read_only=True)
    
    def get_product_type(self, obj):
        """Get the product type name"""
        return obj.content_type.model


class BaseOrderSerializer(serializers.Serializer):
    """Base serializer for all order types"""
    id = serializers.UUIDField(read_only=True)
    serial_number = serializers.IntegerField(read_only=True)
    order_type = serializers.CharField(read_only=True)
    first_name = serializers.CharField()
    middle_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField()
    phone_number = serializers.CharField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    paid = serializers.BooleanField(read_only=True)
    created = serializers.DateTimeField(read_only=True)
    updated = serializers.DateTimeField(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)


class NyscKitOrderSerializer(BaseOrderSerializer):
    """Serializer for NYSC Kit orders - uses call_up_number as state_code"""
    call_up_number = serializers.CharField(max_length=20, help_text="Your NYSC call-up number (used as state code)")
    state = serializers.ChoiceField(choices=STATES)
    local_government = serializers.CharField(max_length=100)


class NyscTourOrderSerializer(BaseOrderSerializer):
    """Serializer for NYSC Tour orders"""
    pass  # Only needs base fields


class ChurchOrderSerializer(BaseOrderSerializer):
    """Serializer for Church orders"""
    pickup_on_camp = serializers.BooleanField(default=True)
    delivery_state = serializers.ChoiceField(choices=STATES, required=False, allow_blank=True)
    delivery_lga = serializers.CharField(max_length=100, required=False, allow_blank=True)


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout process - handles cart to order conversion"""
    # Base order fields (common to all order types)
    first_name = serializers.CharField(max_length=50)
    middle_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50)
    phone_number = serializers.CharField(max_length=15)
    
    # NYSC Kit specific fields - call_up_number replaces state_code
    call_up_number = serializers.CharField(
        max_length=20, 
        required=False, 
        allow_blank=True,
        help_text="Your NYSC call-up number (e.g., AB/22C/1234)"
    )
    state = serializers.ChoiceField(choices=STATES, required=False, allow_blank=True)
    local_government = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # Church specific fields
    pickup_on_camp = serializers.BooleanField(default=True, required=False)
    delivery_state = serializers.ChoiceField(choices=STATES, required=False, allow_blank=True)
    delivery_lga = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate based on cart contents"""
        # Get cart from context
        cart = self.context.get('cart')
        if not cart or len(cart) == 0:
            raise serializers.ValidationError({'cart': 'Cart is empty'})
        
        # Group cart items by product type to determine required fields
        product_types = set()
        for item in cart:
            product_types.add(item['product'].__class__.__name__)
        
        # Validate NYSC Kit fields
        if 'NyscKit' in product_types:
            if not attrs.get('call_up_number'):
                raise serializers.ValidationError({
                    'call_up_number': 'Call-up number is required for NYSC Kit orders (e.g., AB/22C/1234)'
                })
            if not attrs.get('state'):
                raise serializers.ValidationError({
                    'state': 'State is required for NYSC Kit orders'
                })
            if not attrs.get('local_government'):
                raise serializers.ValidationError({
                    'local_government': 'Local government is required for NYSC Kit orders'
                })
        
        # Validate NYSC Tour fields
        if 'NyscTour' in product_types:
            if not attrs.get('middle_name'):
                raise serializers.ValidationError({
                    'middle_name': 'Middle name is required for NYSC Tour orders'
                })
        
        # Validate Church fields
        if 'Church' in product_types:
            if not attrs.get('pickup_on_camp', True):
                if not attrs.get('delivery_state'):
                    raise serializers.ValidationError({
                        'delivery_state': 'Required when not picking up on camp'
                    })
                if not attrs.get('delivery_lga'):
                    raise serializers.ValidationError({
                        'delivery_lga': 'Required when not picking up on camp'
                    })
        
        return attrs


class OrderListSerializer(serializers.Serializer):
    """Lightweight serializer for order list view"""
    id = serializers.UUIDField()
    serial_number = serializers.IntegerField()
    order_type = serializers.CharField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid = serializers.BooleanField()
    created = serializers.DateTimeField()
    item_count = serializers.IntegerField()