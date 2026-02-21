# live_forms/serializers.py
"""
Serializers for Live Forms app.

Mirrors bulk_orders/serializers.py A-Z:
  - LiveFormLinkSummarySerializer  ≡  BulkOrderLinkSummarySerializer
  - LiveFormLinkSerializer         ≡  BulkOrderLinkSerializer
  - LiveFormEntrySerializer        ≡  OrderEntrySerializer

custom_name is:
  - required on write  when custom_branding_enabled=True
  - stripped from output when custom_branding_enabled=False
"""
from rest_framework import serializers
from django.utils import timezone
from .models import LiveFormLink, LiveFormEntry
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LiveFormLinkSummarySerializer
# ---------------------------------------------------------------------------

class LiveFormLinkSummarySerializer(serializers.ModelSerializer):
    """
    Lightweight read-only serializer used when embedding the parent form
    inside LiveFormEntrySerializer. Also returned on public link retrieval
    with social proof block and countdown info.
    """

    is_expired = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    shareable_url = serializers.SerializerMethodField()
    seconds_remaining = serializers.SerializerMethodField()
    total_submissions = serializers.SerializerMethodField()
    social_proof = serializers.SerializerMethodField()

    class Meta:
        model = LiveFormLink
        fields = [
            "id",
            "slug",
            "organization_name",
            "custom_branding_enabled",
            "expires_at",
            "max_submissions",
            "is_active",
            "is_expired",
            "is_open",
            "shareable_url",
            "seconds_remaining",
            "total_submissions",
            "view_count",
            "last_submission_at",
            "social_proof",
            "created_at",
        ]

    def get_is_expired(self, obj: LiveFormLink) -> bool:
        return obj.is_expired()

    def get_is_open(self, obj: LiveFormLink) -> bool:
        return obj.is_open()

    def get_shareable_url(self, obj: LiveFormLink) -> str:
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/live-form/{obj.slug}/")
        return obj.get_shareable_url()

    def get_seconds_remaining(self, obj: LiveFormLink) -> int:
        """
        Seconds until expiry — frontend uses this to seed the countdown timer.
        Returns 0 when already expired (never negative).
        """
        delta = obj.expires_at - timezone.now()
        return max(0, int(delta.total_seconds()))

    def get_total_submissions(self, obj: LiveFormLink) -> int:
        return obj.entries.count()

    def get_social_proof(self, obj: LiveFormLink) -> dict:
        """
        Social proof block returned with every sheet GET.
        recent_submitters: first name + last initial only (privacy).
        """
        recent = (
            obj.entries.order_by("-created_at")
            .values_list("full_name", "created_at")[:5]
        )

        def _truncate(name: str) -> str:
            parts = name.strip().split()
            if len(parts) >= 2:
                return f"{parts[0].capitalize()} {parts[-1][0].upper()}."
            return parts[0].capitalize() if parts else "Anonymous"

        recent_submitters = [
            {"name": _truncate(name), "submitted_at": submitted_at}
            for name, submitted_at in recent
        ]

        submissions_last_hour = obj.entries.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).count()

        return {
            "total_submissions": obj.entries.count(),
            "submissions_last_hour": submissions_last_hour,
            "recent_submitters": recent_submitters,
            "view_count": obj.view_count,
            "last_submission_at": obj.last_submission_at,
        }


# ---------------------------------------------------------------------------
# LiveFormLinkSerializer  (full — admin create / update)
# ---------------------------------------------------------------------------

