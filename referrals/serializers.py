from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ReferrerProfile, PromotionalMedia


User = get_user_model()


class ReferrerProfileSerializer(serializers.ModelSerializer):
    """Serializer for ReferrerProfile model"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    referral_code = serializers.CharField(read_only=True)

    class Meta:
        model = ReferrerProfile
        fields = [
            'id',
            'user',
            'user_email',
            'referral_code',
            'full_name',
            'phone_number',
            'bank_name',
            'account_number',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'referral_code', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Ensure user doesn't already have a referrer profile"""
        user = self.context['request'].user
        
        # Check if this is an update operation
        if self.instance:
            return attrs
        
        # For create operations, check if user already has a profile
        if ReferrerProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError(
                "You already have a referrer profile. Each user can only have one profile."
            )
        
        return attrs

    def create(self, validated_data):
        """Create referrer profile with authenticated user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PromotionalMediaSerializer(serializers.ModelSerializer):
    """Serializer for PromotionalMedia model"""
    media_url = serializers.CharField(read_only=True)
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PromotionalMedia
        fields = [
            'id',
            'title',
            'media_type',
            'media_file',
            'media_url',
            'marketing_text',
            'is_active',
            'order',
            'created_at',
            'updated_at',
            'created_by_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'media_url']

    def get_created_by_name(self, obj):
        if hasattr(obj, 'created_by') and obj.created_by:
            # Get full name
            full_name = obj.created_by.get_full_name().strip()
            
            # If full name is empty, use username
            if full_name:
                return full_name
            elif hasattr(obj.created_by, 'username') and obj.created_by.username:
                return obj.created_by.username
            elif hasattr(obj.created_by, 'email') and obj.created_by.email:
                # Extract name from email (before @)
                return obj.created_by.email.split('@')[0]
        
        # Return None (will show as null in JSON) or empty string
        return None  # or return ""


class SharePayloadSerializer(serializers.Serializer):
    """Serializer for the share payload response"""
    promotional_media = PromotionalMediaSerializer(many=True, read_only=True)
    referral_code = serializers.CharField(read_only=True)
    whatsapp_link = serializers.URLField(read_only=True)
    share_message = serializers.CharField(read_only=True)