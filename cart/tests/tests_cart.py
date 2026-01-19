# cart/tests/tests_cart.py
"""
Comprehensive tests for Cart class
Tests core cart functionality, product validation, and session management
"""
from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from products.models import Category, NyscKit, NyscTour, Church
from measurement.models import Measurement
from cart.cart import Cart
import uuid

User = get_user_model()


class BaseCartTestCase(TestCase):
    """Base test case with common helper methods"""
    
    def setUp(self):
        """Set up common test data"""
        self.factory = RequestFactory()
    
    def get_request_with_session(self, user=None):
        """Helper to create request with session"""
        request = self.factory.get('/')
        middleware = SessionMiddleware(lambda x: x)
        middleware.process_request(request)
        request.session.save()
        request.user = user
        return request


class CartInitializationTest(BaseCartTestCase):
    """Test Cart initialization and session handling"""

    def test_cart_initialization_anonymous(self):
        """Test cart initializes for anonymous user"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        self.assertIsNotNone(cart.cart)
        self.assertIsInstance(cart.cart, dict)
        self.assertEqual(len(cart.cart), 0)

    def test_cart_initialization_authenticated(self):
        """Test cart initializes for authenticated user"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        request = self.get_request_with_session(user=user)
        cart = Cart(request)
        
        self.assertIsNotNone(cart.cart)
        # Should use user-specific cart key
        expected_key = f'cart_user_{user.id}'
        self.assertEqual(cart.cart_key, expected_key)

    def test_cart_persists_in_session(self):
        """Test cart data persists in session"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        # Add some data
        cart.cart['test'] = {'quantity': 1}
        cart.save()
        
        # Create new cart instance
        cart2 = Cart(request)
        self.assertIn('test', cart2.cart)

    def test_anonymous_cart_migration_on_login(self):
        """Test anonymous cart migrates to user cart on login"""
        # Create anonymous cart
        request = self.get_request_with_session()
        cart = Cart(request)
        cart.cart['anon_item'] = {'quantity': 2}
        cart.save()
        
        # Login user
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        request.user = user
        
        # Create cart for authenticated user
        cart_auth = Cart(request)
        
        # Anonymous cart should be migrated
        self.assertIn('anon_item', cart_auth.cart)


class CartAddItemTest(BaseCartTestCase):
    """Test Cart.add() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )
        
        self.tour = NyscTour.objects.create(
            name='Camp Tour',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )

    def test_add_item_to_empty_cart(self):
        """Test adding item to empty cart"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=1, size='M')
        
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart.get_total_price(), Decimal('2000.00'))

    def test_add_item_increments_quantity(self):
        """Test adding same item increments quantity"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        cart.add(self.vest, quantity=3, size='M')
        
        self.assertEqual(len(cart), 5)

    def test_add_item_with_override(self):
        """Test adding with override replaces quantity"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        cart.add(self.vest, quantity=5, size='M', override_quantity=True)
        
        self.assertEqual(len(cart), 5)

    def test_add_different_items(self):
        """Test adding different products"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        cart.add(self.tour, quantity=1, call_up_number='AB/22C/1234')
        
        self.assertEqual(len(cart), 3)

    def test_add_same_product_different_extra_fields(self):
        """Test adding same product with different extra fields creates separate items"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=1, size='M')
        cart.add(self.vest, quantity=1, size='L')
        
        self.assertEqual(len(cart.cart), 2)  # Two separate items

    def test_add_uses_current_price(self):
        """Test adding item uses current database price"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        # Add item
        cart.add(self.vest, quantity=1, size='M')
        
        # Change price
        self.vest.price = Decimal('2500.00')
        self.vest.save()
        
        # Add again - should use new price
        cart.add(self.vest, quantity=1, size='M')
        
        # Check price in cart was updated
        item_key = list(cart.cart.keys())[0]
        self.assertEqual(Decimal(cart.cart[item_key]['price']), Decimal('2500.00'))

    def test_add_with_extra_fields_stored(self):
        """Test extra fields are stored correctly"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=1, size='XL', custom_field='test')
        
        item_key = list(cart.cart.keys())[0]
        extra_fields = cart.cart[item_key]['extra_fields']
        
        self.assertEqual(extra_fields['size'], 'XL')
        self.assertEqual(extra_fields['custom_field'], 'test')


class CartRemoveItemTest(BaseCartTestCase):
    """Test Cart.remove() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_remove_item(self):
        """Test removing item from cart"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        cart.remove(self.vest, extra_fields={'size': 'M'})
        
        self.assertEqual(len(cart), 0)

    def test_remove_specific_variant(self):
        """Test removing specific variant leaves other variants"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=1, size='M')
        cart.add(self.vest, quantity=1, size='L')
        
        cart.remove(self.vest, extra_fields={'size': 'M'})
        
        self.assertEqual(len(cart.cart), 1)
        # Verify L variant remains
        remaining_key = list(cart.cart.keys())[0]
        self.assertIn('size:::L', remaining_key)

    def test_remove_without_extra_fields(self):
        """Test removing without specifying extra_fields removes first match"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        cart.remove(self.vest)
        
        self.assertEqual(len(cart), 0)

    def test_remove_nonexistent_item(self):
        """Test removing nonexistent item does nothing"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        tour = NyscTour.objects.create(
            name='Tour',
            category=self.category,
            price=Decimal('5000.00')
        )
        
        cart.add(self.vest, quantity=1, size='M')
        initial_count = len(cart)
        
        cart.remove(tour)  # Remove item not in cart
        
        self.assertEqual(len(cart), initial_count)


