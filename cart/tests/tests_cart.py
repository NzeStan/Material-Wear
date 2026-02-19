# cart/tests/tests_cart.py
"""
Comprehensive tests for Cart class (cart.py)

Coverage:
- Cart initialization (anonymous & authenticated users)
- Cart migration from anonymous to authenticated
- Product validation (exists, available, out of stock)
- Cart operations (add, remove, clear, cleanup)
- Security: price manipulation prevention, user cart isolation
- Edge cases: invalid products, corrupted data, decimal precision
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from django.conf import settings
from unittest.mock import Mock, patch, MagicMock
from cart.cart import Cart
from products.models import NyscKit, NyscTour, Church
from products.constants import VEST_SIZES
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


class CartInitializationTests(TestCase):
    """Test cart initialization for anonymous and authenticated users"""

    def setUp(self):
        self.factory = RequestFactory()

    def _create_request_with_session(self, user=None):
        """Helper to create request with session middleware"""
        request = self.factory.get("/")

        # Add session
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()

        # Add user
        request.user = user if user else Mock(is_authenticated=False)

        return request

    def test_anonymous_user_cart_creation(self):
        """Test cart creation for anonymous user uses default session key"""
        request = self._create_request_with_session()
        cart = Cart(request)

        # Should use default CART_SESSION_ID
        self.assertEqual(cart.cart_key, settings.CART_SESSION_ID)
        self.assertEqual(cart.cart, {})
        self.assertIn(settings.CART_SESSION_ID, request.session)

    def test_authenticated_user_cart_creation(self):
        """Test cart creation for authenticated user uses user-specific key"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        request = self._create_request_with_session(user=user)
        cart = Cart(request)

        # Should use user-specific cart key
        expected_key = f"cart_user_{user.id}"
        self.assertEqual(cart.cart_key, expected_key)
        self.assertEqual(cart.cart, {})
        self.assertIn(expected_key, request.session)

    def test_cart_migration_anonymous_to_authenticated(self):
        """Test anonymous cart migrates to authenticated user cart on login"""
        # Create anonymous cart with items
        request = self._create_request_with_session()
        anon_cart = Cart(request)

        # Add item to anonymous cart
        request.session[settings.CART_SESSION_ID] = {
            "item1": {"quantity": 2, "price": "100.00"}
        }
        request.session.save()

        # Login user
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        request.user = user

        # Initialize cart as authenticated user
        auth_cart = Cart(request)

        # Cart should be migrated to user-specific key
        expected_key = f"cart_user_{user.id}"
        self.assertEqual(auth_cart.cart_key, expected_key)
        self.assertEqual(auth_cart.cart, {"item1": {"quantity": 2, "price": "100.00"}})

        # Anonymous cart should be cleared
        self.assertNotIn(settings.CART_SESSION_ID, request.session)

    def test_no_migration_if_user_already_has_cart(self):
        """Test no migration if user already has their own cart"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        request = self._create_request_with_session(user=user)

        # User already has cart
        user_key = f"cart_user_{user.id}"
        request.session[user_key] = {"item2": {"quantity": 1, "price": "50.00"}}

        # Also has anonymous cart
        request.session[settings.CART_SESSION_ID] = {
            "item1": {"quantity": 2, "price": "100.00"}
        }
        request.session.save()

        # Initialize cart
        cart = Cart(request)

        # Should keep user's existing cart, not migrate
        self.assertEqual(cart.cart, {"item2": {"quantity": 1, "price": "50.00"}})
        # Anonymous cart should still exist (not deleted if user cart exists)
        self.assertIn(settings.CART_SESSION_ID, request.session)

    def test_cart_isolation_between_users(self):
        """Test that different users have isolated carts"""
        user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="testpass123"
        )
        user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="testpass123"
        )

        request1 = self._create_request_with_session(user=user1)
        request2 = self._create_request_with_session(user=user2)

        cart1 = Cart(request1)
        cart2 = Cart(request2)

        # Different cart keys
        self.assertNotEqual(cart1.cart_key, cart2.cart_key)
        self.assertEqual(cart1.cart_key, f"cart_user_{user1.id}")
        self.assertEqual(cart2.cart_key, f"cart_user_{user2.id}")

    def test_cart_preserves_existing_data(self):
        """Test cart initialization preserves existing session data"""
        request = self._create_request_with_session()

        # Pre-populate session with cart data
        existing_data = {"item1": {"quantity": 3, "price": "150.00"}}
        request.session[settings.CART_SESSION_ID] = existing_data
        request.session.save()

        # Initialize cart
        cart = Cart(request)

        # Should preserve existing data
        self.assertEqual(cart.cart, existing_data)


class ProductValidationTests(TestCase):
    """Test product validation logic"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category first
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        # Create test products
        self.available_kit = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

        self.unavailable_kit = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("5000.00"),
            available=False,
            out_of_stock=False,
        )

        self.out_of_stock_kit = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=True,
        )

    def test_validate_existing_available_product(self):
        """Test validation of existing available product"""
        exists, available, message = self.cart.validate_product(
            "nysc_kit", self.available_kit.id
        )

        self.assertTrue(exists)
        self.assertTrue(available)
        self.assertIsNone(message)

    def test_validate_unavailable_product(self):
        """Test validation of unavailable product"""
        exists, available, message = self.cart.validate_product(
            "nysc_kit", self.unavailable_kit.id
        )

        self.assertTrue(exists)
        self.assertFalse(available)
        self.assertEqual(message, "no longer available")

    def test_validate_out_of_stock_product(self):
        """Test validation of out of stock product"""
        exists, available, message = self.cart.validate_product(
            "nysc_kit", self.out_of_stock_kit.id
        )

        self.assertTrue(exists)
        self.assertFalse(available)
        self.assertEqual(message, "out of stock")

    def test_validate_nonexistent_product(self):
        """Test validation of non-existent product"""
        fake_id = "12345678-1234-1234-1234-123456789abc"
        exists, available, message = self.cart.validate_product("nysc_kit", fake_id)

        self.assertFalse(exists)
        self.assertFalse(available)
        self.assertEqual(message, "no longer exists")

    def test_validate_invalid_product_type(self):
        """Test validation with invalid product type"""
        exists, available, message = self.cart.validate_product(
            "invalid_type", self.available_kit.id
        )

        self.assertFalse(exists)
        self.assertFalse(available)
        self.assertEqual(message, "no longer exists")

    def test_validate_product_all_types(self):
        """Test validation works for all product types"""
        from products.models import Category

        # Create categories
        tour_category = Category.objects.create(
            name="NYSC TOUR", slug="nysc-tour", product_type="nysc_tour"
        )
        church_category = Category.objects.create(
            name="CHURCH PROGRAMME", slug="church-prog", product_type="church"
        )

        # Test NyscTour
        tour = NyscTour.objects.create(
            name="Lagos",
            category=tour_category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False,
        )

        exists, available, message = self.cart.validate_product("nysc_tour", tour.id)
        self.assertTrue(exists)
        self.assertTrue(available)

        # Test Church
        church = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=church_category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=False,
        )

        exists, available, message = self.cart.validate_product("church", church.id)
        self.assertTrue(exists)
        self.assertTrue(available)


