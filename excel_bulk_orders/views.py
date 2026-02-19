# excel_bulk_orders/views.py
"""
API Views for Excel Bulk Orders.

Endpoints:
- Create bulk order → Generate Excel template
- Upload Excel → Validate entries
- Initialize payment → Process single payment
- Verify payment → Create participants & generate documents
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count
import logging
import cloudinary.uploader
import json
from .email_utils import send_bulk_order_confirmation_email

from .models import ExcelBulkOrder, ExcelParticipant
from .serializers import (
    ExcelBulkOrderListSerializer,
    ExcelBulkOrderDetailSerializer,
    ExcelBulkOrderCreateSerializer,
    ExcelUploadSerializer,
    ExcelParticipantSerializer,
)
from .utils import (
    generate_excel_template,
    validate_excel_file,
    create_participants_from_excel,
)
from payment.utils import initialize_payment, verify_payment
from payment.security import verify_paystack_signature
from jmw.background_utils import send_email_async
logger = logging.getLogger(__name__)



class ExcelBulkOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Excel Bulk Orders.
    
    Workflow:
    1. POST /excel-bulk-orders/ → Create order & get template
    2. POST /excel-bulk-orders/{id}/upload/ → Upload filled Excel
    3. POST /excel-bulk-orders/{id}/validate/ → Validate uploaded Excel
    4. POST /excel-bulk-orders/{id}/initialize-payment/ → Start payment
    5. POST /excel-bulk-orders/{id}/verify-payment/ → Verify & complete
    """
    
    queryset = ExcelBulkOrder.objects.all()
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ExcelBulkOrderCreateSerializer
        elif self.action == 'list':
            return ExcelBulkOrderListSerializer
        return ExcelBulkOrderDetailSerializer
    
    def get_queryset(self):
        """Filter by created_by for authenticated users"""
        if self.request.user.is_authenticated and self.request.user.is_staff:
            return ExcelBulkOrder.objects.all()
        elif self.request.user.is_authenticated:
            return ExcelBulkOrder.objects.filter(created_by=self.request.user)
        # Public access for retrieve/payment actions
        return ExcelBulkOrder.objects.all()
    
    def create(self, request, *args, **kwargs):
        """
        Create bulk order and generate Excel template.
        
        Returns template download URL.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bulk_order = serializer.save()
        
        # Generate Excel template
        try:
            template_buffer = generate_excel_template(bulk_order)
            
            # Upload to Cloudinary
            template_filename = f"excel_templates/{bulk_order.reference}.xlsx"
            upload_result = cloudinary.uploader.upload(
                template_buffer,
                resource_type='raw',
                public_id=template_filename,
                folder='excel_bulk_orders/templates'
            )
            
            bulk_order.template_file = upload_result['secure_url']
            bulk_order.save()
            
            logger.info(f"Created Excel bulk order: {bulk_order.reference}")
            
            # Return full details with template URL
            response_serializer = ExcelBulkOrderDetailSerializer(
                bulk_order,
                context={'request': request}
            )
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Error generating template: {str(e)}")
            bulk_order.delete()
            return Response(
                {"error": f"Failed to generate template: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='upload')
    def upload_excel(self, request, pk=None):
        """
        Upload filled Excel file.
        
        Saves file to Cloudinary and updates status.
        Does NOT validate yet - validation is separate step.
        """
        bulk_order = self.get_object()
        
        if bulk_order.payment_status:
            return Response(
                {"error": "Payment already completed for this order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        upload_serializer = ExcelUploadSerializer(data=request.data)
        upload_serializer.is_valid(raise_exception=True)
        
        excel_file = upload_serializer.validated_data['excel_file']
        
        try:
            # Upload to Cloudinary
            upload_filename = f"excel_uploads/{bulk_order.reference}.xlsx"
            upload_result = cloudinary.uploader.upload(
                excel_file,
                resource_type='raw',
                public_id=upload_filename,
                folder='excel_bulk_orders/uploads'
            )
            
            bulk_order.uploaded_file = upload_result['secure_url']
            bulk_order.validation_status = 'uploaded'
            bulk_order.save()
            
            logger.info(f"Excel uploaded for bulk order: {bulk_order.reference}")
            
            serializer = ExcelBulkOrderDetailSerializer(
                bulk_order,
                context={'request': request}
            )
            
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error uploading Excel: {str(e)}")
            return Response(
                {"error": f"Failed to upload file: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='validate')
    def validate_excel(self, request, pk=None):
        """
        Validate uploaded Excel file.
        
        Returns validation results with detailed errors or success.
        """
        bulk_order = self.get_object()
        
        if not bulk_order.uploaded_file:
            return Response(
                {"error": "No Excel file uploaded yet"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if bulk_order.payment_status:
            return Response(
                {"error": "Payment already completed for this order"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Download file from Cloudinary
            import requests
            from io import BytesIO
            
            response = requests.get(bulk_order.uploaded_file)
            excel_file = BytesIO(response.content)  # Wrap bytes in BytesIO
            
            # Validate
            validation_result = validate_excel_file(bulk_order, excel_file)

            # ✅ FIX: Store complete validation result (not just errors)
            bulk_order.validation_errors = validation_result

            # Update bulk order status
            if validation_result['valid']:
                bulk_order.validation_status = 'valid'
                
                # Calculate total amount
                # Reset the file pointer to beginning
                excel_file.seek(0)
                import pandas as pd
                df = pd.read_excel(excel_file, sheet_name='Participants')
                
                total_participants = len(df)
                valid_coupons = 0
                
                # Count valid coupons
                from .models import ExcelCouponCode
                for idx, row in df.iterrows():
                    coupon_code = str(row['Coupon Code']).strip() if not pd.isna(row['Coupon Code']) else ''
                    if coupon_code:
                        try:
                            coupon = ExcelCouponCode.objects.get(
                                code=coupon_code,
                                bulk_order=bulk_order,
                                is_used=False
                            )
                            valid_coupons += 1
                        except ExcelCouponCode.DoesNotExist:
                            pass
                
                chargeable = total_participants - valid_coupons
                bulk_order.total_amount = chargeable * bulk_order.price_per_participant
                
            else:
                bulk_order.validation_status = 'invalid'
                bulk_order.total_amount = 0

            bulk_order.save()

            logger.info(
                f"Excel validation for {bulk_order.reference}: "
                f"Valid={validation_result['valid']}, "
                f"Total rows={validation_result.get('summary', {}).get('total_rows', 0)}"
            )

            # Return validation results
            serializer = ExcelBulkOrderDetailSerializer(
                bulk_order,
                context={'request': request}
            )

            return Response({
                'validation_result': validation_result,
                'bulk_order': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error validating Excel: {str(e)}")
            return Response(
                {"error": f"Validation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='initialize-payment')
    def initialize_payment(self, request, pk=None):
        """
        Initialize Paystack payment for the bulk order.
        
        Only works if Excel is validated and ready.
        """
        bulk_order = self.get_object()
        
        if bulk_order.validation_status != 'valid':
            return Response(
                {"error": "Excel file must be validated before payment"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if bulk_order.payment_status:
            return Response(
                {"error": "Payment already completed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if bulk_order.total_amount <= 0:
            return Response(
                {"error": "Invalid payment amount"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Initialize payment with Paystack
            # Callback URL points to FRONTEND (not backend API)
            frontend_callback_url = request.data.get('callback_url')
            if not frontend_callback_url:
                frontend_callback_url = f"{settings.FRONTEND_URL}/payment/verify"

            payment_data = initialize_payment(
                email=bulk_order.coordinator_email,
                amount=bulk_order.total_amount,
                reference=bulk_order.reference,
                callback_url=frontend_callback_url
            )
            
            if payment_data.get('status'):
                bulk_order.validation_status = 'processing'
                bulk_order.save()
                
                logger.info(f"Payment initialized for {bulk_order.reference}")
                
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
    
    @action(detail=True, methods=['get'], url_path='verify-payment')
    def verify_payment(self, request, pk=None):
        """
        Verify payment status - Pure status check endpoint.

        This is a read-only endpoint that checks the current payment status.
        The actual payment processing (creating participants, sending emails)
        is handled by the webhook endpoint which receives server-to-server
        calls from Paystack.

        Frontend flow:
        1. Paystack redirects user to frontend with reference
        2. Frontend calls this endpoint to check if payment was processed
        3. Webhook (separately) handles the actual payment processing
        """
        bulk_order = self.get_object()

        # Get participant count if payment is complete
        participants_count = bulk_order.participants.count() if bulk_order.payment_status else 0

        serializer = ExcelBulkOrderDetailSerializer(
            bulk_order,
            context={'request': request}
        )

        return Response({
            'reference': bulk_order.reference,
            'title': bulk_order.title,
            'coordinator_email': bulk_order.coordinator_email,
            'paid': bulk_order.payment_status,
            'validation_status': bulk_order.validation_status,
            'total_amount': float(bulk_order.total_amount),
            'participants_count': participants_count,
            'paystack_reference': bulk_order.paystack_reference,
            'message': 'Payment successful' if bulk_order.payment_status else 'Payment pending',
            'bulk_order': serializer.data
        })
    
    @action(detail=True, methods=['get'], url_path='download-template')
    def download_template(self, request, pk=None):
        """Download the Excel template"""
        bulk_order = self.get_object()
        
        if not bulk_order.template_file:
            return Response(
                {"error": "Template not generated yet"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Redirect to Cloudinary URL
        import requests
        response = requests.get(bulk_order.template_file)
        
        http_response = HttpResponse(
            response.content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        http_response['Content-Disposition'] = f'attachment; filename="{bulk_order.reference}_template.xlsx"'
        
        return http_response
    
    @action(detail=True, methods=['get'], url_path='paid-participants', permission_classes=[permissions.AllowAny])
    def paid_participants(self, request, pk=None):
        """
        Public page showing all paid participants for social proof.
        Supports both HTML view and JSON API.
        
        Usage:
        - JSON API: GET /api/excel-bulk-orders/{uuid}/paid-participants/
        - HTML View: GET /api/excel-bulk-orders/{uuid}/paid-participants/ (with Accept: text/html)
        """
        bulk_order = self.get_object()
        
        # Check if payment complete
        if not bulk_order.payment_status:
            return Response(
                {"error": "No paid participants yet. Payment not completed."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get all participants
        participants = bulk_order.participants.all().order_by('-created_at')
        
        # Size summary
        size_summary = list(
            participants.values("size")
            .annotate(count=Count("size"))
            .order_by("size")
        )
        
        # Check if HTML view requested (browser)
        if request.accepted_renderer.format == 'html':
            context = {
                'bulk_order': bulk_order,
                'participants': participants[:20],  # First 20 for display
                'all_participants': participants,  # All for download
                'size_summary': size_summary,
                'total_participants': participants.count(),
                'total_paid': participants.filter(is_coupon_applied=False).count(),
                'total_free': participants.filter(is_coupon_applied=True).count(),
                'company_name': settings.COMPANY_NAME,
                'company_address': settings.COMPANY_ADDRESS,
                'company_phone': settings.COMPANY_PHONE,
                'company_email': settings.COMPANY_EMAIL,
                'now': timezone.now(),
            }
            
            return Response(
                context,
                template_name='excel_bulk_orders/paid_participants_public.html'
            )
        
        # JSON response for API
        return Response({
            'reference': bulk_order.reference,
            'title': bulk_order.title,
            'coordinator': bulk_order.coordinator_name,
            'total_participants': participants.count(),
            'total_paid': participants.filter(is_coupon_applied=False).count(),
            'total_free': participants.filter(is_coupon_applied=True).count(),
            'size_summary': size_summary,
            'recent_participants': [
                {
                    'full_name': p.full_name,
                    'size': p.size,
                    'custom_name': p.custom_name if bulk_order.requires_custom_name else None,
                    'status': 'Free (Coupon)' if p.is_coupon_applied else 'Paid',
                    'created_at': p.created_at.isoformat()
                }
                for p in participants[:20]
            ]
        })


class ExcelParticipantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing participants.
    Read-only access.
    """
    
    queryset = ExcelParticipant.objects.all()
    serializer_class = ExcelParticipantSerializer
    permission_classes = [permissions.AllowAny]
    

    def get_queryset(self):
        """Filter by bulk_order if specified"""
        queryset = ExcelParticipant.objects.all()
        
        bulk_order_id = self.request.query_params.get('bulk_order')
        if bulk_order_id:
            # Validate UUID format to prevent ValidationError
            try:
                import uuid
                uuid.UUID(bulk_order_id)  # Will raise ValueError if invalid
                queryset = queryset.filter(bulk_order_id=bulk_order_id)
            except (ValueError, AttributeError):
                # Invalid UUID format - return empty queryset
                queryset = queryset.none()
        
        return queryset.select_related('bulk_order', 'coupon')
    

