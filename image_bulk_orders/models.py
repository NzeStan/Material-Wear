# image_bulk_orders/models.py
"""
Models for Image Bulk Orders app.

EXACT CLONE of bulk_orders models with ONLY addition of optional image field.
"""
import uuid
import string
import random
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from decimal import Decimal
from cloudinary.models import CloudinaryField
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class ImageBulkOrderLink(models.Model):
    """
    Main bulk order link entity.
    IDENTICAL to BulkOrderLink from bulk_orders app.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    organization_name = models.CharField(max_length=255)
    price_per_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    custom_branding_enabled = models.BooleanField(default=False)
    payment_deadline = models.DateTimeField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='image_bulk_orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Auto-generate slug and normalize organization name"""
        try:
            # Normalize organization name to uppercase
            self.organization_name = self.organization_name.upper()
            
            # Generate slug if not exists
            if not self.slug:
                base_slug = slugify(self.organization_name)
                slug = base_slug
                counter = 1
                
                while ImageBulkOrderLink.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                self.slug = slug
                logger.info(f"Generated slug: {self.slug} for organization: {self.organization_name}")
            
            super().save(*args, **kwargs)
            logger.info(f"ImageBulkOrderLink saved successfully: {self.slug}")
        except Exception as e:
            logger.error(f"Error saving ImageBulkOrderLink: {str(e)}")
            raise

    def __str__(self):
        return f"{self.organization_name} - {self.slug}"

    def get_absolute_url(self):
        """Return the shareable URL"""
        return self.get_shareable_url()

    def is_expired(self):
        """Check if payment deadline has passed"""
        return timezone.now() > self.payment_deadline
    
    def get_shareable_url(self):
        """Returns a clean, shareable URL using the slug"""
        return f"/image-bulk-order/{self.slug}/"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Image Bulk Order Link"
        verbose_name_plural = "Image Bulk Order Links"
        indexes = [
            models.Index(
                fields=["created_by", "payment_deadline"],
                name="img_bulk_user_deadline_idx",
            ),
            models.Index(fields=["organization_name"], name="img_bulk_org_name_idx"),
            models.Index(fields=["created_at"], name="img_bulk_created_idx"),
            models.Index(fields=["slug"], name="img_bulk_slug_idx"),
        ]


class ImageCouponCode(models.Model):
    """
    Coupon codes for image bulk orders.
    IDENTICAL to CouponCode from bulk_orders app.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bulk_order = models.ForeignKey(
        ImageBulkOrderLink, on_delete=models.CASCADE, related_name="coupons"
    )
    code = models.CharField(max_length=20, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
            logger.info(f"ImageCouponCode saved successfully: {self.code}")
        except Exception as e:
            logger.error(f"Error saving ImageCouponCode: {str(e)}")
            raise

    def __str__(self):
        return f"{self.code} ({'Used' if self.is_used else 'Available'})"

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["bulk_order", "is_used"], name="img_coupon_bulk_used_idx"
            ),
            models.Index(fields=["code"], name="img_coupon_code_idx"),
        ]


class ImageOrderEntry(models.Model):
    """
    Individual participant entry for image bulk orders.
    IDENTICAL to OrderEntry from bulk_orders BUT with OPTIONAL image field.
    """
    
    SIZE_CHOICES = [
        ("S", "Small"),
        ("M", "Medium"),
        ("L", "Large"),
        ("XL", "Extra Large"),
        ("XXL", "2X Large"),
        ("XXXL", "3X Large"),
        ("XXXXL", "4X Large"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference = models.CharField(max_length=20, unique=True)
    bulk_order = models.ForeignKey(
        "ImageBulkOrderLink", on_delete=models.CASCADE, related_name="orders"
    )
    serial_number = models.PositiveIntegerField(editable=False)
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    custom_name = models.CharField(max_length=255, blank=True)
    
    # ✅ NEW: Optional image field (stored in Cloudinary)
    image = CloudinaryField(
        'image',
        null=True,
        blank=True,
        folder='image_bulk_orders',
        help_text='Optional image upload (will be organized by order slug and size)'
    )
    
    coupon_used = models.ForeignKey(
        "ImageCouponCode", null=True, blank=True, on_delete=models.SET_NULL
    )
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        """Auto-generate reference and serial_number on first save"""
        # Generate reference if not exists
        if not self.reference:
            self.reference = self._generate_reference()
            logger.info(f"Generated reference: {self.reference}")

        # Auto-increment serial_number within bulk_order
        if not self.serial_number:
            last_order = ImageOrderEntry.objects.filter(
                bulk_order=self.bulk_order
            ).order_by('-serial_number').first()
            
            self.serial_number = (last_order.serial_number + 1) if last_order else 1
            logger.info(f"Assigned serial_number: {self.serial_number} for bulk_order: {self.bulk_order.slug}")

        super().save(*args, **kwargs)
        logger.info(f"ImageOrderEntry saved: {self.reference}")

    def _generate_reference(self):
        """Generate unique reference like IMG-BULK-1234"""
        while True:
            reference = f"IMG-BULK-{random.randint(1000, 9999)}"
            if not ImageOrderEntry.objects.filter(reference=reference).exists():
                return reference

    def __str__(self):
        return f"{self.serial_number}. {self.full_name} ({self.size})"

    class Meta:
        ordering = ["bulk_order", "serial_number"]
        verbose_name = "Image Order Entry"
        verbose_name_plural = "Image Order Entries"
        unique_together = [["bulk_order", "serial_number"]]
        indexes = [
            models.Index(
                fields=["bulk_order", "serial_number"], name="img_order_bulk_serial_idx"
            ),
            models.Index(fields=["email"], name="img_order_email_idx"),
            models.Index(fields=["paid"], name="img_order_paid_idx"),
            models.Index(fields=["size"], name="img_order_size_idx"),
            models.Index(fields=["created_at"], name="img_order_created_idx"),
            models.Index(fields=["updated_at"], name="img_order_updated_idx"),
            models.Index(fields=["reference"], name="img_order_reference_idx"),
        ]
