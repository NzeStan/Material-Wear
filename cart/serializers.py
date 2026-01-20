# cart/serializers.py
from rest_framework import serializers
from django.apps import apps
from products.serializers import NyscKitSerializer, NyscTourSerializer, ChurchSerializer
from products.constants import (
    VEST_SIZES, CHURCH_SIZES, CAP_SIZE, MEASUREMENT_SIZE,
    NYSC_KIT_TYPE_CHOICES, PRODUCT_TYPE_CHOICES
)
from typing import Dict, Any, Optional, List
from measurement.models import Measurement


# Extract size values for validation
VALID_VEST_SIZES = [size[0] for size in VEST_SIZES if size[0]]  # Exclude empty option
VALID_CHURCH_SIZES = [size[0] for size in CHURCH_SIZES if size[0]]  # Exclude empty option


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
    
    def get_product(self, obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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
    product_type = serializers.ChoiceField(choices=[pt[0] for pt in PRODUCT_TYPE_CHOICES])
    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    override = serializers.BooleanField(default=False)
    
    # NYSC Kit specific fields
    size = serializers.CharField(required=False, allow_blank=True)
    
    # NYSC Tour specific fields
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
        
        # Build extra_fields based on product type
        extra_fields = {}
        
        # Handle product-specific validations
        if product_type == 'nysc_kit':
            # Get the authenticated user from the request context
            request = self.context.get('request')
            
            if product.type == 'kakhi':
                # Kakhi must use measurement size - check if user has measurement
                if not request or not request.user.is_authenticated:
                    raise serializers.ValidationError({
                        'user': 'You must be logged in to purchase Kakhi products'
                    })
                
                # Check if user has measurement
                try:
                    measurement = Measurement.objects.filter(
                        user=request.user, 
                        is_deleted=False
                    ).first()
                    
                    if not measurement:
                        raise serializers.ValidationError({
                            'measurement': 'You must create a measurement profile before purchasing Kakhi. Please go to your profile to add your measurements.'
                        })
                    
                    # Use measurement constants
                    extra_fields['size'] = MEASUREMENT_SIZE.lower()  # 'measurement'
                    extra_fields['measurement_id'] = str(measurement.id)
                    
                except Measurement.DoesNotExist:
                    raise serializers.ValidationError({
                        'measurement': 'You must create a measurement profile before purchasing Kakhi.'
                    })
                    
            elif product.type == 'cap':
                # Cap has fixed "free size" from constants
                extra_fields['size'] = CAP_SIZE.lower().replace(' ', '_')  # 'free_size'
                
            elif product.type == 'vest':
                # Vest requires size selection - validate against VEST_SIZES constant
                if not attrs.get('size'):
                    raise serializers.ValidationError({
                        'size': f'Size is required for Vest products. Valid sizes: {", ".join(VALID_VEST_SIZES)}'
                    })
                
                # Validate size is in VALID_VEST_SIZES
                if attrs['size'] not in VALID_VEST_SIZES:
                    raise serializers.ValidationError({
                        'size': f'Invalid size. Valid sizes: {", ".join(VALID_VEST_SIZES)}'
                    })
                
                extra_fields['size'] = attrs['size']
                
        elif product_type == 'church':
            # Church requires size selection - validate against CHURCH_SIZES constant
            if not attrs.get('size'):
                raise serializers.ValidationError({
                    'size': f'Size is required for Church products. Valid sizes: {", ".join(VALID_CHURCH_SIZES)}'
                })
            
            # Validate size is in VALID_CHURCH_SIZES
            if attrs['size'] not in VALID_CHURCH_SIZES:
                raise serializers.ValidationError({
                    'size': f'Invalid size. Valid sizes: {", ".join(VALID_CHURCH_SIZES)}'
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
        
        # Store processed extra_fields
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
    grouped_by_type = serializers.SerializerMethodField()

    def get_grouped_by_type(self, obj: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Group cart items by product type"""
        items = obj.get('items', [])
        grouped = {}
        for item in items:
            ptype = item['product'].__class__.__name__
            if ptype not in grouped:
                grouped[ptype] = []
            
            # Serialize the item properly using CartItemSerializer
            serialized_item = CartItemSerializer(item).data  # ✅ Serialized!
            grouped[ptype].append(serialized_item)
        return grouped
    
class ClearCartSerializer(serializers.Serializer):
    """Serializer for clearing cart - no input required"""
    pass