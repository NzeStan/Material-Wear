# excel_bulk_orders/serializers.py
"""
Serializers for Excel Bulk Orders API.

Handles:
- Bulk order creation
- Excel upload and validation
- Payment processing
- Participant management
"""
from rest_framework import serializers
from .models import ExcelBulkOrder, ExcelParticipant
from bulk_orders.models import CouponCode
from decimal import Decimal


class ExcelParticipantSerializer(serializers.ModelSerializer):
    """Serializer for individual participants"""
    
    coupon_status = serializers.SerializerMethodField()
    
    class Meta:
        model = ExcelParticipant
        fields = [
            'id', 'full_name', 'size', 'custom_name',
            'coupon_code', 'is_coupon_applied', 'coupon_status',
            'row_number', 'created_at'
        ]
        read_only_fields = ['id', 'is_coupon_applied', 'created_at']
    
    def get_coupon_status(self, obj):
        """Get user-friendly coupon status"""
        if obj.is_coupon_applied:
            return 'Applied - Free'
        elif obj.coupon_code:
            return 'Invalid/Expired'
        return 'No Coupon'
    
    def to_representation(self, instance):
        """Conditionally include custom_name"""
        representation = super().to_representation(instance)
        
        if not instance.bulk_order.requires_custom_name:
            representation.pop('custom_name', None)
        
        return representation


class ExcelBulkOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing bulk orders"""
    
    participant_count = serializers.SerializerMethodField()
    couponed_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_validation_status_display', read_only=True)
    
    class Meta:
        model = ExcelBulkOrder
        fields = [
            'id', 'reference', 'title', 'coordinator_name',
            'coordinator_email', 'price_per_participant',
            'participant_count', 'couponed_count', 'total_amount',
            'validation_status', 'status_display', 'payment_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'reference', 'total_amount', 'created_at', 'updated_at']
    
    def get_participant_count(self, obj):
        return obj.participants.count()
    
    def get_couponed_count(self, obj):
        return obj.participants.filter(is_coupon_applied=True).count()


class ExcelBulkOrderDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with participant data"""
    
    participants = ExcelParticipantSerializer(many=True, read_only=True)
    validation_summary = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_validation_status_display', read_only=True)
    payment_breakdown = serializers.SerializerMethodField()
    
    class Meta:
        model = ExcelBulkOrder
        fields = [
            'id', 'reference', 'title',
            'coordinator_name', 'coordinator_email', 'coordinator_phone',
            'price_per_participant', 'requires_custom_name',
            'template_file', 'uploaded_file',
            'validation_status', 'status_display', 'validation_summary',
            'total_amount', 'payment_status', 'paystack_reference',
            'payment_breakdown', 'participants',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'reference', 'template_file', 'validation_status',
            'total_amount', 'payment_status', 'paystack_reference',
            'created_at', 'updated_at'
        ]
    
    def get_validation_summary(self, obj):
        return obj.get_validation_summary()
    
    def get_payment_breakdown(self, obj):
        """
        Calculate payment breakdown.
        
        FIXED: Now calculates from Excel data before payment,
        and from actual participants after payment.
        """
        import pandas as pd
        import requests
        from io import BytesIO
        import logging
        
        logger = logging.getLogger(__name__)
        
        # After payment: use actual participants
        if obj.payment_status and obj.participants.exists():
            total_participants = obj.participants.count()
            couponed = obj.participants.filter(is_coupon_applied=True).count()
            chargeable = total_participants - couponed
            
            logger.debug(
                f"Payment breakdown (after payment) for {obj.reference}: "
                f"Total={total_participants}, Couponed={couponed}, Chargeable={chargeable}"
            )
        
        # Before payment but after validation: calculate from Excel
        elif obj.validation_status == 'valid' and obj.uploaded_file:
            try:
                # Download and read Excel file
                response = requests.get(obj.uploaded_file, timeout=10)
                excel_file = BytesIO(response.content)
                df = pd.read_excel(excel_file, sheet_name='Participants')
                
                total_participants = len(df)
                couponed = 0
                
                # Count valid coupons
                from .models import ExcelCouponCode
                for idx, row in df.iterrows():
                    coupon_code = str(row['Coupon Code']).strip() if not pd.isna(row['Coupon Code']) else ''
                    if coupon_code:
                        if ExcelCouponCode.objects.filter(
                            code=coupon_code,
                            bulk_order=obj,
                            is_used=False
                        ).exists():
                            couponed += 1
                
                chargeable = total_participants - couponed
                
                logger.debug(
                    f"Payment breakdown (before payment) for {obj.reference}: "
                    f"Total={total_participants}, Couponed={couponed}, Chargeable={chargeable}"
                )
                
            except Exception as e:
                logger.error(f"Error calculating payment breakdown from Excel: {str(e)}")
                total_participants = 0
                couponed = 0
                chargeable = 0
        
        # No data yet
        else:
            total_participants = 0
            couponed = 0
            chargeable = 0
        
        return {
            'total_participants': total_participants,
            'couponed_participants': couponed,
            'chargeable_participants': chargeable,
            'price_per_participant': str(obj.price_per_participant),
            'total_amount': str(obj.total_amount),
            'currency': 'NGN'
        }



class ExcelBulkOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new bulk orders"""
    
    class Meta:
        model = ExcelBulkOrder
        fields = [
            'title', 'coordinator_name', 'coordinator_email',
            'coordinator_phone', 'price_per_participant',
            'requires_custom_name'
        ]
    
    def validate_price_per_participant(self, value):
        """Ensure price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value
    
    def validate_coordinator_email(self, value):
        """Basic email validation"""
        if not value:
            raise serializers.ValidationError("Coordinator email is required.")
        return value.lower()
    
    def create(self, validated_data):
        """Create bulk order and set created_by if authenticated"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return ExcelBulkOrder.objects.create(**validated_data)


class ExcelUploadSerializer(serializers.Serializer):
    """Serializer for Excel file uploads"""
    
    excel_file = serializers.FileField(
        help_text="Excel file (.xlsx) with participant data"
    )
    
    def validate_excel_file(self, value):
        """Validate uploaded file"""
        # Check file extension
        if not value.name.endswith('.xlsx'):
            raise serializers.ValidationError(
                "Only .xlsx files are accepted. Please upload an Excel file."
            )
        
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File size exceeds 5MB limit. Current size: {value.size / (1024 * 1024):.2f}MB"
            )
        
        return value


class ValidationErrorSerializer(serializers.Serializer):
    """Serializer for validation error responses"""
    
    row = serializers.IntegerField()
    field = serializers.CharField()
    error = serializers.CharField()
    current_value = serializers.CharField(allow_blank=True, allow_null=True)
    
    class Meta:
        fields = ['row', 'field', 'error', 'current_value']