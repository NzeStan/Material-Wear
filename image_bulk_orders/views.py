# image_bulk_orders/views.py
"""
Views for Image Bulk Orders app.

EXACT CLONE of bulk_orders views with image handling.
Reference format: IMG-BULK-xxxx
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, throttle_classes as apply_throttle_classes
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.conf import settings
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.core.cache import cache
import json
import logging

from .models import ImageBulkOrderLink, ImageOrderEntry, ImageCouponCode
from .serializers import (
    ImageBulkOrderLinkSerializer,
    ImageOrderEntrySerializer,
    ImageCouponCodeSerializer
)
from payment.security import verify_paystack_signature
from payment.utils import initialize_payment, verify_payment
from .utils import (
    generate_coupon_codes_image,
    generate_image_bulk_order_pdf,
    generate_image_bulk_order_word,
    generate_image_bulk_order_excel,
)
from jmw.background_utils import send_email_async
from jmw.throttling import BulkOrderWebhookThrottle

logger = logging.getLogger(__name__)


class ImageBulkOrderLinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for image bulk order links.
    IDENTICAL to BulkOrderLinkViewSet from bulk_orders.
    """
    
    serializer_class = ImageBulkOrderLinkSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = ImageBulkOrderLink.objects.all()
    lookup_field = 'slug'

    def get_queryset(self):
        if self.request.user.is_staff:
            return ImageBulkOrderLink.objects.all()
        if self.request.user.is_authenticated:
            return ImageBulkOrderLink.objects.filter(created_by=self.request.user)
        return ImageBulkOrderLink.objects.none()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def generate_coupons(self, request, slug=None):
        """Generate coupons for an image bulk order"""
        bulk_order = self.get_object()
        count = int(request.data.get('count', 50))
        
        if bulk_order.coupons.count() > 0:
            return Response(
                {"error": f"This bulk order already has {bulk_order.coupons.count()} coupons."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        coupons = generate_coupon_codes_image(bulk_order, count=count)
        
        return Response({
            "message": f"Successfully generated {len(coupons)} coupon codes",
            "count": len(coupons)
        })

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def submit_order(self, request, slug=None):
        """
        Submit order for this bulk order (with optional image).
        Public endpoint - no auth required.
        """
        try:
            bulk_order = ImageBulkOrderLink.objects.get(slug=slug)
        except ImageBulkOrderLink.DoesNotExist:
            return Response(
                {"error": "Bulk order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ImageOrderEntrySerializer(
            data=request.data,
            context={'bulk_order': bulk_order, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order_entry = serializer.save()
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def stats(self, request, slug=None):
        """Get statistics for an image bulk order (with caching)"""
        cache_key = f"image_bulk_order_stats_{slug}"
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)
        
        try:
            bulk_order = ImageBulkOrderLink.objects.get(slug=slug)
        except ImageBulkOrderLink.DoesNotExist:
            return Response(
                {"error": "Bulk order not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        order_stats = bulk_order.orders.aggregate(
            total_orders=Count('id'),
            paid_orders=Count('id', filter=Q(paid=True)),
        )
        
        coupon_stats = bulk_order.coupons.aggregate(
            total_coupons=Count('id'),
            used_coupons=Count('id', filter=Q(is_used=True)),
        )
        
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
        }
        
        cache.set(cache_key, response_data, 300)  # 5 minutes
        return Response(response_data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def download_pdf(self, request, slug=None):
        """Generate PDF summary"""
        try:
            return generate_image_bulk_order_pdf(slug, request)
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            return Response(
                {"error": f"Error generating PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def download_word(self, request, slug=None):
        """Generate Word document"""
        try:
            return generate_image_bulk_order_word(slug)
        except Exception as e:
            logger.error(f"Error generating Word: {str(e)}")
            return Response(
                {"error": f"Error generating Word: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def generate_size_summary(self, request, slug=None):
        """Generate Excel size summary"""
        try:
            return generate_image_bulk_order_excel(slug)
        except Exception as e:
            logger.error(f"Error generating Excel: {str(e)}")
            return Response(
                {"error": f"Error generating Excel: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImageOrderEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for image order entries.
    IDENTICAL to OrderEntryViewSet from bulk_orders.
    """
    
    serializer_class = ImageOrderEntrySerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        if self.action in ['initialize_payment', 'retrieve', 'verify_payment']:
            return ImageOrderEntry.objects.all().select_related('bulk_order', 'coupon_used')
        
        if self.action == 'list':
            if self.request.user.is_authenticated:
                return ImageOrderEntry.objects.filter(
                    email=self.request.user.email
                ).select_related('bulk_order', 'coupon_used')
            return ImageOrderEntry.objects.none()
        
        return ImageOrderEntry.objects.all()

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def initialize_payment(self, request, pk=None):
        """Initialize Paystack payment for this order"""
        order_entry = self.get_object()
        
        if order_entry.paid:
            return Response(
                {"error": "This order has already been paid for."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order_entry.coupon_used:
            return Response(
                {"error": "This order uses a coupon and doesn't require payment."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        callback_url = request.data.get('callback_url', settings.FRONTEND_URL)
        
        try:
            payment_data = initialize_payment(
                email=order_entry.email,
                amount=float(order_entry.bulk_order.price_per_item),
                reference=order_entry.reference,
                callback_url=callback_url
            )
            
            return Response({
                "authorization_url": payment_data['authorization_url'],
                "access_code": payment_data['access_code'],
                "reference": order_entry.reference,
                "order_reference": order_entry.reference
            })
        
        except Exception as e:
            logger.error(f"Payment initialization failed: {str(e)}")
            return Response(
                {"error": "Failed to initialize payment. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def verify_payment(self, request, pk=None):
        """Verify payment status for this order"""
        order_entry = self.get_object()
        
        return Response({
            "paid": order_entry.paid,
            "reference": order_entry.reference,
            "email": order_entry.email,
            "full_name": order_entry.full_name,
            "size": order_entry.size
        })


class ImageCouponCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for coupon codes (admin only).
    IDENTICAL to CouponCodeViewSet from bulk_orders.
    """
    
    serializer_class = ImageCouponCodeSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = ImageCouponCode.objects.all()
    
    def get_queryset(self):
        queryset = ImageCouponCode.objects.select_related('bulk_order')
        bulk_order_slug = self.request.query_params.get('bulk_order_slug')
        
        if bulk_order_slug:
            queryset = queryset.filter(bulk_order__slug=bulk_order_slug)
        
        return queryset


@apply_throttle_classes([BulkOrderWebhookThrottle])
@csrf_exempt
def image_bulk_order_payment_webhook(request):
    """
    Paystack webhook handler for image bulk order payments.
    Reference format: IMG-BULK-xxxx
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Verify signature
        signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
        if not signature or not verify_paystack_signature(request.body, signature):
            logger.error("Invalid webhook signature")
            return JsonResponse({'error': 'Invalid signature'}, status=401)
        
        payload = json.loads(request.body)
        event = payload.get('event')
        
        if event != 'charge.success':
            return JsonResponse({'status': 'ignored'}, status=200)
        
        data = payload.get('data', {})
        if data.get('status') != 'success':
            return JsonResponse({'error': 'Payment not successful'}, status=400)
        
        reference = data.get('reference', '')
        if not reference or not reference.startswith('IMG-BULK-'):
            logger.error(f"Invalid reference format: {reference}")
            return JsonResponse({'error': 'Invalid reference'}, status=400)
        
        # Idempotent payment processing
        with transaction.atomic():
            order_entry = (
                ImageOrderEntry.objects
                .select_for_update()
                .select_related('bulk_order')
                .get(reference=reference)
            )
            
            if order_entry.paid:
                logger.info(f"Payment already processed: {reference}")
                return JsonResponse({
                    'status': 'success',
                    'message': 'Payment already processed'
                }, status=200)
            
            order_entry.paid = True
            order_entry.save(update_fields=['paid', 'updated_at'])
        
        # Invalidate cache
        cache_key = f"image_bulk_order_stats_{order_entry.bulk_order.slug}"
        cache.delete(cache_key)
        
        # Send confirmation email (async)
        subject = f"Payment Confirmed - {order_entry.bulk_order.organization_name}"
        message = f"""
Dear {order_entry.full_name},

Your payment for {order_entry.bulk_order.organization_name} has been confirmed!

Order Details:
- Reference: {order_entry.reference}
- Size: {order_entry.get_size_display()}
- Serial Number: {order_entry.serial_number}

Thank you for your order!

Best regards,
{settings.COMPANY_NAME}
        """
        
        send_email_async(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order_entry.email]
        )
        
        logger.info(f"Payment processed successfully: {reference}")
        
        return JsonResponse({
            'status': 'success',
            'reference': reference
        }, status=200)
        
    except ImageOrderEntry.DoesNotExist:
        logger.error(f"Order not found for reference: {reference}")
        return JsonResponse({'error': 'Order not found'}, status=404)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        logger.exception("Webhook processing error")
        return JsonResponse({'error': 'Server error'}, status=500)
