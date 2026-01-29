# bulk_orders/urls.py
# UPDATED: Added verify_payment endpoint documentation

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    BulkOrderLinkViewSet,
    CouponCodeViewSet,
    OrderEntryViewSet,
    bulk_order_payment_webhook,
)

app_name = "bulk_orders"

router = DefaultRouter()
router.register(r'links', BulkOrderLinkViewSet, basename='link')
router.register(r'coupons', CouponCodeViewSet, basename='coupon')
router.register(r'orders', OrderEntryViewSet, basename='order')

urlpatterns = [
    # Webhook endpoint
    path('payment/callback/', bulk_order_payment_webhook, name='payment-webhook'),
    
    # Router URLs
    path('', include(router.urls)),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================

# BULK ORDER LINKS:
# GET    /api/bulk_orders/links/                                  # List all bulk order links (Admin)
# POST   /api/bulk_orders/links/                                  # Create bulk order link (Admin)
# GET    /api/bulk_orders/links/<slug>/                           # Get bulk order details
# POST   /api/bulk_orders/links/<slug>/submit_order/               # Submit order for this bulk order
#        Request body: { "email": "...", "full_name": "...", "size": "...", "coupon_code": "..." }
#
# ORDER MANAGEMENT:
# GET    /api/bulk_orders/orders/                                  # List user's orders (Auth Required)
# GET    /api/bulk_orders/orders/<uuid>/                           # Get specific order (Public)
# POST   /api/bulk_orders/orders/<uuid>/initialize_payment/        # Initialize payment (Public)
#        ✅ NEW: Optional request body: { "callback_url": "https://your-frontend.com/payment/verify" }
#        Returns: { "authorization_url": "...", "reference": "...", "order_reference": "JMW-BULK-1234" }
#
# GET    /api/bulk_orders/orders/<uuid>/verify_payment/            # ✅ NEW: Verify payment status (Public)
#        Returns: { "paid": true/false, "reference": "JMW-BULK-1234", ... }
#
# COUPON MANAGEMENT:
# GET    /api/bulk_orders/coupons/                                 # List coupons (Admin)
# GET    /api/bulk_orders/coupons/?bulk_order_slug=<slug>          # Filter by bulk order
# POST   /api/bulk_orders/coupons/<id>/validate_coupon/            # Validate coupon
#
# PAYMENT:
# POST   /api/bulk_orders/payment/callback/                        # ✅ UPDATED: POST-only webhook (Paystack)
#        ❌ REMOVED: GET response with HTML
#        ✅ NOW: Only accepts POST from Paystack

# ============================================================================
# PAYMENT FLOW (API + FRONTEND)
# ============================================================================
#
# ✅ UPDATED FLOW:
#
# 1. USER SUBMITS ORDER (No auth required)
#    POST /api/bulk_orders/links/<slug>/submit_order/
#    {
#      "email": "user@example.com",
#      "full_name": "John Doe",
#      "size": "L",
#      "coupon_code": "ABC123"  // optional
#    }
#    Returns: { "id": "uuid", "reference": "JMW-BULK-1234", ... }
#
# 2. FRONTEND STORES ORDER INFO
#    Save order UUID and reference to state/localStorage
#
# 3. USER INITIATES PAYMENT
#    POST /api/bulk_orders/orders/<uuid>/initialize_payment/
#    {
#      "callback_url": "https://your-frontend.com/payment/verify"  // optional
#    }
#    Returns: {
#      "authorization_url": "https://paystack.com/...",
#      "reference": "ORDER-xxx-xxx",
#      "order_reference": "JMW-BULK-1234",
#      "amount": 5000.00
#    }
#
# 4. FRONTEND REDIRECTS TO PAYSTACK
#    window.location.href = response.authorization_url
#
# 5. USER COMPLETES PAYMENT ON PAYSTACK
#    Paystack processes payment
#
# 6. PAYSTACK REDIRECTS USER BACK TO FRONTEND
#    URL: https://your-frontend.com/payment/verify?reference=ORDER-xxx-xxx
#
# 7. FRONTEND CALLS VERIFY ENDPOINT
#    GET /api/bulk_orders/orders/<uuid>/verify_payment/
#    Returns: { "paid": true, "reference": "JMW-BULK-1234", ... }
#
# 8. FRONTEND SHOWS SUCCESS/FAILURE
#    if (response.paid) {
#      showSuccess("Payment successful! Order: " + response.reference)
#      navigate('/orders/' + response.order_id)
#    } else {
#      showError("Payment pending or failed")
#      showRetryButton()
#    }
#
# 9. SIMULTANEOUSLY: PAYSTACK SENDS WEBHOOK TO BACKEND
#    POST /api/bulk_orders/payment/callback/ (Server-to-server)
#    Backend updates order.paid = True
#    Backend sends email receipt
#    Backend generates PDF receipt
#
# ============================================================================

# ============================================================================
# FRONTEND EXAMPLE CODE
# ============================================================================
#
# // React/Vue/whatever example
# const PaymentCallback = () => {
#   const [status, setStatus] = useState('loading');
#   const searchParams = new URLSearchParams(window.location.search);
#   const reference = searchParams.get('reference');
#   
#   useEffect(() => {
#     if (reference) {
#       // Extract order UUID from reference: ORDER-{bulk_order_id}-{order_entry_id}
#       const parts = reference.split('-');
#       const orderUuid = parts.slice(6, 11).join('-');
#       
#       // Verify payment status
#       fetch(`/api/bulk_orders/orders/${orderUuid}/verify_payment/`)
#         .then(res => res.json())
#         .then(data => {
#           if (data.paid) {
#             setStatus('success');
#             setTimeout(() => {
#               navigate(`/orders/${data.order_id}`);
#             }, 2000);
#           } else {
#             setStatus('pending');
#           }
#         })
#         .catch(() => setStatus('error'));
#     }
#   }, [reference]);
#   
#   return (
#     <div>
#       {status === 'loading' && <LoadingSpinner />}
#       {status === 'success' && (
#         <div>
#           <h1>✓ Payment Successful!</h1>
#           <p>Your order has been confirmed.</p>
#         </div>
#       )}
#       {status === 'pending' && (
#         <div>
#           <h1>⏳ Payment Pending</h1>
#           <p>Your payment is being processed.</p>
#           <button onClick={recheckPayment}>Check Again</button>
#         </div>
#       )}
#       {status === 'error' && (
#         <div>
#           <h1>❌ Payment Failed</h1>
#           <p>Something went wrong. Please try again.</p>
#           <button onClick={retryPayment}>Retry Payment</button>
#         </div>
#       )}
#     </div>
#   );
# };
#
# ============================================================================

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

# EXAMPLE 1: Submit order (user on page /bulk-order/church-2024-abc1/)
# POST /api/bulk_orders/links/church-2024-abc1/submit_order/
# {
#   "email": "john@example.com",
#   "full_name": "John Doe",
#   "size": "L",
#   "custom_name": "PASTOR JOHN",  // Only if custom_branding_enabled=True
#   "coupon_code": "ABC12345"      // Optional
# }
# Response: { "id": "uuid", "reference": "JMW-BULK-1234", ... }

# EXAMPLE 2: Initialize payment
# POST /api/bulk_orders/orders/{uuid}/initialize_payment/
# {
#   "callback_url": "https://my-frontend.com/payment/verify"  // Optional
# }
# Response: {
#   "authorization_url": "https://checkout.paystack.com/...",
#   "reference": "ORDER-xxx-xxx",
#   "order_reference": "JMW-BULK-1234"
# }

# EXAMPLE 3: Verify payment (after Paystack redirect)
# GET /api/bulk_orders/orders/{uuid}/verify_payment/
# Response: {
#   "paid": true,
#   "reference": "JMW-BULK-1234",
#   "amount": 5000.00,
#   "email": "john@example.com",
#   ...
# }