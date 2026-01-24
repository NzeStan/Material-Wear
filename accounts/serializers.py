# accounts/serializers.py
from rest_framework import serializers
from dj_rest_auth.serializers import (
    UserDetailsSerializer, 
    LoginSerializer, 
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout endpoint - empty but required for drf-spectacular"""
    pass


class UserStatusSerializer(serializers.Serializer):
    """
    Comprehensive user authentication status serializer
    
    Returns authentication state and complete user role/permission information
    for frontend access control and conditional UI rendering.
    """
    is_authenticated = serializers.BooleanField()
    user = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        """Get basic user information"""
        if obj.get('is_authenticated') and obj.get('user'):
            user = obj['user']
            return {
                'id': str(user.id),
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                
                # Account status
                'is_active': user.is_active,
                
                # Role/Permission flags
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,  # Admin access
                
                # Timestamps
                'date_joined': user.date_joined,
                'last_login': user.last_login,
            }
        return None
    
    def get_permissions(self, obj):
        """
        Get user permissions and groups
        
        Returns detailed permission information for frontend access control:
        - User groups
        - Specific permissions
        - Quick role checks
        """
        if not obj.get('is_authenticated') or not obj.get('user'):
            return None
        
        user = obj['user']
        
        # Get user groups
        groups = list(user.groups.values_list('name', flat=True))
        
        # Get specific permissions (if you need granular control)
        # Format: 'app_label.codename'
        user_permissions = []
        if user.is_superuser:
            # Superusers have all permissions
            user_permissions = ['all']
        else:
            # Get actual permissions
            permissions = user.user_permissions.select_related('content_type').all()
            user_permissions = [
                f"{perm.content_type.app_label}.{perm.codename}" 
                for perm in permissions
            ]
        
        return {
            'groups': groups,
            'permissions': user_permissions,
            
            # Quick role checks for common access patterns
            'roles': {
                'is_admin': user.is_staff or user.is_superuser,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'can_access_admin': user.is_staff or user.is_superuser,
                'can_manage_users': user.is_superuser,
                'can_manage_orders': user.is_staff or user.is_superuser,
                'can_manage_products': user.is_staff or user.is_superuser,
                'can_view_reports': user.is_staff or user.is_superuser,
            },
            
            # Permission helpers (customize based on your needs)
            'can': {
                'create_bulk_orders': user.is_authenticated,
                'view_all_orders': user.is_staff or user.is_superuser,
                'edit_products': user.is_staff or user.is_superuser,
                'manage_measurements': user.is_authenticated,
                'access_admin_panel': user.is_staff or user.is_superuser,
            }
        }


class UserStatusBasicSerializer(serializers.Serializer):
    """
    Lightweight user status serializer (for high-frequency checks)
    
    Returns minimal authentication state without permission lookups.
    Use this for frequent polling or when you only need to know if user is logged in.
    """
    is_authenticated = serializers.BooleanField()
    user = serializers.SerializerMethodField()
    
    def get_user(self, obj):
        """Get minimal user information"""
        if obj.get('is_authenticated') and obj.get('user'):
            user = obj['user']
            return {
                'id': str(user.id),
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            }
        return None


class CustomUserSerializer(UserDetailsSerializer):
    """
    Custom user serializer with read-only sensitive fields
    and computed full_name field
    """
    email = serializers.EmailField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    full_name = serializers.SerializerMethodField()
    is_superuser = serializers.BooleanField(read_only=True)
    is_staff = serializers.BooleanField(read_only=True)
    
    class Meta(UserDetailsSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'full_name', 
                 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
        read_only_fields = ('id', 'email', 'username', 'is_active', 'is_staff', 
                           'is_superuser', 'date_joined', 'last_login')
    
    def get_full_name(self, obj):
        """Return full name or email if names not provided"""
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name if full_name else obj.email


class CustomRegisterSerializer(RegisterSerializer):
    """Custom registration serializer with optional first/last names"""
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    def validate_password1(self, password):
        """Validate password strength"""
        try:
            validate_password(password, self.instance)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return password
    
    def get_cleaned_data(self):
        """Get cleaned registration data"""
        data = super().get_cleaned_data()
        data.update({
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
        })
        return data
    
    def save(self, request):
        """Save new user and log registration"""
        user = super().save(request)
        logger.info(f"New user registered: {user.email}")
        return user


class CustomLoginSerializer(LoginSerializer):
    """Custom login serializer using email instead of username"""
    email = serializers.EmailField(required=True)
    username = None  # Remove username field
    
    def validate(self, attrs):
        """Validate login credentials"""
        attrs = super().validate(attrs)
        return attrs


class CustomPasswordResetSerializer(PasswordResetSerializer):
    """Custom password reset serializer with enhanced email sending"""
    
    def save(self):
        """Send password reset email"""
        request = self.context.get('request')
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
            'html_email_template_name': 'registration/password_reset_email.html',
        }
        self.reset_form.save(**opts)
        logger.info(f"Password reset email sent for: {self.validated_data['email']}")


class CustomPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    """Custom password reset confirm serializer with password validation"""
    
    def validate(self, attrs):
        """Validate password reset data"""
        attrs = super().validate(attrs)
        
        # Add password strength validation
        password = attrs['new_password1']
        try:
            validate_password(password, self.user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password1': list(e.messages)})
        return attrs
    
    def save(self):
        """Save new password and log action"""
        self.user.set_password(self.validated_data['new_password1'])
        self.user.save()
        logger.info(f"Password reset successful for user: {self.user.email}")
        return self.user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password for authenticated users"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password1 = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        """Validate that old password is correct"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate(self, data):
        """Validate that new passwords match and meet requirements"""
        if data['new_password1'] != data['new_password2']:
            raise serializers.ValidationError({"new_password2": "Passwords don't match"})
        
        # Validate password strength
        try:
            validate_password(data['new_password1'], self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password1": list(e.messages)})
        
        return data
    
    def save(self):
        """Save new password and log action"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password1'])
        user.save()
        logger.info(f"Password changed for user: {user.email}")
        return user