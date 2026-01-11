# products/serializers.py
from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import Category, NyscKit, NyscTour, Church
from django.conf import settings


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'product_type', 'description', 'product_count']
        read_only_fields = ['id']
        
    def get_product_count(self, obj):
        """Get count of available products in this category"""
        model_map = {
            'nysc_kit': NyscKit,
            'nysc_tour': NyscTour,
            'church': Church,
        }
        model = model_map.get(obj.product_type)
        if model:
            return model.objects.filter(category=obj, available=True).count()
        return 0


class BaseProductSerializer(serializers.ModelSerializer):
    """Base serializer for all product types"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    absolute_url = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()
    can_be_purchased = serializers.BooleanField(read_only=True)
    
    def get_absolute_url(self, obj):
        """Get the absolute URL for this product"""
        return obj.get_absolute_url()
    
    def get_thumbnail(self, obj):
        """Get optimized thumbnail URL"""
        if obj.image:
            # For Cloudinary images, use transformation for thumbnail
            if hasattr(obj.image, 'build_url'):
                return obj.image.build_url(
                    width=300,
                    height=300,
                    crop='fill',
                    quality='auto',
                    fetch_format='auto'
                )
            return obj.image.url
        return None


class NyscKitSerializer(BaseProductSerializer):
    """Serializer for NYSC Kit products"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = NyscKit
        fields = [
            'id', 'name', 'slug', 'type', 'type_display', 'category', 
            'category_name', 'description', 'price', 'image', 'image_1', 
            'image_2', 'image_3', 'available', 'out_of_stock', 
            'created', 'updated', 'absolute_url', 'thumbnail', 'can_be_purchased'
        ]
        read_only_fields = ['id', 'slug', 'created', 'updated', 'can_be_purchased']
        
    def to_representation(self, instance):
        """Optimize image fields for API response"""
        representation = super().to_representation(instance)
        
        # Remove null images
        image_fields = ['image', 'image_1', 'image_2', 'image_3']
        for field in image_fields:
            if not representation.get(field):
                representation.pop(field, None)
                
        return representation


class NyscTourSerializer(BaseProductSerializer):
    """Serializer for NYSC Tour products"""
    
    class Meta:
        model = NyscTour
        fields = [
            'id', 'name', 'slug', 'category', 'category_name', 'description', 
            'price', 'image', 'image_1', 'image_2', 'image_3', 'available', 
            'out_of_stock', 'created', 'updated', 'absolute_url', 'thumbnail',
            'can_be_purchased'
        ]
        read_only_fields = ['id', 'slug', 'created', 'updated', 'can_be_purchased']
        
    def to_representation(self, instance):
        """Optimize image fields for API response"""
        representation = super().to_representation(instance)
        
        # Remove null images
        image_fields = ['image', 'image_1', 'image_2', 'image_3']
        for field in image_fields:
            if not representation.get(field):
                representation.pop(field, None)
                
        return representation


class ChurchSerializer(BaseProductSerializer):
    """Serializer for Church merchandise products"""
    church_display = serializers.CharField(source='get_church_display', read_only=True)
    
    class Meta:
        model = Church
        fields = [
            'id', 'name', 'slug', 'church', 'church_display', 'category', 
            'category_name', 'description', 'price', 'image', 'image_1', 
            'image_2', 'image_3', 'available', 'out_of_stock', 'created', 
            'updated', 'absolute_url', 'thumbnail', 'can_be_purchased'
        ]
        read_only_fields = ['id', 'slug', 'created', 'updated', 'can_be_purchased']
        
    def to_representation(self, instance):
        """Optimize image fields for API response"""
        representation = super().to_representation(instance)
        
        # Remove null images
        image_fields = ['image', 'image_1', 'image_2', 'image_3']
        for field in image_fields:
            if not representation.get(field):
                representation.pop(field, None)
                
        return representation


class ProductListSerializer(serializers.Serializer):
    """Serializer for mixed product list view"""
    nysc_kits = NyscKitSerializer(many=True, read_only=True)
    nysc_tours = NyscTourSerializer(many=True, read_only=True)
    churches = ChurchSerializer(many=True, read_only=True)
    categories = CategorySerializer(many=True, read_only=True)
    current_category = CategorySerializer(read_only=True, allow_null=True)
    pagination = serializers.DictField(read_only=True)