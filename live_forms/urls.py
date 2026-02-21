# live_forms/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LiveFormLinkViewSet, LiveFormEntryViewSet

app_name = "live_forms"

router = DefaultRouter()
router.register(r"forms", LiveFormLinkViewSet, basename="form")
router.register(r"entries", LiveFormEntryViewSet, basename="entry")

urlpatterns = [
    path("", include(router.urls)),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================
#
# LIVE FORM LINKS:
# GET    /api/live_forms/forms/                         List (admin/owner)
# POST   /api/live_forms/forms/                         Create (admin)
# GET    /api/live_forms/forms/<slug>/                  Public detail + social proof + countdown seed
# PATCH  /api/live_forms/forms/<slug>/                  Update (admin)
# DELETE /api/live_forms/forms/<slug>/                  Delete (admin)
#
# PUBLIC ACTIONS:
# POST   /api/live_forms/forms/<slug>/submit/           Submit entry (public, throttled)
# GET    /api/live_forms/forms/<slug>/live_feed/        Real-time polling feed (public, throttled)
#        Optional: ?since=<ISO datetime>  → returns only new rows since that time
#
# ADMIN ACTIONS:
# GET    /api/live_forms/forms/<slug>/admin_entries/    Full entry list (admin only)
# GET    /api/live_forms/forms/<slug>/download_pdf/     Download PDF   (admin only)
# GET    /api/live_forms/forms/<slug>/download_word/    Download Word  (admin only)
# GET    /api/live_forms/forms/<slug>/download_excel/   Download Excel (admin only)
#
# ENTRIES:
# GET    /api/live_forms/entries/                       List all (admin only)
# GET    /api/live_forms/entries/<uuid>/                Retrieve single entry (public)
# DELETE /api/live_forms/entries/<uuid>/                Delete (admin only)