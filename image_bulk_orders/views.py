# image_bulk_orders/views.py
"""
Views for Image Bulk Orders app.

Enhancements:
- Payment webhook routes through webhook_router
- Email notifications for order confirmation and payment
- Social proof paid_orders view
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, throttle_classes as apply_throttle_classes
from rest_framework.response import Response
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Q
from django.core.cache import cache
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from jmw.throttling import BulkOrderWebhookThrottle
from payment.utils import initialize_payment
from payment.security import verify_paystack_signature, sanitize_payment_log_data
from .models import ImageBulkOrderLink, ImageCouponCode, ImageOrderEntry
from .serializers import (
    ImageBulkOrderLinkSerializer,
    ImageBulkOrderLinkSummarySerializer,
    ImageCouponCodeSerializer,
    ImageOrderEntrySerializer,
)
from .utils import generate_coupon_codes_image
import json
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class ImageBulkOrderLinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Image Bulk Order Links
    IDENTICAL to BulkOrderLinkViewSet with image support
    """
    serializer_class = ImageBulkOrderLinkSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'slug'
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ImageBulkOrderLink.objects.all().prefetch_related('orders', 'coupons')
        return ImageBulkOrderLink.objects.filter(
            created_by=self.request.user
        ).prefetch_related('orders', 'coupons')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ImageBulkOrderLinkSummarySerializer
        return ImageBulkOrderLinkSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def generate_coupons(self, request, slug=None):
        """Generate coupon codes for this bulk order"""
        bulk_order = self.get_object()
        count = request.data.get('count', 10)
        
        try:
            count = int(count)
            if count < 1 or count > 100:
                return Response(
                    {"error": "Count must be between 1 and 100"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid count value"},
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
        
        stats = {
            **order_stats,
            **coupon_stats,
            'organization_name': bulk_order.organization_name,
            'price_per_item': str(bulk_order.price_per_item),
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, stats, 300)
        
        return Response(stats)

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def paid_orders(self, request, slug=None):
        """
        Public page showing all paid orders for social proof.
        Supports HTML view and PDF download.
        """
        try:
            # Allow public access - get object directly by slug
            try:
                bulk_order = ImageBulkOrderLink.objects.get(slug=slug)
            except ImageBulkOrderLink.DoesNotExist:
                return Response(
                    {"error": "Bulk order not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get only PAID orders
            paid_orders = bulk_order.orders.filter(paid=True).order_by('-created_at')
            
            # Size summary
            size_summary = list(
                paid_orders.values("size")
                .annotate(count=Count("size"))
                .order_by("size")
            )
            
            # Check if download=pdf parameter
            if request.GET.get('download') == 'pdf':
                try:
                    from weasyprint import HTML
                    
                    context = {
                        'bulk_order': bulk_order,
                        'size_summary': size_summary,
                        'paid_orders': paid_orders,
                        'total_paid': paid_orders.count(),
                        'company_name': settings.COMPANY_NAME,
                        'company_address': settings.COMPANY_ADDRESS,
                        'company_phone': settings.COMPANY_PHONE,
                        'company_email': settings.COMPANY_EMAIL,
                        'now': timezone.now(),
                    }
                    
                    html_string = render_to_string('image_bulk_orders/pdf_template.html', context)
                    html = HTML(string=html_string, base_url=request.build_absolute_uri())
                    pdf = html.write_pdf()
                    
                    from django.http import HttpResponse
                    response = HttpResponse(pdf, content_type='application/pdf')
                    filename = f'completed_orders_{bulk_order.slug}.pdf'
                    response['Content-Disposition'] = f'attachment; filename="{filename}"'
                    
                    logger.info(f"Generated public paid orders PDF for: {bulk_order.slug}")
                    return response
                    
                except ImportError:
                    return Response(
                        {"error": "PDF generation not available"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                except Exception as e:
                    logger.error(f"Error generating PDF: {str(e)}", exc_info=True)
                    return Response(
                        {"error": f"PDF generation failed: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # HTML view
            now = timezone.now()
            
            # Calculate days remaining safely
            try:
                if bulk_order.payment_deadline > now:
                    days_remaining = (bulk_order.payment_deadline - now).days
                else:
                    days_remaining = 0
            except TypeError:
                # Handle timezone-naive comparison
                logger.warning(f"Timezone issue with payment_deadline for {bulk_order.slug}")
                days_remaining = 0
            
            context = {
                'bulk_order': bulk_order,
                'size_summary': size_summary,
                'paid_orders': paid_orders,
                'total_paid': paid_orders.count(),
                'recent_orders': list(paid_orders[:20]),  # Convert to list
                'company_name': settings.COMPANY_NAME,
                'now': now,
                'days_remaining': days_remaining,
            }
            
            return render(request, 'image_bulk_orders/paid_orders_public.html', context)
        
        except Exception as e:
            logger.error(f"Error in paid_orders view: {str(e)}", exc_info=True)
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ImageOrderEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Image Order Entries
    IDENTICAL to OrderEntryViewSet from bulk_orders
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
        
        return ImageOrderEntry.objects.all().select_related('bulk_order', 'coupon_used')
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def initialize_payment(self, request, pk=None):
        """Initialize payment for this order entry"""
        order_entry = self.get_object()
        
        # ✅ Check if coupon was used (already paid)
        if order_entry.paid:
            return Response(
                {"error": "This order has already been paid for."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize Paystack payment
            result = initialize_payment(
                amount=order_entry.bulk_order.price_per_item,
                email=order_entry.email,
                reference=order_entry.reference,
                callback_url=request.data.get('callback_url')
            )
            
            if result and result.get('status'):
                return Response({
                    "authorization_url": result['data']['authorization_url'],
                    "reference": result['data']['reference'],
                    "order_reference": order_entry.reference,
                    "amount": float(order_entry.bulk_order.price_per_item)
                })
            else:
                return Response(
                    {"error": "Failed to initialize payment"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Payment initialization error: {str(e)}")
            return Response(
                {"error": "Payment initialization failed. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def verify_payment(self, request, pk=None):
        """Verify payment status for an ImageOrderEntry - PUBLIC ENDPOINT"""
        order_entry = self.get_object()
        
        return Response({
            "order_id": str(order_entry.id),
            "reference": order_entry.reference,
            "paid": order_entry.paid,
            "amount": float(order_entry.bulk_order.price_per_item),
            "email": order_entry.email,
            "full_name": order_entry.full_name,
            "organization": order_entry.bulk_order.organization_name,
            "has_image": bool(order_entry.image),
            "created_at": order_entry.created_at,
            "updated_at": order_entry.updated_at,
        })


class ImageCouponCodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for coupon codes.
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


# ============================================================================
# WEBHOOK HANDLER (Routes through webhook_router)
# ============================================================================

@apply_throttle_classes([BulkOrderWebhookThrottle])
@csrf_exempt
def image_bulk_order_payment_webhook(request):
    """
    Paystack webhook handler for image bulk order payments.
    Reference format: IMG-BULK-xxxx
    
    ✅ UPDATED: Now routes through webhook_router
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
        
        # ✅ Send payment receipt email (async)
        from jmw.background_utils import send_image_payment_receipt_email
        send_image_payment_receipt_email(order_entry)
        
        logger.info(f"Payment processed successfully for: {reference}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Payment processed successfully'
        }, status=200)
        
    except ImageOrderEntry.DoesNotExist:
        logger.error(f"Order entry not found for reference: {reference}")
        return JsonResponse({'error': 'Order not found'}, status=404)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)