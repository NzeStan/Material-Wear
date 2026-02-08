# image_bulk_orders/urls.py
"""
URL Configuration for Image Bulk Orders API.

Routes:
- /api/image-bulk-orders/links/ - Bulk order links CRUD
- /api/image-bulk-orders/orders/ - Order entries (read-only)
- /api/image-bulk-orders/coupons/ - Coupon codes (admin only)
- /webhooks/image-bulk-order-payment/ - Payment webhook
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ImageBulkOrderLinkViewSet,
    ImageOrderEntryViewSet,
    ImageCouponCodeViewSet,
    image_bulk_order_payment_webhook,
)

app_name = 'image_bulk_orders'

# API Router
router = DefaultRouter()
router.register(r'links', ImageBulkOrderLinkViewSet, basename='link')
router.register(r'orders', ImageOrderEntryViewSet, basename='order')
router.register(r'coupons', ImageCouponCodeViewSet, basename='coupon')

urlpatterns = [
    # API endpoints
    path('image-bulk-orders/', include(router.urls)),
    
    # Webhook endpoint
    path('webhook/', image_bulk_order_payment_webhook, name='payment-webhook'),
]