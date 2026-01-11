# cart/serializers.py
from rest_framework import serializers
from django.apps import apps
from products.serializers import NyscKitSerializer, NyscTourSerializer, ChurchSerializer


class CartItemSerializer(serializers.Serializer):
    """Serializer for individual cart items"""
    product_type = serializers.CharField(read_only=True)
    product_id = serializers.UUIDField(read_only=True)
    product = serializers.SerializerMethodField()
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    extra_fields = serializers.DictField(read_only=True)
    item_key = serializers.CharField(read_only=True)
    
    def get_product(self, obj):
        """Serialize product based on its type"""
        product = obj.get('product')
        if not product:
            return None
            
        product_class_name = product.__class__.__name__
        serializer_map = {
            'NyscKit': NyscKitSerializer,
            'NyscTour': NyscTourSerializer,
            'Church': ChurchSerializer,
        }
        
        serializer_class = serializer_map.get(product_class_name)
        if serializer_class:
            return serializer_class(product).data
        return None


class AddToCartSerializer(serializers.Serializer):
    """Serializer for adding items to cart"""
    product_type = serializers.ChoiceField(choices=['nysc_kit', 'nysc_tour', 'church'])
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    override = serializers.BooleanField(default=False)
    extra_fields = serializers.DictField(required=False, default=dict)
    
    # NYSC Kit specific fields
    size = serializers.CharField(required=False, allow_blank=True)
    call_up_number = serializers.CharField(required=False, allow_blank=True)
    
    # Church specific fields
    custom_name_text = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate product exists and handle product-specific requirements"""
        product_type = attrs['product_type']
        product_id = attrs['product_id']
        
        # Get the product model
        model_mapping = {
            'nysc_kit': 'NyscKit',
            'nysc_tour': 'NyscTour',
            'church': 'Church'
        }
        
        try:
            model = apps.get_model('products', model_mapping[product_type])
            product = model.objects.get(id=product_id)
        except model.DoesNotExist:
            raise serializers.ValidationError({
                'product_id': 'Product not found'
            })
        
        # Check if product can be purchased
        if not product.can_be_purchased:
            raise serializers.ValidationError({
                'product_id': 'This product is not available for purchase'
            })
        
        # Build extra_fields from individual fields
        extra_fields = attrs.get('extra_fields', {})
        
        # Handle product-specific validations
        if product_type == 'nysc_kit':
            if not attrs.get('size'):
                raise serializers.ValidationError({
                    'size': 'Size is required for NYSC Kit products'
                })
            extra_fields['size'] = attrs['size']
            
            # Kakhi requires call-up number
            if product.type == 'kakhi':
                if not attrs.get('call_up_number'):
                    raise serializers.ValidationError({
                        'call_up_number': 'Call-up number is required for Kakhi products'
                    })
                extra_fields['call_up_number'] = attrs['call_up_number']
                
        elif product_type == 'church':
            if not attrs.get('size'):
                raise serializers.ValidationError({
                    'size': 'Size is required for Church products'
                })
            extra_fields['size'] = attrs['size']
            
            # Custom name is optional
            if attrs.get('custom_name_text'):
                extra_fields['custom_name_text'] = attrs['custom_name_text']
                
        elif product_type == 'nysc_tour':
            if not attrs.get('call_up_number'):
                raise serializers.ValidationError({
                    'call_up_number': 'Call-up number is required for NYSC Tour'
                })
            extra_fields['call_up_number'] = attrs['call_up_number']
        
        # Store processed extra_fields back
        attrs['extra_fields'] = extra_fields
        attrs['product'] = product  # Store product for later use
        
        return attrs


class UpdateCartItemSerializer(serializers.Serializer):
    """Serializer for updating cart item quantity"""
    quantity = serializers.IntegerField(min_value=0)  # 0 means remove
    
    def validate_quantity(self, value):
        """Ensure quantity is valid"""
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value


class CartSerializer(serializers.Serializer):
    """Serializer for the entire cart"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    grouped_by_type = serializers.DictField(read_only=True)