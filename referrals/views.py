from urllib.parse import quote
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from .models import ReferrerProfile, PromotionalMedia
from .serializers import (
    ReferrerProfileSerializer,
    PromotionalMediaSerializer,
    SharePayloadSerializer
)
from django.conf import settings


class ReferrerProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing referrer profiles.
    
    - list: Admin only - list all referrer profiles
    - create: Authenticated users can create their profile (one per user)
    - retrieve: Users can view their own profile
    - update/partial_update: Users can update their own profile
    - destroy: Admin only
    """
    serializer_class = ReferrerProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return profiles based on user permissions"""
        user = self.request.user
        if user.is_staff:
            return ReferrerProfile.objects.all().select_related('user')
        return ReferrerProfile.objects.filter(user=user).select_related('user')

    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['list', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        """Create a referrer profile for the authenticated user"""
        # Check if user already has a profile
        if ReferrerProfile.objects.filter(user=request.user).exists():
            return Response(
                {'detail': 'You already have a referrer profile. Each user can only have one profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @action(detail=False, methods=['get'], url_path='me')
    def get_my_profile(self, request):
        """Get the authenticated user's referrer profile"""
        try:
            profile = ReferrerProfile.objects.select_related('user').get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except ReferrerProfile.DoesNotExist:
            return Response(
                {'detail': 'You do not have a referrer profile yet.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['patch', 'put'], url_path='me/update')
    def update_my_profile(self, request):
        """Update the authenticated user's referrer profile"""
        try:
            profile = ReferrerProfile.objects.get(user=request.user)
        except ReferrerProfile.DoesNotExist:
            return Response(
                {'detail': 'You do not have a referrer profile yet.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        partial = request.method == 'PATCH'
        serializer = self.get_serializer(profile, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PromotionalMediaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for promotional media.
    
    - list: Authenticated users can view active media
    - retrieve: Authenticated users can view specific media
    - create/update/destroy: Admin only
    """
    serializer_class = PromotionalMediaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return active media for regular users, all media for admins"""
        user = self.request.user
        queryset = PromotionalMedia.objects.all()
        
        if not user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset.select_related('created_by')

    def get_permissions(self):
        """Admin-only for create, update, delete operations"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Set created_by to the current admin user"""
        serializer.save(created_by=self.request.user)


class SharePayloadViewSet(viewsets.ViewSet):
    """
    ViewSet for generating share payloads for referrers.
    
    Returns promotional media, marketing text, and WhatsApp deep link
    with the referrer's code embedded.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='generate')
    def generate_payload(self, request):
        """
        Generate complete share payload for the authenticated referrer.
        
        Returns:
        - promotional_media: List of active promotional media
        - referral_code: User's unique referral code
        - whatsapp_link: WhatsApp deep link with pre-filled message
        - share_message: Combined marketing text with referral code
        """
        # Get user's referrer profile
        try:
            profile = ReferrerProfile.objects.select_related('user').get(
                user=request.user,
                is_active=True
            )
        except ReferrerProfile.DoesNotExist:
            return Response(
                {'detail': 'You do not have an active referrer profile. Please create one first.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get active promotional media
        media = PromotionalMedia.objects.filter(is_active=True).order_by('order', '-created_at')
        
        # Build share message
        share_message = self._build_share_message(media, profile.referral_code)
        
        # Generate WhatsApp deep link
        whatsapp_link = self._generate_whatsapp_link(share_message)
        
        # Prepare response
        payload = {
            'promotional_media': PromotionalMediaSerializer(media, many=True).data,
            'referral_code': profile.referral_code,
            'whatsapp_link': whatsapp_link,
            'share_message': share_message,
        }
        
        serializer = SharePayloadSerializer(payload)
        return Response(payload)

    def _build_share_message(self, media, referral_code):
        """Build the complete share message with marketing text and referral code"""
        # Combine marketing texts from all active media
        marketing_texts = [m.marketing_text for m in media if m.marketing_text]
        
        if marketing_texts:
            base_message = '\n\n'.join(marketing_texts)
        else:
            base_message = (
                "🎯 Check out JMW Accessories for quality NYSC uniforms, "
                "church merchandise, and more!"
            )
        
        # Append referral code
        message = f"{base_message}\n\n💎 Use my referral code: {referral_code}"
        
        return message

    def _generate_whatsapp_link(self, message):
        """
        Generate WhatsApp deep link with pre-filled message.
        
        WhatsApp API format:
        https://wa.me/?text=<URL_ENCODED_MESSAGE>
        
        Or for specific number:
        https://wa.me/2348012345678?text=<URL_ENCODED_MESSAGE>
        """
        whatsapp_number = getattr(settings, 'WHATSAPP_NUMBER', '2348012345678')
        # URL encode the message
        encoded_message = quote(message)
        
        # Generate deep link (without specific number, user can choose contact)
        whatsapp_link = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
        
        return whatsapp_link