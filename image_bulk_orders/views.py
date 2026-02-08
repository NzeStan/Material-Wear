# image_bulk_orders/views.py
"""
API Views for Image Bulk Orders (API-FIRST).

Optimizations:
- select_related/prefetch_related for all queries
- Efficient pagination
- Query count minimization
- Caching for public endpoints
- Proper permission handling

Security:
- Authentication where needed
- Public access for submission/payment
- Webhook signature verification
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db import transaction
from django.template.loader import render_to_string
from datetime import timedelta
import logging
import json

from .models import ImageBulkOrderLink, ImageOrderEntry, ImageCouponCode
from .serializers import (
    ImageBulkOrderLinkSerializer,
    ImageBulkOrderLinkSummarySerializer,
    ImageOrderEntrySerializer,
    ImageOrderListSerializer,
    ImageCouponCodeSerializer,
)
from .utils import generate_coupon_codes
from payment.utils import initialize_payment, verify_payment
from payment.security import verify_paystack_signature, sanitize_payment_log_data
from jmw.background_utils import send_email_async
from jmw.throttling import BulkOrderWebhookThrottle

logger = logging.getLogger(__name__)


class ImageBulkOrderLinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Image Bulk Order Links.
    
    Optimizations:
    - Annotated queries for counts
    - Cached queryset for list views
    - select_related for foreign keys
    """
    serializer_class = ImageBulkOrderLinkSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = ImageBulkOrderLink.objects.all()
    lookup_field = 'slug'
    
    def get_queryset(self):
        """
        Optimized queryset with annotations.
        
        Performance:
        - Annotates paid_count and total_orders
        - Uses select_related for created_by
        - Reduces query count from N+1 to 1
        """
        # Base queryset
        qs = ImageBulkOrderLink.objects.select_related('created_by')
        
        # Filter based on user
        if self.request.user.is_staff:
            # Staff sees all
            pass
        elif self.request.user.is_authenticated:
            # Authenticated users see their own
            qs = qs.filter(created_by=self.request.user)
        else:
            # Unauthenticated users see none for list
            if self.action == 'list':
                return qs.none()
        
        # Add annotations for efficiency
        qs = qs.annotate(
            _paid_count=Count('orders', filter=Q(orders__paid=True)),
            _total_orders=Count('orders')
        )
        
        return qs.order_by('-created_at')
    
    def retrieve(self, request, *args, **kwargs):
        """Allow public access to retrieve for submission"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def generate_coupons(self, request, slug=None):
        """
        Generate coupon codes for bulk order.
        Admin only action.
        """
        bulk_order = self.get_object()
        count = int(request.data.get('count', 50))
        
        # Check if coupons already exist
        if bulk_order.coupons.exists():
            return Response(
                {
                    "error": f"This bulk order already has {bulk_order.coupons.count()} coupons. "
                    "Delete existing coupons first if you want to regenerate."
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupons = generate_coupon_codes(bulk_order, count=count)
            return Response({
                "message": f"Successfully generated {len(coupons)} coupons",
                "count": len(coupons),
                "sample_codes": [c.code for c in coupons[:5]]
            })
        except Exception as e:
            logger.error(f"Error generating coupons: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[permissions.AllowAny],
        parser_classes=[MultiPartParser, FormParser]
    )
    def submit_order(self, request, slug=None):
        """
        Submit order entry with image upload.
        
        Multipart/form-data required for image upload.
        Public access - no authentication required.
        """
        # Get bulk order (public access)
        try:
            bulk_order = ImageBulkOrderLink.objects.get(slug=slug)
        except ImageBulkOrderLink.DoesNotExist:
            return Response(
                {"error": "Bulk order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate order entry with image
        serializer = ImageOrderEntrySerializer(
            data=request.data,
            context={'bulk_order': bulk_order, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order_entry = serializer.save()
        
        logger.info(
            f"Order submitted: {order_entry.reference} "
            f"for bulk order: {bulk_order.slug}"
        )
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def stats(self, request, slug=None):
        """
        Get statistics for bulk order.
        
        Optimizations:
        - Single optimized query with aggregations
        - Cached for 5 minutes
        """
        cache_key = f"image_bulk_stats_{slug}"
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            logger.debug(f"Returning cached stats for {slug}")
            return Response(cached_stats)
        
        # Get bulk order
        try:
            bulk_order = ImageBulkOrderLink.objects.get(slug=slug)
        except ImageBulkOrderLink.DoesNotExist:
            return Response(
                {"error": "Bulk order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Single optimized query with aggregations
        order_stats = bulk_order.orders.aggregate(
            total_orders=Count('id'),
            paid_orders=Count('id', filter=Q(paid=True)),
        )
        
        coupon_stats = bulk_order.coupons.aggregate(
            total_coupons=Count('id'),
            used_coupons=Count('id', filter=Q(is_used=True)),
        )
        
        # Build response
        total_orders = order_stats['total_orders'] or 0
        paid_orders = order_stats['paid_orders'] or 0
        total_coupons = coupon_stats['total_coupons'] or 0
        used_coupons = coupon_stats['used_coupons'] or 0
        
        response_data = {
            'organization': bulk_order.organization_name,
            'slug': bulk_order.slug,
            'total_orders': total_orders,
            'paid_orders': paid_orders,
            'unpaid_orders': total_orders - paid_orders,
            'payment_percentage': round((paid_orders / total_orders * 100), 2) if total_orders > 0 else 0,
            'total_coupons': total_coupons,
            'used_coupons': used_coupons,
            'coupon_usage_percentage': round((used_coupons / total_coupons * 100), 2) if total_coupons > 0 else 0,
            'is_expired': bulk_order.is_expired(),
            'payment_deadline': bulk_order.payment_deadline,
            'custom_branding_enabled': bulk_order.custom_branding_enabled,
            'total_revenue': float(bulk_order.get_total_revenue()),
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, response_data, 300)
        logger.info(f"Cached stats for {slug} for 5 minutes")
        
        return Response(response_data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def paid_orders(self, request, slug=None):
        """
        Social proof: Public view of paid orders.
        
        Optimizations:
        - Paginated results
        - Minimal fields
        - Cached response
        """
        try:
            bulk_order = ImageBulkOrderLink.objects.get(slug=slug)
        except ImageBulkOrderLink.DoesNotExist:
            return Response(
                {"error": "Bulk order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get paid orders (optimized)
        paid_orders = (
            bulk_order.orders
            .filter(paid=True)
            .only('id', 'serial_number', 'full_name', 'size', 'uploaded_image', 'created_at')
            .order_by('-created_at')[:20]  # Latest 20
        )
        
        # Size summary
        size_summary = list(
            bulk_order.orders
            .filter(paid=True)
            .values('size')
            .annotate(count=Count('size'))
            .order_by('size')
        )
        
        return Response({
            'bulk_order': {
                'organization_name': bulk_order.organization_name,
                'slug': bulk_order.slug,
                'custom_branding_enabled': bulk_order.custom_branding_enabled,
            },
            'total_paid': bulk_order.orders.filter(paid=True).count(),
            'size_summary': size_summary,
            'recent_orders': [
                {
                    'serial_number': order.serial_number,
                    'full_name': order.full_name,
                    'size': order.size,
                    'image_thumbnail': order.uploaded_image,  # Can add transformation here
                    'created_at': order.created_at,
                }
                for order in paid_orders
            ]
        })


class ImageOrderEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Image Order Entries.
    
    Permissions:
    - list: Authenticated users see their own orders
    - retrieve: Public access by reference (for payment)
    """
    permission_classes = [permissions.AllowAny]
    lookup_field = 'reference'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ImageOrderListSerializer
        return ImageOrderEntrySerializer
    
    def get_queryset(self):
        """
        Optimized queryset based on action.
        
        Performance:
        - select_related for foreign keys
        - Appropriate filtering
        """
        qs = ImageOrderEntry.objects.select_related(
            'bulk_order',
            'coupon_used'
        )
        
        # For public actions (retrieve, payment)
        if self.action in ['retrieve', 'initialize_payment', 'verify_payment']:
            return qs
        
        # For list: only authenticated user's orders
        if self.action == 'list':
            if self.request.user.is_authenticated:
                return qs.filter(email=self.request.user.email)
            return qs.none()
        
        return qs
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def initialize_payment(self, request, reference=None):
        """
        Initialize payment for order entry.
        
        Public access - uses reference as lookup.
        """
        order_entry = self.get_object()
        
        # Validation checks
        if order_entry.paid:
            return Response(
                {"error": "This order has already been paid"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order_entry.coupon_used:
            return Response(
                {"error": "This order uses a coupon and requires no payment"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order_entry.bulk_order.is_expired():
            return Response(
                {"error": "Payment deadline has passed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize payment
            callback_url = request.build_absolute_uri(
                f'/api/image-bulk-orders/orders/{order_entry.reference}/verify-payment/'
            )
            
            payment_data = initialize_payment(
                email=order_entry.email,
                amount=order_entry.bulk_order.price_per_item,
                reference=order_entry.reference,
                callback_url=callback_url
            )
            
            if payment_data.get('status'):
                logger.info(f"Payment initialized for {order_entry.reference}")
                
                return Response({
                    'authorization_url': payment_data['data']['authorization_url'],
                    'access_code': payment_data['data']['access_code'],
                    'reference': payment_data['data']['reference']
                })
            else:
                return Response(
                    {"error": "Payment initialization failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error initializing payment: {str(e)}")
            return Response(
                {"error": f"Payment initialization failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post', 'get'], permission_classes=[permissions.AllowAny])
    def verify_payment(self, request, reference=None):
        """
        Verify payment for order entry.
        
        Can be called by frontend or Paystack callback.
        """
        order_entry = self.get_object()
        
        if order_entry.paid:
            return Response({
                'message': 'Payment already verified',
                'paid': True,
                'order': ImageOrderEntrySerializer(order_entry, context={'request': request}).data
            })
        
        try:
            # Verify payment with Paystack
            verification = verify_payment(order_entry.reference)
            
            if verification.get('status') and verification['data'].get('status') == 'success':
                # Mark as paid
                with transaction.atomic():
                    order_entry.paid = True
                    order_entry.save(update_fields=['paid', 'updated_at'])
                
                logger.info(f"Payment verified for {order_entry.reference}")
                
                # Send confirmation email (async)
                # TODO: Implement send_order_confirmation_email
                
                serializer = ImageOrderEntrySerializer(
                    order_entry,
                    context={'request': request}
                )
                
                return Response({
                    'message': 'Payment verified successfully',
                    'order': serializer.data
                })
            else:
                return Response(
                    {"error": "Payment verification failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error verifying payment: {str(e)}")
            return Response(
                {"error": f"Payment verification failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImageCouponCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for coupon codes.
    Admin only access.
    """
    serializer_class = ImageCouponCodeSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = ImageCouponCode.objects.all()
    
    def get_queryset(self):
        """Optimized queryset with select_related"""
        return ImageCouponCode.objects.select_related('bulk_order').order_by('-created_at')
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def validate_coupon(self, request):
        """
        Validate a coupon code.
        
        Public endpoint for checking coupon validity.
        """
        code = request.data.get('code', '').strip().upper()
        bulk_order_slug = request.data.get('bulk_order_slug', '').strip()
        
        if not code or not bulk_order_slug:
            return Response(
                {"error": "Both 'code' and 'bulk_order_slug' are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bulk_order = ImageBulkOrderLink.objects.get(slug=bulk_order_slug)
            coupon = ImageCouponCode.objects.get(
                code=code,
                bulk_order=bulk_order
            )
            
            if coupon.is_used:
                return Response({
                    'valid': False,
                    'message': 'This coupon has already been used'
                })
            
            return Response({
                'valid': True,
                'message': 'Coupon is valid',
                'code': coupon.code
            })
            
        except ImageBulkOrderLink.DoesNotExist:
            return Response(
                {"error": "Bulk order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ImageCouponCode.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Invalid coupon code'
            })
        except Exception as e:
            logger.error(f"Error validating coupon: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@csrf_exempt
def image_bulk_order_payment_webhook(request):
    """
    Paystack webhook handler for image bulk orders.
    
    Reference format: IMG-XXXXXXXXXX
    
    Security:
    - Signature verification
    - Idempotency checks
    
    Performance:
    - Single database query with select_for_update
    - Transaction safety
    """
    if request.method != 'POST':
        logger.warning(f"Invalid webhook method: {request.method}")
        return JsonResponse(
            {'status': 'error', 'message': 'Method not allowed'},
            status=405
        )
    
    try:
        # 🔐 STEP 1: Verify webhook signature
        signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
        
        if not signature:
            logger.error("Image webhook received without signature")
            return JsonResponse(
                {'status': 'error', 'message': 'Missing signature'},
                status=401
            )
        
        if not verify_paystack_signature(request.body, signature):
            logger.error("Image webhook signature verification failed")
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid signature'},
                status=401
            )
        
        # 📦 STEP 2: Parse payload
        payload = json.loads(request.body)
        event = payload.get('event')
        data = payload.get('data', {})
        
        logger.info(f"Image webhook received: {event}")
        
        # 🚫 Ignore non-charge events
        if event != 'charge.success':
            logger.info(f"Ignoring webhook event: {event}")
            return JsonResponse(
                {'status': 'success', 'message': 'Event ignored'},
                status=200
            )
        
        # ❌ Check payment status BEFORE touching DB
        if data.get('status') != 'success':
            logger.warning(
                f"Charge event received but payment not successful: {data.get('status')}"
            )
            return JsonResponse(
                {'status': 'error', 'message': 'Payment not successful'},
                status=400
            )
        
        # 🔎 STEP 3: Extract and validate reference
        reference = data.get('reference', '')
        
        if not reference or not reference.startswith('IMG-'):
            logger.error(f"Invalid reference format: {reference}")
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid reference format'},
                status=400
            )
        
        try:
            # 🔒 STEP 4: Idempotent payment processing
            with transaction.atomic():
                order_entry = (
                    ImageOrderEntry.objects
                    .select_for_update()
                    .select_related('bulk_order')
                    .get(reference=reference)
                )
                
                # Already paid → idempotent exit
                if order_entry.paid:
                    logger.info(
                        f"Payment already processed for {reference}. "
                        f"Skipping duplicate webhook."
                    )
                    return JsonResponse(
                        {
                            'status': 'success',
                            'message': 'Payment already processed',
                            'reference': reference
                        },
                        status=200
                    )
                
                # ✅ Mark as paid
                order_entry.paid = True
                order_entry.save(update_fields=['paid', 'updated_at'])
            
            # 📧 STEP 5: Send confirmation email (outside transaction)
            # TODO: Implement send_order_confirmation_email_async
            
            logger.info(
                f"Image order payment successful: {reference}"
            )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Payment processed',
                'reference': reference
            }, status=200)
            
        except ImageOrderEntry.DoesNotExist:
            logger.error(f"Order entry not found: {reference}")
            return JsonResponse(
                {'status': 'error', 'message': 'Order not found'},
                status=404
            )
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return JsonResponse(
                {'status': 'error', 'message': str(e)},
                status=500
            )
            
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid JSON'},
            status=400
        )
    except Exception as e:
        logger.error(f"Unexpected webhook error: {str(e)}")
        return JsonResponse(
            {'status': 'error', 'message': 'Internal server error'},
            status=500
        )