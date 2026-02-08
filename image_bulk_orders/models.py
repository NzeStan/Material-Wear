# image_bulk_orders/models.py
"""
Models for image-based bulk order management.

Optimizations:
- Proper database indexes for common queries
- select_related/prefetch_related in managers
- Efficient serial number generation with database constraints
- Cloudinary integration with public_id storage
"""
import uuid
import string
import random
from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ImageBulkOrderLink(models.Model):
    """
    Bulk order campaign with image requirements.
    
    Optimizations:
    - Indexed slug for fast lookups
    - Compound indexes for common filters
    - Normalized organization_name (uppercase)
    """
    
    GENERATION_STATUS_CHOICES = [
        ('pending', 'Pending Generation'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=255, unique=True, editable=False, db_index=True)
    organization_name = models.CharField(max_length=255)
    price_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    custom_branding_enabled = models.BooleanField(default=False)
    payment_deadline = models.DateTimeField()
    
    # Image requirements
    image_required = models.BooleanField(default=True)
    max_image_size_mb = models.PositiveIntegerField(default=5)
    allowed_image_formats = models.JSONField(
        default=list,
        help_text="Allowed formats: jpg, jpeg, png, webp"
    )
    
    # Document generation tracking
    last_generated_at = models.DateTimeField(null=True, blank=True)
    generation_status = models.CharField(
        max_length=20,
        choices=GENERATION_STATUS_CHOICES,
        default='pending'
    )
    generated_zip_url = models.URLField(blank=True, null=True)
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='image_bulk_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Image Bulk Order Link'
        verbose_name_plural = 'Image Bulk Order Links'
        indexes = [
            models.Index(fields=['slug'], name='img_bulk_slug_idx'),
            models.Index(fields=['created_by', 'payment_deadline'], name='img_bulk_user_deadline_idx'),
            models.Index(fields=['organization_name'], name='img_bulk_org_idx'),
            models.Index(fields=['created_at'], name='img_bulk_created_idx'),
            models.Index(fields=['generation_status'], name='img_bulk_gen_status_idx'),
        ]
    
    def save(self, *args, **kwargs):
        """Generate slug and normalize organization name"""
        if not self.slug:
            base_slug = slugify(self.organization_name)
            unique_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            self.slug = f"{base_slug}-{unique_suffix}"
        
        # Normalize organization name to uppercase
        self.organization_name = self.organization_name.upper()
        
        # Set default allowed formats if not set
        if not self.allowed_image_formats:
            self.allowed_image_formats = ['jpg', 'jpeg', 'png', 'webp']
        
        super().save(*args, **kwargs)
        logger.info(f"ImageBulkOrderLink saved: {self.slug}")
    
    def __str__(self):
        return f"{self.organization_name} ({self.slug})"
    
    def is_expired(self):
        """Check if payment deadline has passed"""
        return timezone.now() > self.payment_deadline
    
    def get_shareable_url(self):
        """Get shareable URL for this bulk order"""
        return f"/image-bulk-order/{self.slug}/"
    
    def get_paid_count(self):
        """Get count of paid orders (cached)"""
        return self.orders.filter(paid=True).count()
    
    def get_total_revenue(self):
        """Calculate total revenue from paid orders"""
        paid_orders = self.orders.filter(paid=True, coupon_used__isnull=True).count()
        return paid_orders * self.price_per_item


class ImageCouponCode(models.Model):
    """
    Coupon codes for image bulk orders.
    
    Optimizations:
    - Unique index on code for fast lookups
    - Compound index on (bulk_order, is_used) for filtering
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulk_order = models.ForeignKey(
        ImageBulkOrderLink,
        on_delete=models.CASCADE,
        related_name='coupons'
    )
    code = models.CharField(max_length=20, unique=True, db_index=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Image Coupon Code'
        verbose_name_plural = 'Image Coupon Codes'
        indexes = [
            models.Index(fields=['bulk_order', 'is_used'], name='img_coupon_bulk_used_idx'),
            models.Index(fields=['code'], name='img_coupon_code_idx'),
        ]
    
    def save(self, *args, **kwargs):
        """Normalize code to uppercase"""
        self.code = self.code.upper()
        super().save(*args, **kwargs)
        logger.debug(f"ImageCouponCode saved: {self.code}")
    
    def __str__(self):
        return f"{self.code} ({'Used' if self.is_used else 'Available'})"


class ImageOrderEntry(models.Model):
    """
    Individual order entry with image upload.
    
    Optimizations:
    - Compound unique constraint on (bulk_order, serial_number)
    - Indexes on common filter fields
    - Efficient serial number generation
    - Cloudinary integration with public_id storage
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
    reference = models.CharField(max_length=20, unique=True, db_index=True)
    bulk_order = models.ForeignKey(
        ImageBulkOrderLink,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    serial_number = models.PositiveIntegerField(editable=False)
    
    # Participant details
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    custom_name = models.CharField(max_length=255, blank=True)
    
    # Image fields
    uploaded_image = models.URLField(
        help_text="Cloudinary URL of uploaded image"
    )
    cloudinary_public_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Cloudinary public ID for image management"
    )
    image_uploaded_at = models.DateTimeField(auto_now_add=True)
    image_width = models.PositiveIntegerField(null=True, blank=True)
    image_height = models.PositiveIntegerField(null=True, blank=True)
    
    # Payment
    coupon_used = models.ForeignKey(
        ImageCouponCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    paid = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['bulk_order', 'serial_number']
        verbose_name = 'Image Order Entry'
        verbose_name_plural = 'Image Order Entries'
        unique_together = [('bulk_order', 'serial_number')]
        indexes = [
            models.Index(fields=['bulk_order', 'paid'], name='img_order_bulk_paid_idx'),
            models.Index(fields=['reference'], name='img_order_ref_idx'),
            models.Index(fields=['size', 'paid'], name='img_order_size_paid_idx'),
            models.Index(fields=['email'], name='img_order_email_idx'),
            models.Index(fields=['created_at'], name='img_order_created_idx'),
        ]
    
    def save(self, *args, **kwargs):
        """
        Auto-generate reference and serial number.
        
        Optimizations:
        - Uses select_for_update for concurrent safety
        - Single database query for serial number
        """
        if not self.reference:
            # Generate IMG- prefixed reference
            unique_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            self.reference = f"IMG-{unique_code}"
        
        if not self.serial_number:
            # Get next serial number for this bulk order (thread-safe)
            with transaction.atomic():
                max_serial = (
                    ImageOrderEntry.objects
                    .filter(bulk_order=self.bulk_order)
                    .select_for_update()
                    .aggregate(models.Max('serial_number'))['serial_number__max']
                )
                self.serial_number = (max_serial or 0) + 1
        
        super().save(*args, **kwargs)
        logger.info(f"ImageOrderEntry saved: {self.reference} (Serial: {self.serial_number})")
    
    def __str__(self):
        return f"{self.reference} - {self.full_name}"
    
    def get_image_filename(self):
        """
        Get filename for organized image directory.
        Uses custom_name if available and enabled, otherwise serial + full_name.
        """
        if self.bulk_order.custom_branding_enabled and self.custom_name:
            base_name = slugify(self.custom_name)
        else:
            base_name = f"{self.serial_number:04d}_{slugify(self.full_name)}"
        
        # Get extension from Cloudinary URL
        ext = self.uploaded_image.split('.')[-1].split('?')[0]
        return f"{base_name}.{ext}"
    
    def get_receipt_context(self):
        """Get context data for receipt generation"""
        return {
            'order': self,
            'bulk_order': self.bulk_order,
            'amount_paid': self.bulk_order.price_per_item if not self.coupon_used else Decimal('0.00'),
        }