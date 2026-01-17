# order/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import CheckoutView, OrderViewSet

app_name = "order"

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='order')

urlpatterns = [
    # Checkout endpoint
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    
    # Router URLs (orders CRUD)
    path('', include(router.urls)),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================
# POST   /api/order/checkout/                  # Create orders from cart
# GET    /api/order/                           # List user's orders
# GET    /api/order/<id>/                      # Get specific order details
# GET    /api/order/<id>/receipt/              # Get order receipt
#
# ============================================================================
# CHECKOUT REQUEST FORMAT
# ============================================================================
# All orders require base fields:
# {
#   "first_name": "John",
#   "middle_name": "A",      // Optional (REQUIRED for NYSC Tour orders)
#   "last_name": "Doe",
#   "phone_number": "08012345678"
# }
#
# For NYSC Kit orders (additional fields):
# {
#   ...base fields,
#   "call_up_number": "AB/22C/1234",  // Your NYSC call-up number
#   "state": "Abia",
#   "local_government": "Aba North"
# }
#
# For Church orders (additional fields):
# {
#   ...base fields,
#   "pickup_on_camp": true,                    // Default: true
#   "delivery_state": "Lagos",                 // Required if pickup_on_camp=false
#   "delivery_lga": "Ikeja"                    // Required if pickup_on_camp=false
# }
#
# For NYSC Tour orders:
# {
#   ...base fields only
#   // Note: call_up_number is stored in cart item, not in checkout
# }
#
# ============================================================================
# IMPORTANT CHANGES
# ============================================================================
# - call_up_number is now used as the state_code field for NYSC Kit orders
# - Format: XX/YYX/ZZZZ (e.g., AB/22C/1234)
# - This field is required during checkout for NYSC Kit orders
# - The call_up_number is stored in the order's call_up_number field 
#   (previously called state_code)
#
# Note: The system automatically creates separate orders for each product type in cart