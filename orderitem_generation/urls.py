# orderitem_generation/urls.py
from django.urls import path
from .api_views import (
    NyscKitPDFView, NyscTourPDFView, ChurchPDFView, AvailableStatesView
)

app_name = "orderitem_generation"

urlpatterns = [
    # PDF generation endpoints
    path('nysc-kit/pdf/', NyscKitPDFView.as_view(), name='nysc-kit-pdf'),
    path('nysc-tour/pdf/', NyscTourPDFView.as_view(), name='nysc-tour-pdf'),
    path('church/pdf/', ChurchPDFView.as_view(), name='church-pdf'),
    
    # Helper endpoint
    path('available-filters/', AvailableStatesView.as_view(), name='available-filters'),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================
# GET    /api/generate/nysc-kit/pdf/?state=<state>     # Generate NYSC Kit PDF
# GET    /api/generate/nysc-tour/pdf/?state=<state>    # Generate NYSC Tour PDF
# GET    /api/generate/church/pdf/?church=<church>     # Generate Church PDF
# GET    /api/generate/available-filters/              # Get available states/churches
#
# ============================================================================
# USAGE EXAMPLES
# ============================================================================
# Generate NYSC Kit orders for Abia:
# GET /api/generate/nysc-kit/pdf/?state=Abia
#
# Generate Tour orders for Lagos:
# GET /api/generate/nysc-tour/pdf/?state=Lagos
#
# Generate Church orders for WINNERS:
# GET /api/generate/church/pdf/?church=WINNERS
#
# Get list of states/churches with orders:
# GET /api/generate/available-filters/