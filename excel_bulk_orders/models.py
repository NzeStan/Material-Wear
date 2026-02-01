# excel_bulk_orders/models.py
"""
Models for Excel-based bulk order management system.

This app handles coordinator-managed bulk orders where one person:
1. Creates a bulk order campaign
2. Downloads an Excel template
3. Fills participant details offline
4. Uploads completed Excel
5. Makes a single payment for all participants
6. System generates documents for all participants
"""
import uuid
import string
import random
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ExcelBulkOrder(models.Model):
    """
    Main model for Excel-based bulk orders.
    
    Workflow:
    1. Coordinator creates order
    2. System generates Excel template
    3. Coordinator uploads filled Excel
    4. System validates entries
    5. Coordinator makes single payment
    6. System processes all participants
    """
    
    VALIDATION_STATUS_CHOICES = [
        ('pending', 'Pending Upload'),
        ('uploaded', 'File Uploaded - Not Validated'),
        ('valid', 'Validated - Ready for Payment'),
        ('invalid', 'Validation Failed'),
        ('processing', 'Processing Payment'),
        ('completed', 'Payment Complete'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=20, unique=True, editable=False)
    
    # Coordinator Information
    coordinator_name = models.CharField(max_length=255)
    coordinator_email = models.EmailField()
    coordinator_phone = models.CharField(max_length=20)
    
    # Campaign Details
    title = models.CharField(
        max_length=255,
        help_text="e.g., 'NYSC Batch C Stream 1 Camp'"
    )
    price_per_participant = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per participant in Naira"
    )
    requires_custom_name = models.BooleanField(
        default=False,
        help_text="If True, Custom Name column will appear in Excel template"
    )
    
    # Files
    template_file = models.URLField(
        blank=True,
        null=True,
        help_text="Cloudinary URL of generated Excel template"
    )
    uploaded_file = models.URLField(
        blank=True,
        null=True,
        help_text="Cloudinary URL of uploaded Excel with participant data"
    )
    
    # Validation
    validation_status = models.CharField(
        max_length=20,
        choices=VALIDATION_STATUS_CHOICES,
        default='pending'
    )
    validation_errors = models.JSONField(
        null=True,
        blank=True,
        help_text="Detailed validation errors for uploaded Excel"
    )
    
    # Payment
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount to be paid (excluding couponed participants)"
    )
    payment_status = models.BooleanField(default=False)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='excel_bulk_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference'], name='excel_bulk_ref_idx'),
            models.Index(fields=['coordinator_email'], name='excel_bulk_email_idx'),
            models.Index(fields=['validation_status'], name='excel_bulk_status_idx'),
            models.Index(fields=['payment_status'], name='excel_bulk_payment_idx'),
            models.Index(fields=['created_at'], name='excel_bulk_created_idx'),
        ]
        verbose_name = 'Excel Bulk Order'
        verbose_name_plural = 'Excel Bulk Orders'
    
    def __str__(self):
        return f"{self.title} - {self.reference}"
    
    def save(self, *args, **kwargs):
        """Generate reference on first save"""
        if not self.reference:
            self.reference = self._generate_reference()
        super().save(*args, **kwargs)
    
    @staticmethod
    def _generate_reference():
        """Generate unique reference code"""
        chars = string.ascii_uppercase + string.digits
        while True:
            reference = 'EXL-' + ''.join(random.choices(chars, k=12))
            if not ExcelBulkOrder.objects.filter(reference=reference).exists():
                return reference
    
    def calculate_total_amount(self):
        """
        Calculate total amount based on participants and coupons.
        
        Returns:
            Decimal: Total amount to be paid
        """
        total_participants = self.participants.count()
        couponed_participants = self.participants.filter(is_coupon_applied=True).count()
        chargeable = total_participants - couponed_participants
        
        total = chargeable * self.price_per_participant
        logger.info(
            f"Excel Bulk Order {self.reference}: "
            f"Total={total_participants}, Couponed={couponed_participants}, "
            f"Chargeable={chargeable}, Amount=₦{total}"
        )
        return total
    
    def get_validation_summary(self):
        """Get summary of validation results"""
        if not self.validation_errors:
            return None
        
        errors = self.validation_errors.get('errors', [])
        return {
            'total_rows': self.validation_errors.get('summary', {}).get('total_rows', 0),
            'valid_rows': self.validation_errors.get('summary', {}).get('valid_rows', 0),
            'error_rows': len(errors),
            'errors': errors
        }


class ExcelParticipant(models.Model):
    """
    Individual participant extracted from uploaded Excel.
    Created only after successful payment.
    """
    
    SIZE_CHOICES = [
        ('S', 'Small'),
        ('M', 'Medium'),
        ('L', 'Large'),
        ('XL', 'Extra Large'),
        ('XXL', '2X Large'),
        ('XXXL', '3X Large'),
        ('XXXXL', '4X Large'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulk_order = models.ForeignKey(
        ExcelBulkOrder,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    
    # Participant Details
    full_name = models.CharField(max_length=255)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    custom_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Coupon Information
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon = models.ForeignKey(
        'bulk_orders.CouponCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='excel_participants'
    )
    is_coupon_applied = models.BooleanField(
        default=False,
        help_text="True if valid coupon was used (participant not charged)"
    )
    
    # Excel Metadata
    row_number = models.PositiveIntegerField(
        help_text="Original row number from Excel file"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['bulk_order', 'row_number']
        indexes = [
            models.Index(fields=['bulk_order', 'row_number'], name='excel_part_bulk_row_idx'),
            models.Index(fields=['full_name'], name='excel_part_name_idx'),
            models.Index(fields=['size'], name='excel_part_size_idx'),
            models.Index(fields=['is_coupon_applied'], name='excel_part_coupon_idx'),
        ]
        unique_together = [['bulk_order', 'row_number']]
        verbose_name = 'Excel Participant'
        verbose_name_plural = 'Excel Participants'
    
    def __str__(self):
        coupon_info = f" (Coupon: {self.coupon_code})" if self.is_coupon_applied else ""
        return f"{self.full_name} - {self.size}{coupon_info}"
    
    def clean(self):
        """Validate custom_name requirement"""
        from django.core.exceptions import ValidationError
        
        if self.bulk_order.requires_custom_name and not self.custom_name:
            raise ValidationError({
                'custom_name': 'Custom name is required for this bulk order.'
            })