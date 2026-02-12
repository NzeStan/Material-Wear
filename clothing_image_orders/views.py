# clothing_image_orders/views.py
"""
Views for clothing image orders API.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.db.models import Q
from decimal import Decimal
import logging
import hmac
import hashlib

from .models import ClothingImageOrder, ClothingOrderParticipant, ClothingCouponCode
from .serializers import (
    ClothingImageOrderListSerializer,
    ClothingImageOrderDetailSerializer,
    ClothingImageOrderCreateSerializer,
    ClothingOrderParticipantListSerializer,
    ClothingOrderParticipantDetailSerializer,
    ClothingOrderParticipantCreateSerializer,
    ClothingCouponCodeSerializer,
    ParticipantPaymentInitializeSerializer,
    ParticipantPaymentVerifySerializer,
)
from .utils import initialize_payment, verify_payment

logger = logging.getLogger(__name__)


class ClothingImageOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing clothing image orders.
    
    List/Create: Admin only
    Retrieve: Public (by reference)
    Update/Delete: Admin only
    """
    
    lookup_field = 'reference'
    lookup_value_regex = '[A-Z0-9-]+'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ClothingImageOrderCreateSerializer
        elif self.action == 'list':
            return ClothingImageOrderListSerializer
        return ClothingImageOrderDetailSerializer
    
    def get_permissions(self):
        """Set permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'generate_coupons']:
            return [permissions.IsAdminUser()]
        elif self.action in ['list']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        """Return orders based on user permissions"""
        if self.request.user.is_staff:
            return ClothingImageOrder.objects.all().prefetch_related('participants', 'coupons')
        
        # Public users can only see active orders
        return ClothingImageOrder.objects.filter(is_active=True)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def submit_participant(self, request, reference=None):
        """
        Submit a new participant to this order - PUBLIC ENDPOINT
        
        Participants can submit themselves with:
        - Personal details
        - Size selection
        - Image upload (optional/required based on order)
        - Custom name (optional)
        - Coupon code (optional)
        """
        order = self.get_object()
        
        serializer = ClothingOrderParticipantCreateSerializer(
            data=request.data,
            context={'order': order, 'request': request}
        )
        
        if serializer.is_valid():
            participant = serializer.save()
            
            # Return detailed participant data
            return Response(
                ClothingOrderParticipantDetailSerializer(participant).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def generate_coupons(self, request, reference=None):
        """
        Generate coupon codes for this order - ADMIN ONLY
        
        Request body: {"count": 50}
        """
        from .utils import generate_clothing_coupon_codes
        
        order = self.get_object()
        count = request.data.get('count', 50)
        
        try:
            count = int(count)
            if count < 1 or count > 500:
                return Response(
                    {"error": "Count must be between 1 and 500"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError):
            return Response(
                {"error": "Invalid count parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupons = generate_clothing_coupon_codes(order, count=count)
            
            logger.info(f"Generated {len(coupons)} coupons for {order.reference}")
            
            return Response({
                "message": f"Successfully generated {len(coupons)} coupon codes",
                "coupons": ClothingCouponCodeSerializer(coupons, many=True).data
            })
            
        except Exception as e:
            logger.error(f"Error generating coupons: {str(e)}")
            return Response(
                {"error": f"Error generating coupons: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def stats(self, request, reference=None):
        """
        Get statistics for this order - PUBLIC
        """
        order = self.get_object()
        participants = order.participants.all()
        
        # Size breakdown
        size_breakdown = {}
        for size_choice in ClothingOrderParticipant.SIZE_CHOICES:
            size_code = size_choice[0]
            count = participants.filter(size=size_code).count()
            if count > 0:
                size_breakdown[size_code] = count
        
        stats = {
            'total_participants': participants.count(),
            'paid_participants': participants.filter(paid=True).count(),
            'pending_participants': participants.filter(paid=False).count(),
            'with_images': participants.exclude(image='').count(),
            'with_coupons': participants.filter(coupon_used__isnull=False).count(),
            'size_breakdown': size_breakdown,
        }
        
        return Response(stats)


class ClothingOrderParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for participants.
    
    List: Filter by email (authenticated users see their own)
    Retrieve: Public (by reference)
    """
    
    serializer_class = ClothingOrderParticipantDetailSerializer
    lookup_field = 'reference'
    lookup_value_regex = '[A-Z0-9-]+'
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """Return participants based on user and filters"""
        queryset = ClothingOrderParticipant.objects.select_related(
            'order', 'coupon_used'
        ).prefetch_related('order__coupons')
        
        # Filter by email if provided
        email = self.request.query_params.get('email')
        if email:
            queryset = queryset.filter(email__iexact=email)
        
        # Filter by order reference
        order_ref = self.request.query_params.get('order')
        if order_ref:
            queryset = queryset.filter(order__reference=order_ref)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        """Use list serializer for list action"""
        if self.action == 'list':
            return ClothingOrderParticipantListSerializer
        return ClothingOrderParticipantDetailSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def initialize_payment(self, request, reference=None):
        """
        Initialize payment for a participant - PUBLIC ENDPOINT
        
        Optional request body: {"callback_url": "https://..."}
        """
        participant = self.get_object()
        
        # Check if already paid
        if participant.paid:
            return Response(
                {"error": "This participant has already paid"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if using coupon (no payment needed)
        if participant.coupon_used:
            return Response(
                {"error": "This participant is using a coupon and doesn't need to pay"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate payment reference
        payment_ref = f"CLO-PAY-{participant.order.id}-{participant.id}"
        
        # Calculate amount
        amount = participant.order.price_per_item
        email = participant.email
        
        # Get callback URL
        callback_url = request.data.get('callback_url')
        if not callback_url:
            callback_url = f"{settings.FRONTEND_URL}/payment/verify"
        
        # Initialize payment with Paystack
        result = initialize_payment(amount, email, payment_ref, callback_url)
        
        if result and result.get('status'):
            logger.info(
                f"Payment initialized for participant {participant.reference}: {payment_ref}"
            )
            
            return Response({
                "authorization_url": result['data']['authorization_url'],
                "access_code": result['data']['access_code'],
                "reference": payment_ref,
                "participant_reference": participant.reference,
                "amount": float(amount),
                "email": email
            })
        
        logger.error(f"Payment initialization failed for participant {participant.reference}")
        return Response(
            {"error": "Payment initialization failed. Please try again."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def verify_payment(self, request, reference=None):
        """
        Verify payment status for a participant - PUBLIC ENDPOINT
        
        Frontend calls this after Paystack redirect
        """
        participant = self.get_object()
        
        return Response({
            "paid": participant.paid,
            "reference": participant.reference,
            "full_name": participant.full_name,
            "amount": float(participant.order.price_per_item),
            "payment_date": participant.payment_date.isoformat() if participant.payment_date else None,
            "participant_id": str(participant.id)
        })


class ClothingCouponCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for coupon codes - ADMIN ONLY
    """
    
    serializer_class = ClothingCouponCodeSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Return coupons with optional filters"""
        queryset = ClothingCouponCode.objects.select_related('order')
        
        # Filter by order reference
        order_ref = self.request.query_params.get('order')
        if order_ref:
            queryset = queryset.filter(order__reference=order_ref)
        
        # Filter by usage
        is_used = self.request.query_params.get('is_used')
        if is_used is not None:
            queryset = queryset.filter(is_used=is_used.lower() == 'true')
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def validate_coupon(self, request, pk=None):
        """
        Validate a coupon code - PUBLIC
        
        Request body: {"order_reference": "CLO-XXXXX"}
        """
        coupon = self.get_object()
        order_ref = request.data.get('order_reference')
        
        if not order_ref:
            return Response(
                {"error": "order_reference is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if coupon belongs to this order
        if coupon.order.reference != order_ref:
            return Response(
                {"valid": False, "message": "Coupon code does not belong to this order"}
            )
        
        # Check if already used
        if coupon.is_used:
            return Response(
                {"valid": False, "message": "This coupon code has already been used"}
            )
        
        return Response({
            "valid": True,
            "message": "Coupon code is valid",
            "discount": float(coupon.order.price_per_item)
        })


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def clothing_payment_webhook(request):
    """
    Webhook endpoint for Paystack payment notifications.
    
    This is called by Paystack when payment status changes.
    """
    # Verify webhook signature
    signature = request.headers.get('x-paystack-signature')
    
    if not signature:
        logger.warning("Webhook received without signature")
        return HttpResponse(status=400)
    
    # Verify signature
    secret = settings.PAYSTACK_SECRET_KEY.encode('utf-8')
    body = request.body
    computed_signature = hmac.new(secret, body, hashlib.sha512).hexdigest()
    
    if computed_signature != signature:
        logger.warning("Invalid webhook signature")
        return HttpResponse(status=400)
    
    # Process webhook data
    data = request.data
    event = data.get('event')
    
    if event == 'charge.success':
        payment_data = data.get('data', {})
        reference = payment_data.get('reference')
        
        if not reference or not reference.startswith('CLO-PAY-'):
            logger.warning(f"Invalid payment reference: {reference}")
            return HttpResponse(status=200)
        
        try:
            # Extract participant ID from reference
            # Format: CLO-PAY-{order_id}-{participant_id}
            parts = reference.split('-')
            if len(parts) >= 4:
                participant_id = parts[3]
                
                participant = ClothingOrderParticipant.objects.get(id=participant_id)
                
                # Check if already paid (idempotency)
                if not participant.paid:
                    from django.utils import timezone
                    
                    participant.paid = True
                    participant.payment_reference = reference
                    participant.payment_date = timezone.now()
                    participant.save()
                    
                    logger.info(f"Payment confirmed for participant: {participant.reference}")
                
                return HttpResponse(status=200)
                
        except ClothingOrderParticipant.DoesNotExist:
            logger.error(f"Participant not found for reference: {reference}")
            return HttpResponse(status=404)
        
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return HttpResponse(status=500)
    
    return HttpResponse(status=200)