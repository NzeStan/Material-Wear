# clothing_image_orders/urls.py
"""
URL configuration for clothing image orders API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClothingImageOrderViewSet,
    ClothingOrderParticipantViewSet,
    ClothingCouponCodeViewSet,
    clothing_payment_webhook,
)

app_name = "clothing_image_orders"

router = DefaultRouter()
router.register(r'orders', ClothingImageOrderViewSet, basename='order')
router.register(r'participants', ClothingOrderParticipantViewSet, basename='participant')
router.register(r'coupons', ClothingCouponCodeViewSet, basename='coupon')

urlpatterns = [
    # Webhook endpoint
    path('payment/webhook/', clothing_payment_webhook, name='payment-webhook'),
    
    # Router URLs
    path('', include(router.urls)),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================

# CLOTHING IMAGE ORDERS:
# GET    /api/clothing_image_orders/orders/                         # List orders (Auth: Admin)
# POST   /api/clothing_image_orders/orders/                         # Create order (Auth: Admin)
# GET    /api/clothing_image_orders/orders/<reference>/             # Get order details (Public)
# PUT    /api/clothing_image_orders/orders/<reference>/             # Update order (Auth: Admin)
# DELETE /api/clothing_image_orders/orders/<reference>/             # Delete order (Auth: Admin)
#
# POST   /api/clothing_image_orders/orders/<reference>/submit_participant/
#        Submit new participant to order (Public)
#        Request body: {
#          "email": "user@example.com",
#          "full_name": "John Doe",
#          "phone": "08012345678",
#          "size": "L",
#          "custom_name": "PASTOR JOHN",  // optional
#          "image": <file>,  // optional or required based on order settings
#          "coupon_code": "ABC123"  // optional
#        }
#
# POST   /api/clothing_image_orders/orders/<reference>/generate_coupons/
#        Generate coupon codes (Auth: Admin)
#        Request body: { "count": 50 }
#
# GET    /api/clothing_image_orders/orders/<reference>/stats/
#        Get order statistics (Public)
#
# PARTICIPANTS:
# GET    /api/clothing_image_orders/participants/                   # List participants
#        Query params: ?email=user@example.com&order=CLO-XXXXX
#
# GET    /api/clothing_image_orders/participants/<reference>/       # Get participant details (Public)
#
# POST   /api/clothing_image_orders/participants/<reference>/initialize_payment/
#        Initialize payment for participant (Public)
#        Optional request body: { "callback_url": "https://..." }
#        Returns: {
#          "authorization_url": "https://paystack.com/...",
#          "reference": "CLO-PAY-xxx-xxx",
#          "participant_reference": "CLOP-XXXXX",
#          "amount": 5000.00
#        }
#
# GET    /api/clothing_image_orders/participants/<reference>/verify_payment/
#        Verify payment status (Public)
#        Returns: { "paid": true/false, "reference": "CLOP-XXXXX", ... }
#
# COUPONS:
# GET    /api/clothing_image_orders/coupons/                        # List coupons (Auth: Admin)
#        Query params: ?order=CLO-XXXXX&is_used=false
#
# POST   /api/clothing_image_orders/coupons/<id>/validate_coupon/
#        Validate coupon code (Public)
#        Request body: { "order_reference": "CLO-XXXXX" }
#        Returns: { "valid": true/false, "message": "...", "discount": 5000.00 }
#
# PAYMENT WEBHOOK:
# POST   /api/clothing_image_orders/payment/webhook/                # Paystack webhook (Public)
#        ⚠️ Only called by Paystack, signature verified

# ============================================================================
# PAYMENT FLOW
# ============================================================================
#
# 1. USER SUBMITS PARTICIPANT INFO (Public)
#    POST /api/clothing_image_orders/orders/<reference>/submit_participant/
#    {
#      "email": "user@example.com",
#      "full_name": "John Doe",
#      "phone": "08012345678",
#      "size": "L",
#      "custom_name": "PASTOR JOHN",
#      "image": <file>,
#      "coupon_code": "ABC123"  // optional
#    }
#    Returns: { "id": "uuid", "reference": "CLOP-XXXXX", ... }
#
# 2. FRONTEND STORES PARTICIPANT INFO
#    Save participant UUID and reference to state/localStorage
#
# 3. USER INITIATES PAYMENT
#    POST /api/clothing_image_orders/participants/<reference>/initialize_payment/
#    { "callback_url": "https://your-frontend.com/payment/verify" }
#    Returns: { "authorization_url": "https://paystack.com/..." }
#
# 4. FRONTEND REDIRECTS TO PAYSTACK
#    window.location.href = response.authorization_url
#
# 5. USER COMPLETES PAYMENT ON PAYSTACK
#    Paystack processes payment
#
# 6. PAYSTACK REDIRECTS USER BACK TO FRONTEND
#    URL: https://your-frontend.com/payment/verify?reference=CLO-PAY-xxx-xxx
#
# 7. FRONTEND CALLS VERIFY ENDPOINT
#    GET /api/clothing_image_orders/participants/<reference>/verify_payment/
#    Returns: { "paid": true, "reference": "CLOP-XXXXX", ... }
#
# 8. FRONTEND SHOWS SUCCESS/FAILURE
#    if (response.paid) {
#      showSuccess("Payment successful! Reference: " + response.reference)
#    } else {
#      showError("Payment pending or failed")
#    }
#
# 9. PAYSTACK WEBHOOK CONFIRMS PAYMENT (Background)
#    POST /api/clothing_image_orders/payment/webhook/
#    This updates participant.paid = True in the background

# ============================================================================
# ADMIN DOCUMENT GENERATION
# ============================================================================
#
# Admin can generate comprehensive document packages through Django Admin:
#
# 1. Select a clothing image order in the admin
# 2. Choose "Download Complete Package" from actions dropdown
# 3. System generates ZIP file containing:
#    - order_details.pdf
#    - order_details.docx  
#    - order_details.xlsx
#    - images/
#      - size_S/
#        - 001_JOHN_DOE.jpg (or PASTOR_JOHN.jpg if custom_name provided)
#      - size_M/
#      - size_L/
#      - size_XL/
#      - etc.
#
# Images are automatically downloaded from Cloudinary and organized by size.
# Filenames use custom_name if provided, otherwise serial_number + full_name.