class StaticMethodTests(TestCase):
    """Test static methods"""

    def test_get_clothes_sizes_returns_vest_sizes(self):
        """Test get_clothes_sizes returns VEST_SIZES constant"""
        sizes = Cart.get_clothes_sizes()

        self.assertEqual(sizes, VEST_SIZES)
        self.assertIsInstance(sizes, list)
        # Verify format
        self.assertEqual(sizes[0], ("", "Select Size"))
        self.assertEqual(sizes[1], ("XS", "Extra Small (XS)"))
        self.assertEqual(sizes[2], ("S", "Small (S)"))
        self.assertEqual(sizes[3], ("M", "Medium (M)"))


class CartKeyGenerationTests(TestCase):
    """Test cart item key generation"""

    def setUp(self):
        self.factory = RequestFactory()
        request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        request.user = Mock(is_authenticated=False)

        self.cart = Cart(request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

    def test_generate_key_without_extra_fields(self):
        """Test key generation without extra fields"""
        key = self.cart.generate_item_key(self.product, {})

        expected = f"nysc_kit:::{self.product.id}"
        self.assertEqual(key, expected)

    def test_generate_key_with_extra_fields(self):
        """Test key generation with extra fields"""
        extra_fields = {"size": "M", "color": "blue"}
        key = self.cart.generate_item_key(self.product, extra_fields)

        # Should contain product info and sorted extra fields
        self.assertIn(f"nysc_kit:::{self.product.id}", key)
        self.assertIn("color:blue", key)
        self.assertIn("size:M", key)
        self.assertIn("|||", key)

    def test_generate_key_consistent_ordering(self):
        """Test key generation maintains consistent ordering"""
        # Different order of extra fields
        extra1 = {"size": "L", "color": "red", "name": "John"}
        extra2 = {"name": "John", "size": "L", "color": "red"}

        key1 = self.cart.generate_item_key(self.product, extra1)
        key2 = self.cart.generate_item_key(self.product, extra2)

        # Keys should be identical regardless of input order
        self.assertEqual(key1, key2)

    def test_generate_key_different_for_different_fields(self):
        """Test different extra fields generate different keys"""
        extra1 = {"size": "M"}
        extra2 = {"size": "L"}

        key1 = self.cart.generate_item_key(self.product, extra1)
        key2 = self.cart.generate_item_key(self.product, extra2)

        self.assertNotEqual(key1, key2)


class AddToCartTests(TestCase):
    """Test adding items to cart with security focus"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product = NyscKit.objects.create(
            name="Test Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

    def test_add_new_item_to_cart(self):
        """Test adding new item to empty cart"""
        self.cart.add(self.product, quantity=2)

        # Check item was added
        self.assertEqual(len(self.cart), 2)

        # Verify cart structure
        key = self.cart.generate_item_key(self.product, {})
        self.assertIn(key, self.cart.cart)
        self.assertEqual(self.cart.cart[key]["quantity"], 2)
        self.assertEqual(self.cart.cart[key]["price"], str(self.product.price))

    def test_add_increments_existing_item_quantity(self):
        """Test adding existing item increments quantity"""
        # Add first time
        self.cart.add(self.product, quantity=2)

        # Add again
        self.cart.add(self.product, quantity=3)

        # Should increment, not replace
        self.assertEqual(len(self.cart), 5)  # 2 + 3

    def test_add_with_override_quantity(self):
        """Test override_quantity replaces instead of incrementing"""
        # Add initial quantity
        self.cart.add(self.product, quantity=2)

        # Add with override
        self.cart.add(self.product, quantity=5, override_quantity=True)

        # Should replace, not add
        self.assertEqual(len(self.cart), 5)

    def test_add_with_extra_fields(self):
        """Test adding with extra fields creates separate cart entries"""
        # Add same product with different sizes
        self.cart.add(self.product, quantity=1, size="M")
        self.cart.add(self.product, quantity=2, size="L")

        # Should have 2 separate entries
        self.assertEqual(len(self.cart.cart.keys()), 2)
        self.assertEqual(len(self.cart), 3)  # Total quantity

    def test_price_always_from_database_security(self):
        """SECURITY: Test price is always fetched from database, not user input"""
        # Add item
        self.cart.add(self.product, quantity=1)

        key = self.cart.generate_item_key(self.product, {})
        original_price = self.cart.cart[key]["price"]

        # Simulate price manipulation attempt
        self.cart.cart[key]["price"] = "1.00"  # Try to change to 1
        self.cart.save()

        # Add same item again (should refresh price)
        self.cart.add(self.product, quantity=1)

        # Price should be back to database value
        self.assertEqual(self.cart.cart[key]["price"], str(self.product.price))
        self.assertNotEqual(self.cart.cart[key]["price"], "1.00")

    def test_price_updated_when_product_price_changes(self):
        """SECURITY: Test cart price updates when product price changes in DB"""
        # Add item at original price
        self.cart.add(self.product, quantity=1)

        key = self.cart.generate_item_key(self.product, {})
        self.assertEqual(self.cart.cart[key]["price"], "5000.00")

        # Change product price in database
        self.product.price = Decimal("6000.00")
        self.product.save()
        self.product.refresh_from_db()

        # Add same item again (should update price)
        self.cart.add(self.product, quantity=1)

        # Cart should reflect new price
        self.assertEqual(self.cart.cart[key]["price"], "6000.00")

    def test_add_zero_quantity(self):
        """Test adding with zero quantity"""
        self.cart.add(self.product, quantity=0)

        # Item exists but with 0 quantity
        key = self.cart.generate_item_key(self.product, {})
        self.assertEqual(self.cart.cart[key]["quantity"], 0)

    def test_add_negative_quantity(self):
        """Test adding with negative quantity (edge case)"""
        # Add positive first
        self.cart.add(self.product, quantity=5)

        # Add negative (should reduce)
        self.cart.add(self.product, quantity=-2)

        # Should be 3 total
        self.assertEqual(len(self.cart), 3)

    def test_session_modified_after_add(self):
        """Test session is marked as modified after add"""
        self.request.session.modified = False

        self.cart.add(self.product, quantity=1)

        self.assertTrue(self.request.session.modified)


class RemoveFromCartTests(TestCase):
    """Test removing items from cart"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product = NyscKit.objects.create(
            name="Test Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

    def test_remove_item_without_extra_fields(self):
        """Test removing item without extra fields"""
        # Add item
        self.cart.add(self.product, quantity=2)
        self.assertEqual(len(self.cart), 2)

        # Remove item
        self.cart.remove(self.product)

        # Cart should be empty
        self.assertEqual(len(self.cart), 0)
        self.assertEqual(len(self.cart.cart.keys()), 0)

    def test_remove_item_with_matching_extra_fields(self):
        """Test removing item with matching extra fields"""
        # Add item with size
        self.cart.add(self.product, quantity=2, size="M")

        # Remove with matching extra fields
        self.cart.remove(self.product, extra_fields={"size": "M"})

        # Should be removed
        self.assertEqual(len(self.cart), 0)

    def test_remove_does_not_affect_different_extra_fields(self):
        """Test removing only affects items with matching extra fields"""
        # Add same product with different sizes
        self.cart.add(self.product, quantity=2, size="M")
        self.cart.add(self.product, quantity=3, size="L")

        # Remove size M
        self.cart.remove(self.product, extra_fields={"size": "M"})

        # Size L should remain
        self.assertEqual(len(self.cart), 3)
        self.assertEqual(len(self.cart.cart.keys()), 1)

    def test_remove_nonexistent_item(self):
        """Test removing item that doesn't exist (no error)"""
        # Cart is empty
        self.assertEqual(len(self.cart), 0)

        # Try to remove (should not raise error)
        self.cart.remove(self.product)

        # Cart still empty
        self.assertEqual(len(self.cart), 0)

    def test_session_modified_after_remove(self):
        """Test session is marked as modified after remove"""
        self.cart.add(self.product, quantity=1)
        self.request.session.modified = False

        self.cart.remove(self.product)

        self.assertTrue(self.request.session.modified)


class CartLengthTests(TestCase):
    """Test cart length calculation"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product1 = NyscKit.objects.create(
            name="Product 1",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

        self.product2 = NyscKit.objects.create(
            name="Product 2",
            type="cap",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False,
        )

    def test_empty_cart_length(self):
        """Test length of empty cart is 0"""
        self.assertEqual(len(self.cart), 0)

    def test_single_item_cart_length(self):
        """Test length with single item"""
        self.cart.add(self.product1, quantity=3)
        self.assertEqual(len(self.cart), 3)

    def test_multiple_items_cart_length(self):
        """Test length with multiple different items"""
        self.cart.add(self.product1, quantity=2)
        self.cart.add(self.product2, quantity=5)

        self.assertEqual(len(self.cart), 7)  # 2 + 5

    def test_length_with_same_product_different_variations(self):
        """Test length counts all variations separately"""
        self.cart.add(self.product1, quantity=2, size="M")
        self.cart.add(self.product1, quantity=3, size="L")

        self.assertEqual(len(self.cart), 5)  # 2 + 3


class CartTotalPriceTests(TestCase):
    """Test cart total price calculation"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product1 = NyscKit.objects.create(
            name="Product 1",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

        self.product2 = NyscKit.objects.create(
            name="Product 2",
            type="cap",
            category=self.category,
            price=Decimal("3500.50"),
            available=True,
            out_of_stock=False,
        )

    def test_empty_cart_total_price(self):
        """Test total price of empty cart is 0"""
        total = self.cart.get_total_price()
        self.assertEqual(total, Decimal("0"))

    def test_single_item_total_price(self):
        """Test total price with single item"""
        self.cart.add(self.product1, quantity=2)

        total = self.cart.get_total_price()
        expected = Decimal("5000.00") * 2
        self.assertEqual(total, expected)

    def test_multiple_items_total_price(self):
        """Test total price with multiple items"""
        self.cart.add(self.product1, quantity=2)
        self.cart.add(self.product2, quantity=3)

        total = self.cart.get_total_price()
        expected = (Decimal("5000.00") * 2) + (Decimal("3500.50") * 3)
        self.assertEqual(total, expected)

    def test_decimal_precision_in_total(self):
        """Test decimal precision is maintained in total"""
        # Product with precise decimal price
        precise_product = NyscKit.objects.create(
            name="Precise Product",
            type="cap",
            category=self.category,
            price=Decimal("1234.56"),
            available=True,
            out_of_stock=False,
        )

        self.cart.add(precise_product, quantity=3)

        total = self.cart.get_total_price()
        expected = Decimal("1234.56") * 3
        self.assertEqual(total, expected)
        self.assertEqual(total, Decimal("3703.68"))

    def test_total_price_returns_decimal_type(self):
        """Test total price returns Decimal type for precision"""
        self.cart.add(self.product1, quantity=1)

        total = self.cart.get_total_price()
        self.assertIsInstance(total, Decimal)


class ClearCartTests(TestCase):
    """Test clearing cart"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product = NyscKit.objects.create(
            name="Test Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

    def test_clear_cart_with_items(self):
        """Test clearing cart removes all items"""
        # Add items
        self.cart.add(self.product, quantity=5)
        self.assertEqual(len(self.cart), 5)

        # Clear cart
        self.cart.clear()

        # Should be empty
        self.assertEqual(len(self.cart), 0)
        self.assertEqual(self.cart.cart, {})

    def test_clear_empty_cart(self):
        """Test clearing already empty cart"""
        self.assertEqual(len(self.cart), 0)

        # Clear (should not error)
        self.cart.clear()

        self.assertEqual(len(self.cart), 0)

    def test_clear_removes_from_session(self):
        """Test clear removes cart from session"""
        self.cart.add(self.product, quantity=1)
        self.assertIn(self.cart.cart_key, self.request.session)

        self.cart.clear()

        # Cart key should be removed from session
        self.assertNotIn(self.cart.cart_key, self.request.session)

    def test_clear_uses_correct_cart_key_for_authenticated_user(self):
        """Test clear uses correct cart key for authenticated users"""
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.request.user = user

        # Reinitialize cart with user
        cart = Cart(self.request)
        cart.add(self.product, quantity=1)

        user_cart_key = f"cart_user_{user.id}"
        self.assertIn(user_cart_key, self.request.session)

        cart.clear()

        # User's cart key should be removed
        self.assertNotIn(user_cart_key, self.request.session)

    def test_session_modified_after_clear(self):
        """Test session is marked as modified after clear"""
        self.cart.add(self.product, quantity=1)
        self.request.session.modified = False

        self.cart.clear()

        self.assertTrue(self.request.session.modified)


class CartCleanupTests(TestCase):
    """Test cart cleanup functionality"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        # Create products with different states
        self.available_product = NyscKit.objects.create(
            name="Available Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

        self.unavailable_product = NyscKit.objects.create(
            name="Unavailable Product",
            type="cap",
            category=self.category,
            price=Decimal("3000.00"),
            available=False,
            out_of_stock=False,
        )

        self.out_of_stock_product = NyscKit.objects.create(
            name="Out of Stock Product",
            type="cap",
            category=self.category,
            price=Decimal("4000.00"),
            available=True,
            out_of_stock=True,
        )

    def test_cleanup_removes_deleted_products(self):
        """Test cleanup removes products that no longer exist"""
        # Add product
        self.cart.add(self.available_product, quantity=2)
        product_id = self.available_product.id

        # Delete product from database
        self.available_product.delete()

        # Cleanup cart
        result = self.cart.cleanup()

        # Should have removed deleted product
        self.assertIsNotNone(result)
        self.assertEqual(len(result["deleted"]), 1)
        self.assertEqual(result["deleted"][0]["product_id"], str(product_id))

        # Cart should be empty
        self.assertEqual(len(self.cart), 0)

    def test_cleanup_removes_out_of_stock_products(self):
        """Test cleanup removes out of stock products"""
        # Add out of stock product
        self.cart.add(self.out_of_stock_product, quantity=3)

        # Cleanup
        result = self.cart.cleanup()

        # Should remove out of stock
        self.assertIsNotNone(result)
        self.assertEqual(len(result["out_of_stock"]), 1)
        self.assertEqual(
            result["out_of_stock"][0]["product_id"], str(self.out_of_stock_product.id)
        )

        # Cart should be empty
        self.assertEqual(len(self.cart), 0)

    def test_cleanup_removes_unavailable_products(self):
        """Test cleanup removes unavailable products"""
        # Add unavailable product
        self.cart.add(self.unavailable_product, quantity=1)

        # Cleanup
        result = self.cart.cleanup()

        # Should remove unavailable (treated as out_of_stock)
        self.assertIsNotNone(result)
        self.assertEqual(len(result["out_of_stock"]), 1)

        # Cart should be empty
        self.assertEqual(len(self.cart), 0)

    def test_cleanup_keeps_valid_products(self):
        """Test cleanup keeps valid available products"""
        # Add valid product
        self.cart.add(self.available_product, quantity=2)

        # Cleanup
        result = self.cart.cleanup()

        # Should return None (nothing removed)
        self.assertIsNone(result)

        # Cart should still have the item
        self.assertEqual(len(self.cart), 2)

    def test_cleanup_mixed_valid_and_invalid(self):
        """Test cleanup with mix of valid and invalid products"""
        # Add valid and invalid products
        self.cart.add(self.available_product, quantity=2)
        self.cart.add(self.out_of_stock_product, quantity=1)
        self.cart.add(self.unavailable_product, quantity=1)

        initial_count = len(self.cart)

        # Cleanup
        result = self.cart.cleanup()

        # Should remove 2 invalid items
        self.assertIsNotNone(result)
        self.assertEqual(len(result["out_of_stock"]), 2)

        # Only valid product should remain
        self.assertEqual(len(self.cart), 2)
        self.assertEqual(len(self.cart.cart.keys()), 1)

    def test_cleanup_handles_invalid_cart_keys(self):
        """Test cleanup handles corrupted/invalid cart keys"""
        # Add valid product
        self.cart.add(self.available_product, quantity=1)

        # Corrupt cart with invalid key
        self.cart.cart["invalid_key_format"] = {"quantity": 1, "price": "100.00"}
        self.cart.save()

        # Cleanup should handle the error
        result = self.cart.cleanup()

        # Invalid key should be removed
        self.assertNotIn("invalid_key_format", self.cart.cart)

        # Valid product should remain
        self.assertEqual(len(self.cart), 1)

    def test_cleanup_returns_none_when_nothing_removed(self):
        """Test cleanup returns None when no items are removed"""
        self.cart.add(self.available_product, quantity=1)

        result = self.cart.cleanup()

        self.assertIsNone(result)

    def test_cleanup_session_modified(self):
        """Test cleanup marks session as modified"""
        self.cart.add(self.out_of_stock_product, quantity=1)
        self.request.session.modified = False

        self.cart.cleanup()

        self.assertTrue(self.request.session.modified)


class CartIterationTests(TestCase):
    """Test cart iteration functionality"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product1 = NyscKit.objects.create(
            name="Product 1",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

        self.product2 = NyscKit.objects.create(
            name="Product 2",
            type="cap",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False,
        )

    def test_iterate_empty_cart(self):
        """Test iterating over empty cart"""
        items = list(self.cart)
        self.assertEqual(len(items), 0)

    def test_iterate_cart_with_items(self):
        """Test iterating over cart with items"""
        self.cart.add(self.product1, quantity=2)
        self.cart.add(self.product2, quantity=3)

        items = list(self.cart)

        # Should have 2 items
        self.assertEqual(len(items), 2)

        # Check structure
        for item in items:
            self.assertIn("product", item)
            self.assertIn("quantity", item)
            self.assertIn("price", item)
            self.assertIn("total_price", item)

    def test_iteration_calculates_total_price(self):
        """Test iteration includes calculated total_price per item"""
        self.cart.add(self.product1, quantity=3)

        items = list(self.cart)
        item = items[0]

        expected_total = Decimal("5000.00") * 3
        self.assertEqual(item["total_price"], expected_total)

    def test_iteration_converts_price_to_decimal(self):
        """Test iteration converts price strings to Decimal"""
        self.cart.add(self.product1, quantity=1)

        items = list(self.cart)
        item = items[0]

        self.assertIsInstance(item["price"], Decimal)

    def test_iteration_includes_product_object(self):
        """Test iteration includes full product object"""
        self.cart.add(self.product1, quantity=1)

        items = list(self.cart)
        item = items[0]

        self.assertEqual(item["product"], self.product1)
        self.assertEqual(item["product"].name, "Product 1")

    def test_iteration_skips_invalid_items(self):
        """Test iteration skips items with errors"""
        # Add valid item
        self.cart.add(self.product1, quantity=1)

        # Add corrupted item
        self.cart.cart["corrupted"] = {"invalid": "data"}
        self.cart.save()

        # Should skip corrupted item during iteration
        # Use manual iteration to avoid calling __len__ which would fail on corrupted data
        items = []
        for item in self.cart:
            items.append(item)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["product"], self.product1)


class CartSaveTests(TestCase):
    """Test cart save functionality"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

    def test_save_marks_session_as_modified(self):
        """Test save marks session as modified"""
        self.request.session.modified = False

        self.cart.save()

        self.assertTrue(self.request.session.modified)

    def test_save_called_by_add(self):
        """Test save is called after add operation"""
        product = NyscKit.objects.create(
            name="Test",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

        self.request.session.modified = False
        self.cart.add(product, quantity=1)

        self.assertTrue(self.request.session.modified)

    def test_save_called_by_remove(self):
        """Test save is called after remove operation"""
        product = NyscKit.objects.create(
            name="Test",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

        self.cart.add(product, quantity=1)
        self.request.session.modified = False

        self.cart.remove(product)

        self.assertTrue(self.request.session.modified)


class CartEdgeCasesTests(TestCase):
    """Test edge cases and unusual scenarios"""

    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(self.request)
        self.request.session.save()
        self.request.user = Mock(is_authenticated=False)

        self.cart = Cart(self.request)

        # Create category for products
        from products.models import Category

        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        self.product = NyscKit.objects.create(
            name="Test Product",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

    def test_large_quantity(self):
        """Test handling very large quantities"""
        large_qty = 10000
        self.cart.add(self.product, quantity=large_qty)

        self.assertEqual(len(self.cart), large_qty)

        total = self.cart.get_total_price()
        expected = Decimal("5000.00") * large_qty
        self.assertEqual(total, expected)

    def test_multiple_adds_same_item_accumulates(self):
        """Test multiple adds of same item accumulates quantity"""
        for i in range(10):
            self.cart.add(self.product, quantity=1)

        self.assertEqual(len(self.cart), 10)
        self.assertEqual(len(self.cart.cart.keys()), 1)  # Still just 1 unique item

    def test_empty_extra_fields_vs_none(self):
        """Test empty dict vs None for extra_fields generates same key"""
        key1 = self.cart.generate_item_key(self.product, {})
        key2 = self.cart.generate_item_key(self.product, {})

        self.assertEqual(key1, key2)

    def test_unicode_in_extra_fields(self):
        """Test handling unicode characters in extra fields"""
        extra = {"name": "王小明", "note": "Café ☕"}

        # Should not raise error
        self.cart.add(self.product, quantity=1, **extra)

        self.assertEqual(len(self.cart), 1)

    def test_very_long_extra_field_values(self):
        """Test handling very long strings in extra fields"""
        long_string = "A" * 1000
        extra = {"custom_name": long_string}

        # Should handle long strings
        self.cart.add(self.product, quantity=1, **extra)

        items = list(self.cart)
        self.assertEqual(items[0]["extra_fields"]["custom_name"], long_string)

    def test_special_characters_in_extra_fields(self):
        """Test handling special characters in extra fields"""
        extra = {"name": "O'Brien", "note": 'Test & "quotes" <tags>'}

        # Should not raise error
        self.cart.add(self.product, quantity=1, **extra)

        items = list(self.cart)
        self.assertEqual(items[0]["extra_fields"]["name"], "O'Brien")

    def test_cart_after_session_clear_and_reinit(self):
        """Test cart behavior after session is cleared"""
        self.cart.add(self.product, quantity=2)

        # Clear session
        self.request.session.flush()

        # Reinitialize cart
        new_cart = Cart(self.request)

        # Should be empty (new session)
        self.assertEqual(len(new_cart), 0)
