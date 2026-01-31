import secrets
import string
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from cloudinary.models import CloudinaryField
import uuid

User = get_user_model()


def generate_referral_code():
    """Generate a unique 8-character alphanumeric referral code"""
    characters = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(characters) for _ in range(8))
    # Ensure uniqueness
    while ReferrerProfile.objects.filter(referral_code=code).exists():
        code = ''.join(secrets.choice(characters) for _ in range(8))
    return code


class ReferrerProfile(models.Model):
    """
    Referrer profile for authenticated users.
    Each user can only have one referrer profile.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='referrer_profile',
        help_text='User associated with this referrer profile'
    )
    referral_code = models.CharField(
        max_length=8,
        unique=True,
        default=generate_referral_code,
        editable=False,
        help_text='Unique referral code'
    )
    full_name = models.CharField(
        max_length=255,
        help_text='Full name of the referrer'
    )
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        help_text='Contact phone number'
    )
    bank_name = models.CharField(
        max_length=255,
        help_text='Name of the bank'
    )
    account_number = models.CharField(
        max_length=20,
        help_text='Bank account number'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this referrer profile is active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Referrer Profile'
        verbose_name_plural = 'Referrer Profiles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['referral_code']),
            models.Index(fields=['user']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.referral_code})"

    def save(self, *args, **kwargs):
        # Ensure referral code is generated
        if not self.referral_code:
            self.referral_code = generate_referral_code()
        super().save(*args, **kwargs)


class PromotionalMedia(models.Model):
    """
    Admin-managed promotional media for referrers to share.
    Only admin users can upload media.
    """
    MEDIA_TYPE_CHOICES = [
        ('flyer', 'Flyer'),
        ('video', 'Video'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(
        max_length=255,
        help_text='Title of the promotional media'
    )
    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPE_CHOICES,
        help_text='Type of media'
    )
    media_file = CloudinaryField(
        'media',
        resource_type='auto',
        folder='promotional_media',
        blank=True,
        null=True,
        help_text='Promotional media file (image or video)'
    )

    marketing_text = models.TextField(
        help_text='Pre-written marketing text for sharing'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this media is currently active for sharing'
    )
    order = models.IntegerField(
        default=0,
        help_text='Display order (lower numbers appear first)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_promotional_media',
        help_text='Admin user who created this media'
    )

    class Meta:
        verbose_name = 'Promotional Media'
        verbose_name_plural = 'Promotional Media'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'order']),
            models.Index(fields=['media_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_media_type_display()})"

    @property
    def media_url(self):
        """Get the Cloudinary URL for the media file"""
        if self.media_file:
            return self.media_file.url
        return None