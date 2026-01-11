# order/serializers.py
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import BaseOrder, NyscKitOrder, NyscTourOrder, ChurchOrder, OrderItem
from products.models import NyscKit, NyscTour, Church
from products.serializers import NyscKitSerializer, NyscTourSerializer, ChurchSerializer
from products.constants import STATES


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items"""
    product = serializers.SerializerMethodField()
    product_type = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_type', 'product', 'price', 'quantity', 
            'extra_fields', 'cost'
        ]
        read_only_fields = ['id']
    
    def get_product(self, obj):
        """Serialize the related product"""
        product = obj.product
        if not product:
            return None
        
        serializer_map = {
            'NyscKit': NyscKitSerializer,
            'NyscTour': NyscTourSerializer,
            'Church': ChurchSerializer,
        }
        
        serializer_class = serializer_map.get(product.__class__.__name__)
        if serializer_class:
            return serializer_class(product).data
        return None
    
    def get_product_type(self, obj):
        """Get product type name"""
        if obj.product:
            return obj.product.__class__.__name__
        return None
    
    def get_cost(self, obj):
        """Get total cost for this item"""
        return obj.get_cost()


class BaseOrderSerializer(serializers.ModelSerializer):
    """Base serializer for all order types"""
    items = OrderItemSerializer(many=True, read_only=True)
    total_cost = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    order_type = serializers.SerializerMethodField()
    
    class Meta:
        model = BaseOrder
        fields = [
            'id', 'serial_number', 'user', 'email', 'first_name', 
            'middle_name', 'last_name', 'phone_number', 'paid', 
            'created', 'updated', 'items', 'total_cost', 'order_type'
        ]
        read_only_fields = ['id', 'serial_number', 'user', 'paid', 'created', 'updated']
    
    def get_order_type(self, obj):
        """Get the specific order type"""
        return obj.__class__.__name__


class NyscKitOrderSerializer(BaseOrderSerializer):
    """Serializer for NYSC Kit orders"""
    
    class Meta(BaseOrderSerializer.Meta):
        model = NyscKitOrder
        fields = BaseOrderSerializer.Meta.fields + [
            'state_code', 'state', 'local_government'
        ]
    
    def validate_state_code(self, value):
        """Ensure state code is uppercase"""
        return value.upper()


class NyscTourOrderSerializer(BaseOrderSerializer):
    """Serializer for NYSC Tour orders"""
    
    class Meta(BaseOrderSerializer.Meta):
        model = NyscTourOrder
        fields = BaseOrderSerializer.Meta.fields


class ChurchOrderSerializer(BaseOrderSerializer):
    """Serializer for Church orders"""
    
    class Meta(BaseOrderSerializer.Meta):
        model = ChurchOrder
        fields = BaseOrderSerializer.Meta.fields + [
            'pickup_on_camp', 'delivery_state', 'delivery_lga'
        ]
    
    def validate(self, attrs):
        """Validate delivery details if not picking up on camp"""
        if not attrs.get('pickup_on_camp', True):
            if not attrs.get('delivery_state') or not attrs.get('delivery_lga'):
                raise serializers.ValidationError({
                    'delivery_state': 'Required when not picking up on camp',
                    'delivery_lga': 'Required when not picking up on camp'
                })
        return attrs


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout process - handles cart to order conversion"""
    # Base order fields (common to all order types)
    first_name = serializers.CharField(max_length=50)
    middle_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=50)
    phone_number = serializers.CharField(max_length=15)
    
    # NYSC Kit specific fields
    state_code = serializers.CharField(max_length=11, required=False, allow_blank=True)
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
            if not attrs.get('state_code'):
                raise serializers.ValidationError({
                    'state_code': 'Required for NYSC Kit orders'
                })
            if not attrs.get('state'):
                raise serializers.ValidationError({
                    'state': 'Required for NYSC Kit orders'
                })
            if not attrs.get('local_government'):
                raise serializers.ValidationError({
                    'local_government': 'Required for NYSC Kit orders'
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