class CartIterationTest(BaseCartTestCase):
    """Test Cart.__iter__() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )
        
        self.tour = NyscTour.objects.create(
            name='Camp Tour',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )

    def test_iterate_empty_cart(self):
        """Test iterating over empty cart"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        items = list(cart)
        self.assertEqual(len(items), 0)

    def test_iterate_cart_with_items(self):
        """Test iterating over cart with items"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        cart.add(self.tour, quantity=1, call_up_number='AB/22C/1234')
        
        items = list(cart)
        
        self.assertEqual(len(items), 2)
        
        # Check item structure
        for item in items:
            self.assertIn('product', item)
            self.assertIn('quantity', item)
            self.assertIn('price', item)
            self.assertIn('total_price', item)
            self.assertIn('extra_fields', item)

    def test_iterate_calculates_total_price(self):
        """Test iteration calculates total price correctly"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        
        items = list(cart)
        item = items[0]
        
        self.assertEqual(item['total_price'], Decimal('4000.00'))

    def test_iterate_fetches_products(self):
        """Test iteration fetches actual product objects"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=1, size='M')
        
        items = list(cart)
        item = items[0]
        
        self.assertEqual(item['product'].id, self.vest.id)
        self.assertEqual(item['product'].name, self.vest.name)


class CartLengthTest(BaseCartTestCase):
    """Test Cart.__len__() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_empty_cart_length(self):
        """Test empty cart has length 0"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        self.assertEqual(len(cart), 0)

    def test_cart_length_counts_quantities(self):
        """Test length counts total quantities, not items"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=5, size='M')
        
        self.assertEqual(len(cart), 5)

    def test_cart_length_multiple_items(self):
        """Test length sums quantities across items"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        tour = NyscTour.objects.create(
            name='Tour',
            category=self.category,
            price=Decimal('5000.00')
        )
        
        cart.add(self.vest, quantity=3, size='M')
        cart.add(tour, quantity=2, call_up_number='AB/22C/1234')
        
        self.assertEqual(len(cart), 5)


class CartTotalPriceTest(BaseCartTestCase):
    """Test Cart.get_total_price() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )
        
        self.tour = NyscTour.objects.create(
            name='Camp Tour',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )

    def test_empty_cart_total(self):
        """Test empty cart has total of 0"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        self.assertEqual(cart.get_total_price(), Decimal('0'))

    def test_single_item_total(self):
        """Test total with single item"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=3, size='M')
        
        self.assertEqual(cart.get_total_price(), Decimal('6000.00'))

    def test_multiple_items_total(self):
        """Test total with multiple items"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        cart.add(self.tour, quantity=1, call_up_number='AB/22C/1234')
        
        expected = (Decimal('2000.00') * 2) + (Decimal('5000.00') * 1)
        self.assertEqual(cart.get_total_price(), expected)

    def test_total_precision(self):
        """Test total price maintains decimal precision"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        # Product with precise price
        precise_product = NyscKit.objects.create(
            name='Precise Product',
            type='vest',
            category=self.category,
            price=Decimal('19.99'),
            available=True
        )
        
        cart.add(precise_product, quantity=3, size='M')
        
        self.assertEqual(cart.get_total_price(), Decimal('59.97'))


class CartClearTest(BaseCartTestCase):
    """Test Cart.clear() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_clear_cart_with_items(self):
        """Test clearing cart removes all items"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=5, size='M')
        cart.clear()
        
        self.assertEqual(len(cart), 0)
        self.assertEqual(cart.get_total_price(), Decimal('0'))

    def test_clear_empty_cart(self):
        """Test clearing empty cart doesn't cause errors"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.clear()
        
        self.assertEqual(len(cart), 0)

    def test_clear_removes_from_session(self):
        """Test clear removes cart from session"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        cart.clear()
        
        # Check session
        self.assertNotIn('cart', request.session.get(cart.cart_key, {}))


