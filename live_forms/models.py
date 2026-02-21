# live_forms/models.py
"""
Models for Live Forms app.

Google Sheets-style, no-payment collaborative data collection.
Admin generates an expirable shareable link → participants fill
a browser-native spreadsheet (full_name, custom_name, size) in
real time with all rows visible. Admin exports PDF / Word / Excel.

Architecture mirrors bulk_orders A-Z, minus all payment logic.
"""
import uuid
from django.db import models, transaction
from django.db.models import Max
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LiveFormLink  (≡ BulkOrderLink minus price_per_item)
# ---------------------------------------------------------------------------

class LiveFormLink(models.Model):
    """
    Master link entity. Admin creates this; the slug becomes the
    public URL token shared with participants.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(
        max_length=300,
        unique=True,
        editable=False,
        help_text="Auto-generated from organization name.",
    )
    organization_name = models.CharField(max_length=255)
    custom_branding_enabled = models.BooleanField(
        default=False,
        help_text=(
            "When enabled, a 'Custom Name' column is added to the live sheet "
            "and included in all admin exports."
        ),
    )

    # Renamed from payment_deadline — no payment context here
    expires_at = models.DateTimeField(
        help_text=(
            "The form locks automatically at this datetime. "
            "The live sheet shows a real-time countdown to this moment."
        )
    )

    # Optional hard cap on submissions
    max_submissions = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Leave blank for unlimited submissions.",
    )

    # Manual kill switch — mirrors is_active pattern used across project
    is_active = models.BooleanField(
        default=True,
        help_text="Deactivate to close the form immediately, regardless of expiry.",
    )

    # Social proof counters — updated atomically via F() / update() on every interaction
    view_count = models.PositiveIntegerField(default=0)
    last_submission_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="live_form_links",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        """Auto-generate slug and normalize organization name."""
        try:
            self.organization_name = self.organization_name.upper()

            if not self.slug:
                base_slug = slugify(self.organization_name)
                slug = base_slug
                counter = 1
                while LiveFormLink.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                self.slug = slug
                logger.info(
                    f"Generated slug '{self.slug}' for LiveFormLink: {self.organization_name}"
                )

            super().save(*args, **kwargs)
            logger.info(f"LiveFormLink saved: {self.slug}")
        except Exception as e:
            logger.error(f"Error saving LiveFormLink: {str(e)}")
            raise

    def __str__(self):
        return f"{self.organization_name} — {self.slug}"

    def get_absolute_url(self):
        return self.get_shareable_url()

    def is_expired(self):
        """True when the expiry datetime has passed."""
        return timezone.now() > self.expires_at

    def is_open(self):
        """
        True only when the form is active, not expired, and below
        the max-submissions cap (if one is set).
        Queryset-safe: uses .count() which hits the DB index.
        """
        if not self.is_active:
            return False
        if self.is_expired():
            return False
        if self.max_submissions is not None:
            if self.entries.count() >= self.max_submissions:
                return False
        return True

    def get_shareable_url(self):
        """
        Returns an absolute URL when settings.FRONTEND_URL is configured,
        otherwise falls back to a relative path.
        Always use this method — never hardcode the slug path directly.
        """
        from django.conf import settings as _settings
        base = getattr(_settings, "FRONTEND_URL", "").rstrip("/")
        if base:
            return f"{base}/live-form/{self.slug}/"
        return f"/live-form/{self.slug}/"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Live Form Link"
        verbose_name_plural = "Live Form Links"
        indexes = [
            models.Index(
                fields=["created_by", "expires_at"],
                name="liveform_user_expiry_idx",
            ),
            models.Index(
                fields=["organization_name"],
                name="liveform_org_name_idx",
            ),
            models.Index(fields=["created_at"], name="liveform_created_idx"),
            models.Index(fields=["slug"], name="liveform_slug_idx"),
            models.Index(fields=["is_active"], name="liveform_active_idx"),
        ]


# ---------------------------------------------------------------------------
# LiveFormEntry  (≡ OrderEntry minus all payment / coupon fields)
# ---------------------------------------------------------------------------

class LiveFormEntry(models.Model):
    """
    A single participant's row on the live sheet.
    Mirrors OrderEntry — serial_number auto-increments per form,
    names are normalised to uppercase, custom_name only populated
    when LiveFormLink.custom_branding_enabled is True.
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
    live_form = models.ForeignKey(
        LiveFormLink,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    serial_number = models.PositiveIntegerField(editable=False)
    full_name = models.CharField(max_length=255)
    custom_name = models.CharField(max_length=255, blank=True)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ------------------------------------------------------------------
    def save(self, *args, **kwargs):
        """
        Auto-assign serial_number (race-condition safe via select_for_update),
        normalise names to uppercase, update social proof counters atomically.
        """
        # Normalise names
        self.full_name = self.full_name.upper()
        if self.custom_name:
            self.custom_name = self.custom_name.upper()

        # Auto-increment serial_number — race-condition safe
        if not self.serial_number:
            with transaction.atomic():
                # Lock parent row to prevent concurrent serial collisions
                LiveFormLink.objects.select_for_update().get(id=self.live_form_id)
                max_serial = LiveFormEntry.objects.filter(
                    live_form=self.live_form
                ).aggregate(Max("serial_number"))["serial_number__max"]
                self.serial_number = (max_serial or 0) + 1

        try:
            super().save(*args, **kwargs)

            # Atomically update social proof counters on parent (no race condition)
            LiveFormLink.objects.filter(pk=self.live_form_id).update(
                last_submission_at=timezone.now()
            )

            logger.info(
                f"LiveFormEntry saved: #{self.serial_number} "
                f"for form '{self.live_form.slug}'"
            )
        except Exception as e:
            logger.error(f"Error saving LiveFormEntry: {str(e)}")
            raise

    def __str__(self):
        return (
            f"#{self.serial_number} — {self.full_name} "
            f"({self.live_form.organization_name})"
        )

    class Meta:
        ordering = ["live_form", "serial_number"]
        verbose_name = "Live Form Entry"
        verbose_name_plural = "Live Form Entries"
        unique_together = [["live_form", "serial_number"]]
        indexes = [
            models.Index(
                fields=["live_form", "serial_number"],
                name="liveform_entry_serial_idx",
            ),
            models.Index(
                fields=["live_form", "created_at"],
                name="liveform_entry_created_idx",
            ),
            models.Index(fields=["full_name"], name="liveform_entry_name_idx"),
            models.Index(fields=["size"], name="liveform_entry_size_idx"),
            models.Index(fields=["updated_at"], name="liveform_entry_updated_idx"),
        ]