# payment/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    InitiatePaymentView, VerifyPaymentView, 
    payment_webhook, PaymentTransactionViewSet
)

app_name = "payment"

router = DefaultRouter()
router.register(r'transactions', PaymentTransactionViewSet, basename='transaction')

urlpatterns = [
    # Payment flow
    path('initiate/', InitiatePaymentView.as_view(), name='initiate'),
    path('verify/', VerifyPaymentView.as_view(), name='verify'),
    path('webhook/', payment_webhook, name='webhook'),
    
    # Router URLs
    path('', include(router.urls)),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================
# POST   /api/payment/initiate/              # Initialize payment for pending orders
# GET    /api/payment/verify/?reference=...  # Verify payment status
# POST   /api/payment/webhook/               # Paystack webhook (internal)
#
# GET    /api/payment/transactions/          # List user's payment transactions
# GET    /api/payment/transactions/<id>/     # Get specific payment transaction
#
# ============================================================================
# PAYMENT FLOW
# ============================================================================
# 1. User completes checkout -> Creates orders (pending payment)
# 2. User initiates payment -> POST /api/payment/initiate/
#    Returns: { "authorization_url": "...", "reference": "..." }
# 3. User completes payment on Paystack
# 4. Paystack redirects to verify endpoint -> GET /api/payment/verify/?reference=...
# 5. Backend verifies payment and sends receipts
# 6. Webhook also processes payment in background