class LiveFormLinkSerializer(serializers.ModelSerializer):
    """
    Full serializer for admin create/update of LiveFormLink.
    Mirrors BulkOrderLinkSerializer.
    """

    is_expired = serializers.SerializerMethodField()
    is_open = serializers.SerializerMethodField()
    shareable_url = serializers.SerializerMethodField()
    total_submissions = serializers.SerializerMethodField()

    class Meta:
        model = LiveFormLink
        fields = [
            "id",
            "slug",
            "organization_name",
            "custom_branding_enabled",
            "expires_at",
            "max_submissions",
            "is_active",
            "view_count",
            "last_submission_at",
            "created_by",
            "created_at",
            "updated_at",
            "is_expired",
            "is_open",
            "shareable_url",
            "total_submissions",
        ]
        read_only_fields = (
            "id",
            "slug",
            "view_count",
            "last_submission_at",
            "created_by",   # ← ADD THIS
            "created_at",
            "updated_at",
            "is_expired",
            "is_open",
            "shareable_url",
            "total_submissions",
        )

    def get_is_expired(self, obj: LiveFormLink) -> bool:
        return obj.is_expired()

    def get_is_open(self, obj: LiveFormLink) -> bool:
        return obj.is_open()

    def get_shareable_url(self, obj: LiveFormLink) -> str:
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/live-form/{obj.slug}/")
        return obj.get_shareable_url()

    def get_total_submissions(self, obj: LiveFormLink) -> int:
        return obj.entries.count()

    def validate_expires_at(self, value):
        """Expiry must be in the future on creation."""
        if self.instance is None and value <= timezone.now():
            raise serializers.ValidationError(
                "Expiry datetime must be in the future."
            )
        return value


# ---------------------------------------------------------------------------
# LiveFormEntrySerializer  (≡ OrderEntrySerializer)
# ---------------------------------------------------------------------------

class LiveFormEntrySerializer(serializers.ModelSerializer):
    """
    Serializer for participant entries.

    Mirrors OrderEntrySerializer:
      - custom_name required when custom_branding_enabled=True
      - custom_name stripped from output when custom_branding_enabled=False
      - live_form context passed from ViewSet (same pattern as bulk_order context)
    """

    live_form = LiveFormLinkSummarySerializer(read_only=True)
    custom_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = LiveFormEntry
        fields = [
            "id",
            "live_form",
            "serial_number",
            "full_name",
            "custom_name",
            "size",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "id",
            "live_form",
            "serial_number",
            "created_at",
            "updated_at",
        )

    def to_representation(self, instance):
        """
        Strip custom_name from output when custom_branding_enabled=False.
        Mirrors OrderEntrySerializer.to_representation exactly.
        """
        representation = super().to_representation(instance)
        if not instance.live_form.custom_branding_enabled:
            representation.pop("custom_name", None)
        return representation

    def validate(self, attrs):
        """
        Validate against the live_form passed via context (same pattern as
        bulk_orders passing bulk_order via context).
        """
        live_form = self.context.get("live_form")

        if not live_form:
            raise serializers.ValidationError(
                {"live_form": "Live form context is required."}
            )

        # Guard: form must be open
        if not live_form.is_open():
            if not live_form.is_active:
                raise serializers.ValidationError(
                    {"live_form": "This form has been deactivated by the administrator."}
                )
            if live_form.is_expired():
                raise serializers.ValidationError(
                    {"live_form": "This form has expired and is no longer accepting submissions."}
                )
            raise serializers.ValidationError(
                {"live_form": "This form has reached its maximum number of submissions."}
            )

        # Guard: custom_name required when branding enabled
        if live_form.custom_branding_enabled:
            custom_name = attrs.get("custom_name", "").strip()
            if not custom_name:
                raise serializers.ValidationError(
                    {"custom_name": "Custom name is required for this form."}
                )

        return attrs

    def create(self, validated_data):
        live_form = self.context["live_form"]
        validated_data["live_form"] = live_form
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# LiveFormEntryPublicSerializer
# — lightweight version for the live polling feed (no nested form object)
# ---------------------------------------------------------------------------

class LiveFormEntryPublicSerializer(serializers.ModelSerializer):
    """
    Lean serializer for the real-time polling feed.
    Returns only the data needed to render a new row on the live sheet.
    custom_name conditionally included.
    """

    class Meta:
        model = LiveFormEntry
        fields = [
            "id",
            "serial_number",
            "full_name",
            "custom_name",
            "size",
            "created_at",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not instance.live_form.custom_branding_enabled:
            representation.pop("custom_name", None)
        return representation