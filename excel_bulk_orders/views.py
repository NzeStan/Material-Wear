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
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging
import cloudinary.uploader

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
            
            # Update bulk order
            if validation_result['valid']:
                bulk_order.validation_status = 'valid'
                bulk_order.validation_errors = None
                
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
                bulk_order.validation_errors = validation_result
                bulk_order.total_amount = 0
            
            bulk_order.save()
            
            logger.info(
                f"Validated Excel for {bulk_order.reference}: "
                f"Valid={validation_result['valid']}"
            )
            
            # Return validation results
            return Response({
                'validation_result': validation_result,
                'bulk_order': ExcelBulkOrderDetailSerializer(
                    bulk_order,
                    context={'request': request}
                ).data
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
            callback_url = request.build_absolute_uri(
                f'/api/excel-bulk-orders/{bulk_order.id}/verify-payment/'
            )
            
            payment_data = initialize_payment(
                email=bulk_order.coordinator_email,
                amount=bulk_order.total_amount,
                reference=bulk_order.reference,
                callback_url=callback_url
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
    
    @action(detail=True, methods=['post', 'get'], url_path='verify-payment')
    def verify_payment(self, request, pk=None):
        """
        Verify payment and create participants.
        
        Called by Paystack callback or manually by frontend.
        """
        bulk_order = self.get_object()
        
        if bulk_order.payment_status:
            return Response(
                {"message": "Payment already verified"},
                status=status.HTTP_200_OK
            )
        
        # Get reference from query params or use bulk_order reference
        reference = request.query_params.get('reference', bulk_order.reference)
        
        try:
            # Verify payment with Paystack
            verification = verify_payment(reference)
            
            if verification.get('status') and verification['data']['status'] == 'success':
                # Payment successful - create participants
                with transaction.atomic():
                    # Download Excel file
                    import requests
                    from io import BytesIO
                    
                    response = requests.get(bulk_order.uploaded_file)
                    excel_file = BytesIO(response.content)  # Wrap bytes in BytesIO
                    
                    # Create participants
                    participants_count = create_participants_from_excel(
                        bulk_order,
                        excel_file
                    )
                    
                    # Update bulk order
                    bulk_order.payment_status = True
                    bulk_order.paystack_reference = reference
                    bulk_order.validation_status = 'completed'
                    bulk_order.save()
                    
                    logger.info(
                        f"Payment verified for {bulk_order.reference}. "
                        f"Created {participants_count} participants."
                    )
                
                # Send confirmation email to coordinator (not a background task)
                from jmw.background_utils import send_email_async
                
                context = {
                    'bulk_order': bulk_order,
                    'participants_count': participants_count,
                    'company_name': settings.COMPANY_NAME,
                    'company_email': settings.COMPANY_EMAIL,
                }
                
                # Simple text email for now (can create HTML template later)
                email_subject = f'Payment Confirmed - {bulk_order.title}'
                email_message = f"""
Dear {bulk_order.coordinator_name},

Thank you for your payment!

Order Details:
- Reference: {bulk_order.reference}
- Campaign: {bulk_order.title}
- Participants: {participants_count}
- Amount Paid: ₦{bulk_order.total_amount:,.2f}

Your order has been successfully processed.

Best regards,
{settings.COMPANY_NAME}
                """.strip()
                
                send_email_async(
                    subject=email_subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[bulk_order.coordinator_email]
                )
                
                logger.info(f"Confirmation email queued for {bulk_order.coordinator_email}")
                
                serializer = ExcelBulkOrderDetailSerializer(
                    bulk_order,
                    context={'request': request}
                )
                
                return Response({
                    'message': 'Payment verified successfully',
                    'participants_created': participants_count,
                    'bulk_order': serializer.data
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
            queryset = queryset.filter(bulk_order_id=bulk_order_id)
        
        return queryset.select_related('bulk_order', 'coupon')