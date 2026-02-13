# image_bulk_orders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ImageBulkOrderLinkViewSet,
    ImageCouponCodeViewSet,
    ImageOrderEntryViewSet,
    image_bulk_order_payment_webhook,
)

app_name = "image_bulk_orders"

router = DefaultRouter()
router.register(r'links', ImageBulkOrderLinkViewSet, basename='link')
router.register(r'coupons', ImageCouponCodeViewSet, basename='coupon')
router.register(r'orders', ImageOrderEntryViewSet, basename='order')

urlpatterns = [
    # Webhook endpoint (routes through webhook_router)
    path('payment/callback/', image_bulk_order_payment_webhook, name='payment-webhook'),
    
    # Router URLs
    path('', include(router.urls)),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================
# GET    /api/image_bulk_orders/links/                              # List all links (Admin)
# POST   /api/image_bulk_orders/links/                              # Create link (Admin)
# GET    /api/image_bulk_orders/links/<slug>/                       # Get link details
# POST   /api/image_bulk_orders/links/<slug>/submit_order/          # Submit order
# GET    /api/image_bulk_orders/links/<slug>/paid_orders/           # Social proof page
# POST   /api/image_bulk_orders/links/<slug>/generate_coupons/      # Generate coupons
# 
# GET    /api/image_bulk_orders/orders/                             # List user's orders
# GET    /api/image_bulk_orders/orders/<uuid>/                      # Get specific order
# POST   /api/image_bulk_orders/orders/<uuid>/initialize_payment/   # Initialize payment
# GET    /api/image_bulk_orders/orders/<uuid>/verify_payment/       # Verify payment
#
# POST   /api/image_bulk_orders/payment/callback/                   # Paystack webhook