# cart/urls.py
from django.urls import path
from .api_views import (
    CartDetailView, AddToCartView, UpdateCartItemView,
    RemoveFromCartView, ClearCartView, CartSummaryView
)

app_name = "cart"

urlpatterns = [
    # Cart operations
    path('', CartDetailView.as_view(), name='cart-detail'),
    path('summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('add/', AddToCartView.as_view(), name='cart-add'),
    path('update/<str:item_key>/', UpdateCartItemView.as_view(), name='cart-update'),
    path('remove/<str:item_key>/', RemoveFromCartView.as_view(), name='cart-remove'),
    path('clear/', ClearCartView.as_view(), name='cart-clear'),
]

# ============================================================================
# AVAILABLE ENDPOINTS
# ============================================================================
# GET    /api/cart/                          # Get full cart with all items
# GET    /api/cart/summary/                  # Get cart count and total only (lightweight)
# POST   /api/cart/add/                      # Add item to cart
# PATCH  /api/cart/update/<item_key>/        # Update item quantity
# DELETE /api/cart/remove/<item_key>/        # Remove specific item
# POST   /api/cart/clear/                    # Clear entire cart
#
# ============================================================================
# ADD TO CART REQUEST FORMAT
# ============================================================================
# 
# For NYSC Kit (Kakhi):
# NOTE: Kakhi uses user's measurement - user MUST have a measurement profile
# {
#   "product_type": "nysc_kit",
#   "product_id": "uuid-here",
#   "quantity": 1
# }
# Size is automatically set to "measurement" and measurement_id is retrieved from user's profile
# Users without measurements will receive an error asking them to create a measurement first
#
# For NYSC Kit (Cap):
# {
#   "product_type": "nysc_kit",
#   "product_id": "uuid-here",
#   "quantity": 1
# }
# Size is automatically set to "free_size"
#
# For NYSC Kit (Vest):
# {
#   "product_type": "nysc_kit",
#   "product_id": "uuid-here",
#   "quantity": 1,
#   "size": "M"  // Required: XS, S, M, L, XL, XXL, XXXL
# }
#
# For NYSC Tour:
# {
#   "product_type": "nysc_tour",
#   "product_id": "uuid-here",
#   "quantity": 1,
#   "call_up_number": "AB/22C/1234"
# }
#
# For Church:
# {
#   "product_type": "church",
#   "product_id": "uuid-here",
#   "quantity": 1,
#   "size": "XL",
#   "custom_name_text": "PASTOR JOHN"  // Optional
# }
#
# ============================================================================
# IMPORTANT NOTES
# ============================================================================
# - Kakhi products REQUIRE users to have a measurement profile
# - Cap products use fixed "free_size"
# - Vest products require size selection from dropdown
# - Size options: XS, S, M, L, XL, XXL, XXXL