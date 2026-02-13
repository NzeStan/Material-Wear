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
    path('payment/callback/', image_bulk_order_payment_webhook, name='payment-webhook'),
    path('', include(router.urls)),
]
