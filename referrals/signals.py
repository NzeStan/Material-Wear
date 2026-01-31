from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import ReferrerProfile, PromotionalMedia


User = get_user_model()


@receiver(pre_save, sender=ReferrerProfile)
def ensure_unique_referral_code(sender, instance, **kwargs):
    """
    Ensure referral code is unique before saving.
    This is a backup to the model's unique constraint.
    """
    if not instance.referral_code:
        from .models import generate_referral_code
        instance.referral_code = generate_referral_code()


@receiver(post_save, sender=ReferrerProfile)
def log_referrer_profile_creation(sender, instance, created, **kwargs):
    """
    Log when a new referrer profile is created.
    You can extend this to send welcome emails, notifications, etc.
    """
    if created:
        # Log the creation
        print(f"New referrer profile created: {instance.full_name} ({instance.referral_code})")
        
        # TODO: Send welcome email with referral code
        # TODO: Send admin notification
        # TODO: Create initial analytics record


@receiver(post_save, sender=PromotionalMedia)
def log_promotional_media_creation(sender, instance, created, **kwargs):
    """
    Log when new promotional media is created.
    """
    if created:
        print(f"New promotional media created: {instance.title} ({instance.media_type})")
        
        # TODO: Notify all active referrers about new media
        # TODO: Cache invalidation if using caching