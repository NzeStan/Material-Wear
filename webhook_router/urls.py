# webhook_router/urls.py
from django.urls import path
from .views import router_webhook

app_name = "webhook_router"

urlpatterns = [
    path('', router_webhook, name='webhook-router'),
]

# ============================================================================
# WEBHOOK ROUTER
# ============================================================================
# POST   /api/webhook/                       # Universal webhook endpoint
#
# Routes webhooks to appropriate handlers based on reference format:
# - "ORDER-{bulk_order_id}-{order_entry_id}" -> Bulk order webhook
# - Any other format -> Regular order webhook