@csrf_exempt
def excel_bulk_order_payment_webhook(request):
    """
    Paystack webhook handler for excel bulk orders

    Reference format: EXL-{unique_code}
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
            logger.error("Excel webhook received without signature")
            return JsonResponse(
                {'status': 'error', 'message': 'Missing signature'},
                status=401
            )

        if not verify_paystack_signature(request.body, signature):
            logger.error("Excel webhook signature verification failed")
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid signature'},
                status=401
            )

        # 📦 STEP 2: Parse payload
        payload = json.loads(request.body)
        event = payload.get('event')
        data = payload.get('data', {})

        logger.info(f"Excel webhook received: {event}")

        # 🚫 Ignore non-charge events
        if event != 'charge.success':
            logger.info(f"Ignoring webhook event: {event}")
            return JsonResponse(
                {'status': 'success', 'message': 'Event ignored'},
                status=200
            )

        # ❌ IMPORTANT: Check payment status BEFORE touching DB
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

        if not reference or not reference.startswith('EXL-'):
            logger.error(f"Invalid reference format: {reference}")
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid reference format'},
                status=400
            )

        try:
            # 🔒 STEP 4: Idempotent payment processing
            with transaction.atomic():
                bulk_order = (
                    ExcelBulkOrder.objects
                    .select_for_update()
                    .get(reference=reference)
                )

                # Already processed → idempotent exit
                if bulk_order.payment_status:
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

                # ✅ Mark payment as successful
                bulk_order.payment_status = True
                bulk_order.paystack_reference = reference
                bulk_order.validation_status = 'completed'
                bulk_order.save(update_fields=[
                    'payment_status',
                    'paystack_reference',
                    'validation_status',
                    'updated_at'
                ])

            # 📂 STEP 5: Create participants (outside transaction)
            import requests
            from io import BytesIO

            response = requests.get(bulk_order.uploaded_file)
            excel_file = BytesIO(response.content)

            participants_count = create_participants_from_excel(
                bulk_order,
                excel_file
            )

            logger.info(
                f"Created {participants_count} participants for {reference}"
            )

            # 📧 STEP 6: Send confirmation email
            send_bulk_order_confirmation_email(
                bulk_order,
                participants_count
            )

            logger.info(
                f"Excel bulk order payment successful: {reference}. "
                f"Participants: {participants_count}"
            )

            return JsonResponse(
                {
                    'status': 'success',
                    'message': 'Payment verified, participants created, email sent',
                    'reference': reference,
                    'participants_created': participants_count
                },
                status=200
            )

        except ExcelBulkOrder.DoesNotExist:
            logger.error(f"ExcelBulkOrder not found: {reference}")
            return JsonResponse(
                {'status': 'error', 'message': 'Order not found'},
                status=404
            )

    except json.JSONDecodeError:
        logger.error("Invalid JSON in excel webhook payload")
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid JSON'},
            status=400
        )

    except Exception:
        logger.exception("Unexpected error processing excel webhook")
        return JsonResponse(
            {'status': 'error', 'message': 'Internal server error'},
            status=500
        )
