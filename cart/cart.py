# cart/cart.py
from decimal import Decimal
from django.conf import settings
from django.apps import apps
from products.constants import VEST_SIZES
import logging

logger = logging.getLogger(__name__)


class Cart:
    MODEL_MAPPING = {"nysc_kit": "nysckit", "nysc_tour": "nysctour", "church": "church"}

    def validate_product(self, product_type, product_id):
        """
        Check if a product exists and is available for purchase.
        Returns (exists, available, message) tuple.
        """
        try:
            model = apps.get_model("products", self.MODEL_MAPPING[product_type])
            product = model.objects.get(id=product_id)
            if not product.available:
                return True, False, "no longer available"
            if product.out_of_stock:
                return True, False, "out of stock"
            return True, True, None
        except (model.DoesNotExist, LookupError):
            return False, False, "no longer exists"

    @staticmethod
    def get_clothes_sizes():
        """Get available clothing sizes from constants."""
        return VEST_SIZES

    def __init__(self, request):
        """
        Initialize the cart.
        ✅ ENHANCED: Now uses user-specific cart key when authenticated
        """
        self.session = request.session
        self.user = getattr(request, 'user', None)
        
        # ✅ Use user-specific cart key if authenticated
        if self.user and self.user.is_authenticated:
            # Authenticated users get user-specific cart
            cart_key = f"cart_user_{self.user.id}"
            
            # ✅ Migrate anonymous cart to user cart on first login
            anon_cart = self.session.get(settings.CART_SESSION_ID)
            if anon_cart and cart_key not in self.session:
                # Copy anonymous cart to user cart
                self.session[cart_key] = anon_cart
                # Clear anonymous cart
                del self.session[settings.CART_SESSION_ID]
                logger.info(f"Migrated anonymous cart to user {self.user.id}")
        else:
            # Anonymous users use default cart key
            cart_key = settings.CART_SESSION_ID
        
        cart = self.session.get(cart_key)
        if not cart:
            cart = self.session[cart_key] = {}
        
        self.cart = cart
        self.cart_key = cart_key  # Store for later use

    def __iter__(self):
        """Iterate over items in cart and get the products from the database."""
        for item_key in self.cart.keys():
            try:
                # Split our composite key to get product info
                key_parts = item_key.split("|||")
                product_info = key_parts[0]
                product_type, product_id = product_info.split(":::")

                # Get the correct model and fetch the product
                model_name = self.MODEL_MAPPING[product_type]
                model = apps.get_model("products", model_name)
                product = model.objects.get(id=product_id)

                # Create a copy of the cart item data
                item = self.cart[item_key].copy()

                # Add the product object to the item
                item['product'] = product

                # Convert price to Decimal for calculations
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']

                yield item

            except (ValueError, KeyError, LookupError) as e:
                logger.error(f"Error processing cart item: {e}")
                continue

    def generate_item_key(self, product, extra_fields):
        """Generate a unique key for cart items that includes product variations."""
        product_type = product.product_type
        product_id = str(product.id)
        
        # Create base key with product info
        base_key = f"{product_type}:::{product_id}"
        
        # Add extra fields to make the key unique
        if extra_fields:
            # Sort keys to ensure consistent ordering
            sorted_fields = sorted(extra_fields.items())
            fields_str = "|||".join([f"{k}:{v}" for k, v in sorted_fields])
            return f"{base_key}|||{fields_str}"
        
        return base_key

    def add(self, product, quantity=1, override_quantity=False, **extra_fields):
        """
        Add a product to the cart or update its quantity.
        ✅ ENHANCED: Always uses fresh price from database
        """
        # Generate unique key for this item
        item_key = self.generate_item_key(product, extra_fields)
        
        # ✅ ALWAYS use fresh price from database
        current_price = str(product.price)
        
        if item_key not in self.cart:
            # New item - create cart entry
            self.cart[item_key] = {
                'product_id': str(product.id),
                'product_type': product.product_type,
                'quantity': 0,
                'price': current_price,  # ✅ Fresh from database
                'extra_fields': extra_fields,
            }
        else:
            # ✅ Existing item - update price to current database price
            self.cart[item_key]['price'] = current_price
        
        if override_quantity:
            self.cart[item_key]['quantity'] = quantity
        else:
            self.cart[item_key]['quantity'] += quantity
        
        self.save()
        
        logger.debug(f"Cart after add - Key: {item_key}, Item: {self.cart[item_key]}")

    def remove(self, product, extra_fields=None):
        """Remove a specific item from the cart."""
        for item_key in list(self.cart.keys()):
            key_parts = item_key.split("|||")
            product_info = key_parts[0]
            current_type, current_id = product_info.split(":::")

            if current_type == product.product_type and str(current_id) == str(product.id):
                if extra_fields:
                    item_extra_fields = self.cart[item_key].get('extra_fields', {})
                    if item_extra_fields == extra_fields:
                        del self.cart[item_key]
                        self.save()
                        break
                else:
                    del self.cart[item_key]
                    self.save()
                    break

    def __len__(self):
        """Count total items in cart."""
        return sum(item["quantity"] for item in self.cart.values())

    def get_total_price(self):
        """Calculate total price of items in cart."""
        return sum(
            Decimal(item["price"]) * item["quantity"] for item in self.cart.values()
        )

    def clear(self):
        """
        Remove cart from session.
        ✅ ENHANCED: Uses correct cart key
        """
        self.cart = {}
        if self.cart_key in self.session:
            del self.session[self.cart_key]
        self.save()

    def save(self):
        """Mark session as modified to ensure it's saved."""
        self.session.modified = True

    def cleanup(self):
        """
        Remove invalid items from cart.
        Returns dict with lists of removed items and their reasons.
        """
        removed_items = {"deleted": [], "out_of_stock": []}

        cart_keys = list(self.cart.keys())

        for item_key in cart_keys:
            try:
                key_parts = item_key.split("|||")
                product_info = key_parts[0]
                product_type, product_id = product_info.split(":::")

                exists, available, reason = self.validate_product(
                    product_type, product_id
                )

                if not exists or not available:
                    item_info = {
                        "product_type": product_type,
                        "product_id": product_id,
                        "quantity": self.cart[item_key]["quantity"],
                    }

                    del self.cart[item_key]

                    if not exists:
                        removed_items["deleted"].append(item_info)
                    else:
                        removed_items["out_of_stock"].append(item_info)

                    self.save()

            except (ValueError, KeyError) as e:
                logger.error(f"Invalid cart item found during cleanup: {e}")
                del self.cart[item_key]
                self.save()

        return removed_items if any(removed_items.values()) else None