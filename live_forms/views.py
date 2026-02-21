# live_forms/views.py
"""
Views for Live Forms app.

Mirrors bulk_orders/views.py A-Z, minus all payment logic.

Public endpoints:
  GET  /api/live_forms/forms/<slug>/            — sheet detail + social proof
  POST /api/live_forms/forms/<slug>/submit/     — submit an entry
  GET  /api/live_forms/forms/<slug>/entries/    — all entries (for live feed)
  GET  /api/live_forms/forms/<slug>/live_feed/  — social proof + recent rows

Admin-only:
  CRUD on LiveFormLink
  GET  /api/live_forms/forms/<slug>/admin_entries/ — full entry list
  GET  /api/live_forms/entries/<uuid>/            — retrieve single entry
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET
from django.db.models import Count, F
from django.utils import timezone
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse
from .models import LiveFormLink, LiveFormEntry
from .serializers import (
    LiveFormLinkSerializer,
    LiveFormLinkSummarySerializer,
    LiveFormEntrySerializer,
    LiveFormEntryPublicSerializer,
)
from .utils import (
    generate_live_form_pdf,
    generate_live_form_word,
    generate_live_form_excel,
)
from jmw.throttling import LiveFormSubmitThrottle, LiveFormViewThrottle
from jmw.background_utils import send_live_form_submission_email_async
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# sheet_view  — serves the interactive live spreadsheet HTML page
# Route: GET /live-form/<slug>/
# ---------------------------------------------------------------------------

@require_GET
def sheet_view(request, slug):
    """
    Serves the interactive Google Sheets-style page participants land on.
    Passes bootstrap data the JS needs:
      - form metadata (title, expiry, custom_branding_enabled)
      - initial entries (all existing rows on page load)
      - size choices for the submission row dropdown
    The rest is driven by client-side JS polling:
      GET /api/live_forms/forms/<slug>/live_feed/?since=<ts>
    """
    live_form = get_object_or_404(LiveFormLink, slug=slug)

    # Atomic view count increment
    LiveFormLink.objects.filter(pk=live_form.pk).update(view_count=F("view_count") + 1)
    live_form.refresh_from_db()

    entries = live_form.entries.all().order_by("serial_number")

    context = {
        "live_form": live_form,
        "entries": entries,
        "is_open": live_form.is_open(),
        "is_expired": live_form.is_expired(),
        "seconds_remaining": max(
            0, int((live_form.expires_at - timezone.now()).total_seconds())
        ),
        "total_entries": entries.count(),
        "size_choices": LiveFormEntry.SIZE_CHOICES,
    }
    return render(request, "live_forms/sheet.html", context)


# ---------------------------------------------------------------------------
# LiveFormLinkViewSet  (≡ BulkOrderLinkViewSet)
# ---------------------------------------------------------------------------

class LiveFormLinkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LiveFormLink.

    Admin: full CRUD + document download actions.
    Public: retrieve by slug (GET only).
    """

    serializer_class = LiveFormLinkSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def get_queryset(self):
        if self.request.user.is_staff:
            return (
                LiveFormLink.objects.all()
                .annotate(entry_count=Count("entries"))
                .order_by("-created_at")
            )
        if self.request.user.is_authenticated:
            return (
                LiveFormLink.objects.filter(created_by=self.request.user)
                .annotate(entry_count=Count("entries"))
                .order_by("-created_at")
            )
        # Public: only active, not-yet-expired forms (for slug lookup)
        return (
            LiveFormLink.objects.filter(is_active=True)
            .annotate(entry_count=Count("entries"))
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.action == "retrieve" and not self.request.user.is_authenticated:
            return LiveFormLinkSummarySerializer
        return LiveFormLinkSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    # ── Public: retrieve with view-count increment ──────────────────────

    def retrieve(self, request, *args, **kwargs):
        """
        Public GET on a live form slug.
        Increments view_count atomically and returns the full summary
        including social proof and countdown seed (seconds_remaining).
        """
        instance = self.get_object()

        # Atomic view count increment — no lost-update race condition
        LiveFormLink.objects.filter(pk=instance.pk).update(
            view_count=F("view_count") + 1
        )
        instance.refresh_from_db(fields=["view_count"])

        serializer_class = (
            LiveFormLinkSummarySerializer
            if not request.user.is_authenticated
            else LiveFormLinkSerializer
        )
        serializer = serializer_class(instance, context={"request": request})
        return Response(serializer.data)

    # ── submit  (≡ BulkOrderLinkViewSet.submit_order) ──────────────────

    @extend_schema(
        request=LiveFormEntrySerializer,
        responses={201: LiveFormEntrySerializer, 400: OpenApiResponse(description="Validation error")},
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny],
        throttle_classes=[LiveFormSubmitThrottle],
        url_path="submit",
    )
    def submit(self, request, slug=None):
        """
        Public endpoint. Submit a single entry to a live form.
        Enforces form-open guard (expiry, is_active, max_submissions)
        via serializer validation — same pattern as bulk_orders submit_order.
        """
        try:
            live_form = LiveFormLink.objects.get(slug=slug)
        except LiveFormLink.DoesNotExist:
            return Response(
                {"error": "Live form not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = LiveFormEntrySerializer(
            data=request.data,
            context={"live_form": live_form, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        entry = serializer.save()

        # Background email (if email field ever added; no-op guard inside util)
        try:
            send_live_form_submission_email_async(str(entry.id))
        except Exception as e:
            logger.warning(f"Could not queue submission email: {str(e)}")

        logger.info(
            f"New LiveFormEntry #{entry.serial_number} submitted to '{slug}'"
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ── live_feed  (public polling endpoint for real-time rows) ────────

    @extend_schema(
        responses={200: LiveFormEntryPublicSerializer(many=True)},
    )
    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
        throttle_classes=[LiveFormViewThrottle],
        url_path="live_feed",
    )
    def live_feed(self, request, slug=None):
        """
        Public polling endpoint.
        Returns all rows + social proof block. Accepts optional
        `since` query param (ISO datetime) to return only NEW rows
        since the last poll — keeping payloads tiny after initial load.

        Frontend polls every 4 seconds, sending:
          GET /api/live_forms/forms/<slug>/live_feed/?since=<last_updated_at>

        Response always includes the form's social_proof block so the
        counter and recent-submitters strip stay fresh.
        """
        try:
            live_form = LiveFormLink.objects.get(slug=slug)
        except LiveFormLink.DoesNotExist:
            return Response(
                {"error": "Live form not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        since_raw = request.query_params.get("since")
        entries_qs = live_form.entries.all().order_by("serial_number")

        if since_raw:
            try:
                since_dt = timezone.datetime.fromisoformat(
                    since_raw.replace("Z", "+00:00")
                )
                entries_qs = entries_qs.filter(created_at__gt=since_dt)
            except (ValueError, TypeError):
                pass  # bad since param → return all entries

        entries_serializer = LiveFormEntryPublicSerializer(
            entries_qs, many=True, context={"request": request}
        )

        # Lightweight social proof for counter strip refresh
        form_serializer = LiveFormLinkSummarySerializer(
            live_form, context={"request": request}
        )

        return Response(
            {
                "form": {
                    "slug": live_form.slug,
                    "is_open": live_form.is_open(),
                    "is_expired": live_form.is_expired(),
                    "seconds_remaining": max(
                        0,
                        int(
                            (live_form.expires_at - timezone.now()).total_seconds()
                        ),
                    ),
                    "social_proof": form_serializer.data.get("social_proof", {}),
                },
                "entries": entries_serializer.data,
                "server_time": timezone.now().isoformat(),
            }
        )

    # ── admin_entries  (admin-only full entry list for a form) ──────────

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAdminUser],
        url_path="admin_entries",
    )
    def admin_entries(self, request, slug=None):
        """Admin: full entry list with all fields."""
        live_form = self.get_object()
        entries = live_form.entries.all().order_by("serial_number")
        serializer = LiveFormEntrySerializer(
            entries, many=True, context={"request": request}
        )
        return Response(serializer.data)

    # ── Document download actions (≡ bulk_orders admin actions via API) ─

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAdminUser],
        url_path="download_pdf",
    )
    def download_pdf(self, request, slug=None):
        """Admin: download PDF report for this live form."""
        live_form = self.get_object()
        try:
            return generate_live_form_pdf(live_form, request)
        except ImportError:
            return Response(
                {"error": "PDF generation not available. Install GTK+ libraries."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.error(f"PDF generation error for '{slug}': {str(e)}")
            return Response(
                {"error": f"PDF generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAdminUser],
        url_path="download_word",
    )
    def download_word(self, request, slug=None):
        """Admin: download Word document for this live form."""
        live_form = self.get_object()
        try:
            return generate_live_form_word(live_form)
        except Exception as e:
            logger.error(f"Word generation error for '{slug}': {str(e)}")
            return Response(
                {"error": f"Word document generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.IsAdminUser],
        url_path="download_excel",
    )
    def download_excel(self, request, slug=None):
        """Admin: download Excel spreadsheet for this live form."""
        live_form = self.get_object()
        try:
            return generate_live_form_excel(live_form)
        except Exception as e:
            logger.error(f"Excel generation error for '{slug}': {str(e)}")
            return Response(
                {"error": f"Excel generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# ---------------------------------------------------------------------------
# LiveFormEntryViewSet  (≡ OrderEntryViewSet)
# ---------------------------------------------------------------------------

class LiveFormEntryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for LiveFormEntry.

    Public:
      - retrieve  (GET /entries/<uuid>/) — anyone with UUID can view their row
    Admin:
      - list, destroy
    """

    serializer_class = LiveFormEntrySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        if self.action in ["retrieve"]:
            return LiveFormEntry.objects.all().select_related("live_form")

        if self.action == "list":
            if self.request.user.is_staff:
                return LiveFormEntry.objects.all().select_related("live_form")
            return LiveFormEntry.objects.none()

        return LiveFormEntry.objects.all().select_related("live_form")

    def get_permissions(self):
        if self.action in ["list", "destroy", "update", "partial_update"]:
            return [permissions.IsAdminUser()]
        return [permissions.AllowAny()]