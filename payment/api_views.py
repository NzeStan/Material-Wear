# payment/api_views.py
from rest_framework import views, viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import PaymentTransaction
from .serializers import (
    PaymentTransactionSerializer, InitiatePaymentSerializer,
    PaymentResponseSerializer, VerifyPaymentSerializer, PaymentStatusSerializer
)
from rest_framework.decorators import throttle_classes as apply_throttle_classes
from .utils import initialize_payment, verify_payment
from .security import verify_paystack_signature, sanitize_payment_log_data  # ✅ NEW
from order.models import BaseOrder
from jmw.background_utils import (
    send_payment_receipt_email_async, generate_payment_receipt_pdf_task
)
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from .serializers import WebhookSerializer
from jmw.throttling import PaymentRateThrottle
import uuid
import json
import logging

logger = logging.getLogger(__name__)


@extend_schema(tags=['Payment'])
class InitiatePaymentView(views.APIView):
    """
    Initialize payment for pending orders
    Uses order IDs stored in session from checkout
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [PaymentRateThrottle]
    @extend_schema(
        description="Initialize payment for orders in session. Returns Paystack authorization URL.",
        request=InitiatePaymentSerializer,
        responses={
            200: PaymentResponseSerializer,
            400: {'description': 'No pending orders or initialization failed'}
        }
    )
    def post(self, request):
        # Get pending orders from session
        order_ids = request.session.get('pending_orders', [])
        
        if not order_ids:
            return Response({
                'error': 'No pending orders found. Please complete checkout first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Convert string UUIDs to UUID objects and fetch orders
            orders = BaseOrder.objects.filter(
                id__in=[uuid.UUID(id_str) for id_str in order_ids],
                user=request.user
            )
            
            if not orders.exists():
                # Clear invalid session
                request.session.pop('pending_orders', None)
                return Response({
                    'error': 'Orders not found or do not belong to you.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # ✅ NEW: Validate order count matches session
            if orders.count() != len(order_ids):
                logger.warning(
                    f"Order count mismatch for user {request.user.id}. "
                    f"Requested: {len(order_ids)}, Found: {orders.count()}"
                )
                request.session.pop('pending_orders', None)
                return Response({
                    'error': 'Invalid order session. Please checkout again.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get first order for email
            first_order = orders.first()
            total_amount = sum(order.total_cost for order in orders)
            
            # Create payment transaction
            payment = PaymentTransaction.objects.create(
                amount=total_amount,
                email=first_order.email
            )
            payment.orders.set(orders)
            
            logger.info(
                f"Payment transaction created: {payment.reference} - "
                f"Amount: {total_amount} - User: {request.user.email}"
            )
            
            # Build callback URL
            callback_url = request.build_absolute_uri('/api/payment/verify/')
            
            # Initialize payment with Paystack
            response = initialize_payment(
                amount=payment.amount,
                email=payment.email,
                reference=payment.reference,
                callback_url=callback_url,
                metadata={
                    'orders': [str(order.id) for order in orders],
                    'customer_name': f"{first_order.first_name} {first_order.last_name}",
                    'user_id': str(request.user.id)
                }
            )
            
            if not response or not response.get('status'):
                logger.error(f"Payment initialization failed for user {request.user.id}")
                return Response({
                    'error': 'Could not initialize payment. Please try again.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Return authorization URL
            return Response({
                'authorization_url': response['data']['authorization_url'],
                'access_code': response['data']['access_code'],
                'reference': payment.reference,
                'amount': float(payment.amount)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception(f"Error initializing payment for user {request.user.id}")
            return Response({
                'error': 'An error occurred while processing payment. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=['Payment'])
class VerifyPaymentView(views.APIView):
    """
    Verify payment status
    Called after user completes payment on Paystack
    """
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        description="Verify payment status using reference",
        parameters=[VerifyPaymentSerializer],
        responses={
            200: PaymentStatusSerializer,
            400: {'description': 'Verification failed'}
        }
    )
    def get(self, request):
        reference = request.query_params.get('reference')
        
        if not reference:
            return Response({
                'error': 'Payment reference is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment = PaymentTransaction.objects.get(reference=reference)
        except PaymentTransaction.DoesNotExist:
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify with Paystack
        response = verify_payment(reference)
        
        if not response or not response.get('status'):
            return Response({
                'reference': reference,
                'status': 'failed',
                'amount': float(payment.amount),
                'paid': False,
                'message': 'Payment verification failed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check payment status
        if response['data']['status'] == 'success':
            # Update payment status
            if payment.status != 'success':
                payment.status = 'success'
                payment.save()
                
                # Update orders
                for order in payment.orders.all():
                    order.paid = True
                    order.save()
                
                # Clear pending orders from session
                request.session.pop('pending_orders', None)
                
                # Send payment receipt asynchronously
                send_payment_receipt_email_async(str(payment.id))
                generate_payment_receipt_pdf_task(str(payment.id))
                
                logger.info(f"Payment verified successfully: {reference}")
            
            return Response({
                'reference': reference,
                'status': 'success',
                'amount': float(payment.amount),
                'paid': True,
                'message': 'Payment successful'
            }, status=status.HTTP_200_OK)
        else:
            payment.status = 'failed'
            payment.save()
            
            return Response({
                'reference': reference,
                'status': 'failed',
                'amount': float(payment.amount),
                'paid': False,
                'message': 'Payment was not successful'
            }, status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    tags=['Payment'],
    description="Paystack webhook endpoint for payment notifications (Internal use only)",
    request=WebhookSerializer,
    responses={
        200: OpenApiResponse(description="Webhook processed successfully"),
        400: OpenApiResponse(description="Invalid JSON payload"),
        401: OpenApiResponse(description="Invalid signature"),
        404: OpenApiResponse(description="Payment not found"),
        500: OpenApiResponse(description="Server error processing webhook")
    },
    exclude=True  # Exclude from public API docs as it's for Paystack only
)
@apply_throttle_classes([PaymentRateThrottle])
@csrf_exempt
def payment_webhook(request):
    """
    ✅ SECURED: Webhook handler for Paystack payment notifications
    Verifies signature before processing
    """
    try:
        # ✅ STEP 1: Verify webhook signature
        signature = request.META.get('HTTP_X_PAYSTACK_SIGNATURE')
        
        if not signature:
            logger.error("Webhook received without signature")
            return HttpResponse(status=400)
        
        # Verify the signature
        if not verify_paystack_signature(request.body, signature):
            logger.error("Webhook signature verification failed")
            return HttpResponse(status=401)  # Unauthorized
        
        # ✅ STEP 2: Parse payload (now we know it's from Paystack)
        payload = json.loads(request.body)
        
        # ✅ STEP 3: Log sanitized data
        logger.info(
            f"Verified webhook received: {payload.get('event')} - "
            f"Data: {sanitize_payment_log_data(payload)}"
        )
        
        # Only process successful charges
        if payload.get('event') != 'charge.success':
            return HttpResponse(status=200)
        
        data = payload.get('data', {})
        reference = data.get('reference')
        
        if not reference:
            logger.error("Webhook: No reference in payload")
            return HttpResponse(status=400)
        
        try:
            payment = PaymentTransaction.objects.get(reference=reference)
            
            # Idempotency check - don't process if already successful
            if payment.status == 'success':
                logger.info(f"Webhook: Payment {reference} already processed")
                return HttpResponse(status=200)
            
            # Update payment status
            payment.status = 'success'
            payment.save()
            
            # Update orders
            for order in payment.orders.all():
                if not order.paid:
                    order.paid = True
                    order.save()
            
            # Send payment receipt
            send_payment_receipt_email_async(str(payment.id))
            generate_payment_receipt_pdf_task(str(payment.id))
            
            logger.info(f"Webhook: Payment {reference} processed successfully")
            
        except PaymentTransaction.DoesNotExist:
            logger.error(f"Webhook: Payment not found for reference {reference}")
            return HttpResponse(status=404)
        
        return HttpResponse(status=200)
        
    except json.JSONDecodeError:
        logger.error("Webhook: Invalid JSON payload")
        return HttpResponse(status=400)
    except Exception as e:
        logger.exception("Webhook: Error processing payment")
        return HttpResponse(status=500)


@extend_schema_view(
    list=extend_schema(description="List all payment transactions for user"),
    retrieve=extend_schema(
        description="Get specific payment transaction details",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.PATH,
                description='Payment Transaction ID'
            )
        ]
    ),
)
@extend_schema(tags=['Payment'])
class PaymentTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing payment transactions
    Users can only view their own payments
    """
    serializer_class = PaymentTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = PaymentTransaction.objects.none()  # ✅ ADD THIS LINE - Default for schema generation
    
    def get_queryset(self):
        """Get payments for authenticated user"""
        # ✅ ADD THIS CHECK
        if getattr(self, 'swagger_fake_view', False):
            return PaymentTransaction.objects.none()
        
        # Regular queryset for authenticated users
        return PaymentTransaction.objects.filter(
            orders__user=self.request.user
        ).prefetch_related(
            'orders',
            'orders__items'
        ).distinct().order_by('-created')