class CartCleanupTest(BaseCartTestCase):
    """Test Cart.cleanup() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_cleanup_removes_deleted_products(self):
        """Test cleanup removes items for deleted products"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        
        # Delete product
        self.vest.delete()
        
        removed = cart.cleanup()
        
        self.assertIsNotNone(removed)
        self.assertEqual(len(removed['deleted']), 1)
        self.assertEqual(len(cart), 0)

    def test_cleanup_removes_unavailable_products(self):
        """Test cleanup removes unavailable products"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        
        # Mark unavailable
        self.vest.available = False
        self.vest.save()
        
        removed = cart.cleanup()
        
        self.assertIsNotNone(removed)
        self.assertEqual(len(removed['out_of_stock']), 1)

    def test_cleanup_removes_out_of_stock_products(self):
        """Test cleanup removes out of stock products"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        
        # Mark out of stock
        self.vest.out_of_stock = True
        self.vest.save()
        
        removed = cart.cleanup()
        
        self.assertIsNotNone(removed)
        self.assertEqual(len(removed['out_of_stock']), 1)

    def test_cleanup_keeps_valid_items(self):
        """Test cleanup keeps valid items"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=2, size='M')
        
        removed = cart.cleanup()
        
        self.assertIsNone(removed)
        self.assertEqual(len(cart), 2)

    def test_cleanup_handles_invalid_keys(self):
        """Test cleanup handles malformed cart keys"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        # Add invalid key directly to cart
        cart.cart['invalid_key'] = {'quantity': 1}
        cart.save()
        
        removed = cart.cleanup()
        
        # Should remove invalid key
        self.assertNotIn('invalid_key', cart.cart)


class CartProductValidationTest(BaseCartTestCase):
    """Test Cart.validate_product() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_validate_available_product(self):
        """Test validation passes for available product"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        exists, available, reason = cart.validate_product('nysc_kit', str(self.vest.id))
        
        self.assertTrue(exists)
        self.assertTrue(available)
        self.assertIsNone(reason)

    def test_validate_unavailable_product(self):
        """Test validation fails for unavailable product"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        self.vest.available = False
        self.vest.save()
        
        exists, available, reason = cart.validate_product('nysc_kit', str(self.vest.id))
        
        self.assertTrue(exists)
        self.assertFalse(available)
        self.assertEqual(reason, 'no longer available')

    def test_validate_out_of_stock_product(self):
        """Test validation fails for out of stock product"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        self.vest.out_of_stock = True
        self.vest.save()
        
        exists, available, reason = cart.validate_product('nysc_kit', str(self.vest.id))
        
        self.assertTrue(exists)
        self.assertFalse(available)
        self.assertEqual(reason, 'out of stock')

    def test_validate_nonexistent_product(self):
        """Test validation fails for nonexistent product"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        fake_id = str(uuid.uuid4())
        exists, available, reason = cart.validate_product('nysc_kit', fake_id)
        
        self.assertFalse(exists)
        self.assertFalse(available)
        self.assertEqual(reason, 'no longer exists')

    def test_validate_invalid_product_type(self):
        """Test validation handles invalid product type"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        exists, available, reason = cart.validate_product('invalid_type', str(uuid.uuid4()))
        
        self.assertFalse(exists)
        self.assertFalse(available)


class CartItemKeyGenerationTest(BaseCartTestCase):
    """Test Cart.generate_item_key() method"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_key_includes_product_info(self):
        """Test key includes product type and ID"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        key = cart.generate_item_key(self.vest, {'size': 'M'})
        
        self.assertIn('nysc_kit', key)
        self.assertIn(str(self.vest.id), key)

    def test_key_includes_extra_fields(self):
        """Test key includes sorted extra fields"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        key = cart.generate_item_key(self.vest, {'size': 'M', 'color': 'blue'})
        
        self.assertIn('size:::M', key)
        self.assertIn('color:::blue', key)

    def test_keys_differ_for_different_extra_fields(self):
        """Test different extra fields create different keys"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        key1 = cart.generate_item_key(self.vest, {'size': 'M'})
        key2 = cart.generate_item_key(self.vest, {'size': 'L'})
        
        self.assertNotEqual(key1, key2)

    def test_keys_same_for_same_params(self):
        """Test same params create same key"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        key1 = cart.generate_item_key(self.vest, {'size': 'M'})
        key2 = cart.generate_item_key(self.vest, {'size': 'M'})
        
        self.assertEqual(key1, key2)


class CartEdgeCasesTest(BaseCartTestCase):
    """Test edge cases and error scenarios"""

    def setUp(self):
        """Set up test data"""
        super().setUp()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )

    def test_cart_handles_price_changes(self):
        """Test cart updates price when product price changes"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=1, size='M')
        
        # Change price
        self.vest.price = Decimal('3000.00')
        self.vest.save()
        
        # Add same item again
        cart.add(self.vest, quantity=1, size='M')
        
        # Price should be updated
        item_key = list(cart.cart.keys())[0]
        self.assertEqual(Decimal(cart.cart[item_key]['price']), Decimal('3000.00'))

    def test_cart_handles_empty_extra_fields(self):
        """Test cart handles items with no extra fields"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=1)
        
        self.assertEqual(len(cart), 1)

    def test_cart_session_modification_tracking(self):
        """Test cart properly marks session as modified"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        request.session.modified = False
        cart.add(self.vest, quantity=1, size='M')
        
        self.assertTrue(request.session.modified)

    def test_cart_with_very_large_quantities(self):
        """Test cart handles large quantities"""
        request = self.get_request_with_session()
        cart = Cart(request)
        
        cart.add(self.vest, quantity=99999, size='M')
        
        self.assertEqual(len(cart), 99999)
        expected_total = Decimal('2000.00') * 99999
        self.assertEqual(cart.get_total_price(), expected_total)