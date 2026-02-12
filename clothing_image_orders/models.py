# clothing_image_orders/models.py
"""
Models for clothing bulk orders with image upload support.

This app handles bulk orders where each participant:
1. Uploads an optional image (with validation)
2. Selects their size
3. Provides custom name (optional)
4. Makes individual payment
5. Can use a coupon code

Admin can generate comprehensive document packages with:
- PDF, Word, Excel files
- Organized image folders by size
"""
import uuid
import string
import random
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal
from cloudinary.models import CloudinaryField
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ClothingImageOrder(models.Model):
    """
    Main model for clothing bulk orders with image support.
    
    One organization creates an order, multiple participants join individually.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    
    # Organization Information
    organization_name = models.CharField(
        max_length=255,
        help_text="Name of organization (e.g., 'First Baptist Church')"
    )
    coordinator_name = models.CharField(max_length=255)
    coordinator_email = models.EmailField()
    coordinator_phone = models.CharField(max_length=20)
    
    # Order Configuration
    title = models.CharField(
        max_length=255,
        help_text="e.g., 'Church Anniversary Shirts 2025'"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the clothing order"
    )
    price_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Price per item in Naira"
    )
    requires_custom_name = models.BooleanField(
        default=False,
        help_text="If True, participants can provide custom names for printing"
    )
    requires_image = models.BooleanField(
        default=False,
        help_text="If True, image upload is mandatory; if False, it's optional"
    )
    
    # Dates
    order_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Deadline for participants to join and pay"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="If False, order is closed and new participants cannot join"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='clothing_image_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference'], name='clo_img_ref_idx'),
            models.Index(fields=['organization_name'], name='clo_img_org_idx'),
            models.Index(fields=['is_active'], name='clo_img_active_idx'),
            models.Index(fields=['created_at'], name='clo_img_created_idx'),
        ]
        verbose_name = 'Clothing Image Order'
        verbose_name_plural = 'Clothing Image Orders'
    
    def __str__(self):
        return f"{self.reference} - {self.organization_name}"
    
    def save(self, *args, **kwargs):
        """Generate reference on creation"""
        if not self.reference:
            self.reference = self._generate_reference()
        
        # Normalize organization name to uppercase
        self.organization_name = self.organization_name.upper()
        
        super().save(*args, **kwargs)
        logger.debug(f"Saved ClothingImageOrder: {self.reference}")
    
    def _generate_reference(self):
        """Generate unique reference like CLO-XXXXX"""
        while True:
            ref = f"CLO-{uuid.uuid4().hex[:8].upper()}"
            if not ClothingImageOrder.objects.filter(reference=ref).exists():
                return ref
    
    def is_expired(self):
        """Check if order has passed deadline"""
        if not self.order_deadline:
            return False
        return timezone.now() > self.order_deadline
    
    def get_participant_stats(self):
        """Get statistics about participants"""
        participants = self.participants.all()
        return {
            'total': participants.count(),
            'paid': participants.filter(paid=True).count(),
            'pending': participants.filter(paid=False).count(),
            'with_images': participants.exclude(image='').count(),
            'with_coupons': participants.filter(coupon_used__isnull=False).count(),
        }


class ClothingCouponCode(models.Model):
    """
    Coupon codes for clothing image orders.
    Each coupon can be used once to make a participant free.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        ClothingImageOrder,
        on_delete=models.CASCADE,
        related_name='coupons'
    )
    code = models.CharField(max_length=50, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['order', 'is_used'], name='clo_coupon_order_used_idx'),
            models.Index(fields=['code'], name='clo_coupon_code_idx'),
        ]
        verbose_name = 'Clothing Coupon Code'
        verbose_name_plural = 'Clothing Coupon Codes'
    
    def __str__(self):
        return f"{self.code} ({'Used' if self.is_used else 'Available'})"
    
    def save(self, *args, **kwargs):
        """Ensure code is uppercase"""
        self.code = self.code.upper()
        super().save(*args, **kwargs)
        logger.debug(f"Saved ClothingCouponCode: {self.code}")


class ClothingOrderParticipant(models.Model):
    """
    Individual participant in a clothing image order.
    
    Each participant:
    - Makes their own payment
    - Uploads their own image (optional/required based on order settings)
    - Selects their size
    - Can provide custom name
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
    order = models.ForeignKey(
        ClothingImageOrder,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    reference = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    serial_number = models.PositiveIntegerField(
        editable=False,
        help_text="Auto-incrementing number within the order"
    )
    
    # Participant Details
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    custom_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Custom name to print on clothing (if enabled)"
    )
    
    # Image Upload
    image = CloudinaryField(
        'image',
        blank=True,
        null=True,
        folder='clothing_orders',
        resource_type='image',
        help_text="Optional image upload (PNG, JPG, JPEG - max 5MB)"
    )
    
    # Payment
    paid = models.BooleanField(default=False)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
    # Coupon
    coupon_used = models.ForeignKey(
        ClothingCouponCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='participants'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'serial_number']
        indexes = [
            models.Index(fields=['reference'], name='clo_part_ref_idx'),
            models.Index(fields=['order', 'serial_number'], name='clo_part_order_serial_idx'),
            models.Index(fields=['email'], name='clo_part_email_idx'),
            models.Index(fields=['size'], name='clo_part_size_idx'),
            models.Index(fields=['paid'], name='clo_part_paid_idx'),
            models.Index(fields=['created_at'], name='clo_part_created_idx'),
        ]
        unique_together = [['order', 'serial_number']]
        verbose_name = 'Clothing Order Participant'
        verbose_name_plural = 'Clothing Order Participants'
    
    def __str__(self):
        status = "PAID" if self.paid else "PENDING"
        return f"{self.reference} - {self.full_name} ({status})"
    
    def save(self, *args, **kwargs):
        """Generate reference and serial number on creation"""
        # Generate reference
        if not self.reference:
            self.reference = self._generate_reference()
        
        # Generate serial number
        if not self.serial_number:
            last_participant = ClothingOrderParticipant.objects.filter(
                order=self.order
            ).order_by('-serial_number').first()
            
            self.serial_number = 1 if not last_participant else last_participant.serial_number + 1
        
        # Normalize full name to uppercase
        self.full_name = self.full_name.upper()
        if self.custom_name:
            self.custom_name = self.custom_name.upper()
        
        super().save(*args, **kwargs)
        logger.debug(f"Saved ClothingOrderParticipant: {self.reference}")
    
    def _generate_reference(self):
        """Generate unique reference like CLOP-XXXXX"""
        while True:
            ref = f"CLOP-{uuid.uuid4().hex[:8].upper()}"
            if not ClothingOrderParticipant.objects.filter(reference=ref).exists():
                return ref
    
    def get_image_filename(self):
        """
        Generate filename for the image based on settings.
        
        Returns:
            str: Filename like "001_JOHN_DOE.jpg" or "PASTOR_JOHN.jpg"
        """
        if self.custom_name:
            # Use custom name if provided
            return f"{self.custom_name.replace(' ', '_')}.jpg"
        else:
            # Use serial number + name
            name_part = self.full_name.replace(' ', '_')
            return f"{str(self.serial_number).zfill(3)}_{name_part}.jpg"
    
    def get_cloudinary_folder(self):
        """Get the Cloudinary folder path for this participant's image"""
        return f"clothing_orders/{self.order.reference}/{self.size}"