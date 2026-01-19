# cart/tests/tests_api_views.py
"""
Comprehensive tests for Cart API Views

Coverage:
- CartDetailView (GET /api/cart/)
- CartSummaryView (GET /api/cart/summary/)
- AddToCartView (POST /api/cart/add/)
- UpdateCartItemView (PATCH /api/cart/update/<item_key>/)
- RemoveFromCartView (DELETE /api/cart/remove/<item_key>/)
- ClearCartView (POST /api/cart/clear/)
- Authentication scenarios (anonymous vs authenticated)
- User cart isolation
- Error handling and edge cases
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, NyscKit, NyscTour, Church
from measurement.models import Measurement
from cart.cart import Cart

User = get_user_model()


class CartDetailViewTests(TestCase):
    """Test GET /api/cart/ - CartDetailView"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('cart:cart-detail')
        
        # Create category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.cap = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_get_empty_cart(self):
        """Test getting empty cart returns empty items list"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(len(response.data['items']), 0)
        self.assertEqual(float(response.data['total_cost']), 0.0)
    
    def test_get_cart_with_single_item(self):
        """Test getting cart with one item"""
        # Add item to cart first
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 2
        }, format='json')
        
        # Get cart
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 2)
        self.assertEqual(len(response.data['items']), 1)
        
        # Check item details
        item = response.data['items'][0]
        self.assertEqual(item['product_type'], 'nysc_kit')
        self.assertEqual(item['quantity'], 2)
        self.assertEqual(Decimal(item['price']), Decimal("5000.00"))
        self.assertEqual(Decimal(item['total_price']), Decimal("10000.00"))
    
    def test_get_cart_with_multiple_items(self):
        """Test getting cart with multiple different items"""
        add_url = reverse('cart:cart-add')
        
        # Add cap
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 1
        }, format='json')
        
        # Add vest
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 2,
            'size': 'M'
        }, format='json')
        
        # Get cart
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 3)  # 1 + 2
        self.assertEqual(len(response.data['items']), 2)
        
        # Check total cost
        expected_total = (Decimal("5000.00") * 1) + (Decimal("3000.00") * 2)
        self.assertEqual(Decimal(response.data['total_cost']), expected_total)
    
    def test_cart_grouped_by_type(self):
        """Test cart groups items by product type"""
        add_url = reverse('cart:cart-add')
        
        # Create tour product
        tour_category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        tour = NyscTour.objects.create(
            name="Lagos",
            category=tour_category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Add cap (NyscKit)
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 1
        }, format='json')
        
        # Add tour (NyscTour)
        self.client.post(add_url, {
            'product_type': 'nysc_tour',
            'product_id': str(tour.id),
            'quantity': 1,
            'call_up_number': 'AB/22C/1234'
        }, format='json')
        
        # Get cart
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check grouping
        grouped = response.data['grouped_by_type']
        self.assertIn('NyscKit', grouped)
        self.assertIn('NyscTour', grouped)
        self.assertEqual(len(grouped['NyscKit']), 1)
        self.assertEqual(len(grouped['NyscTour']), 1)
    
    def test_cart_contains_item_keys(self):
        """Test cart items include item_key for updates/removal"""
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 1
        }, format='json')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data['items'][0]
        self.assertIn('item_key', item)
        self.assertIsNotNone(item['item_key'])
    
    def test_anonymous_user_can_access_cart(self):
        """Test anonymous users can access their cart"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should work without authentication


class CartSummaryViewTests(TestCase):
    """Test GET /api/cart/summary/ - CartSummaryView"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('cart:cart-summary')
        
        # Create category and product
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_get_empty_cart_summary(self):
        """Test summary of empty cart"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['total'], 0.0)
    
    def test_get_cart_summary_with_items(self):
        """Test summary with items in cart"""
        # Add items
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 3
        }, format='json')
        
        # Get summary
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['total'], 15000.0)  # 5000 * 3
    
    def test_summary_is_lightweight(self):
        """Test summary only returns count and total (no items)"""
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 1
        }, format='json')
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only have count and total, no items list
        self.assertIn('count', response.data)
        self.assertIn('total', response.data)
        self.assertNotIn('items', response.data)


class AddToCartViewTests(TestCase):
    """Test POST /api/cart/add/ - AddToCartView"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('cart:cart-add')
        
        # Create category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.cap = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.kakhi = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("7000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_add_cap_to_cart_success(self):
        """Test successfully adding cap to cart"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 2
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['cart_count'], 2)
        self.assertIn('item', response.data)
    
    def test_add_vest_with_size_success(self):
        """Test adding vest with required size"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'M'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 1)
    
    def test_add_vest_without_size_fails(self):
        """Test adding vest without size fails"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1
            # Missing size
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('size', response.data)
    
    def test_add_kakhi_without_authentication_fails(self):
        """Test adding kakhi without authentication fails"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user', response.data)
    
    def test_add_kakhi_without_measurement_fails(self):
        """Test adding kakhi without measurement fails"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=user)
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('measurement', response.data)
    
    def test_add_kakhi_with_measurement_success(self):
        """Test adding kakhi with measurement succeeds"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        Measurement.objects.create(
            user=user,
            chest=Decimal("40.00"),
            waist=Decimal("32.00"),
            is_deleted=False
        )
        self.client.force_authenticate(user=user)
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 1)
    
    def test_add_invalid_product_id_fails(self):
        """Test adding with invalid product_id fails"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': 'invalid-uuid',
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_id', response.data)
    
    def test_add_nonexistent_product_fails(self):
        """Test adding non-existent product fails"""
        import uuid
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(uuid.uuid4()),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_id', response.data)
    
    def test_add_unavailable_product_fails(self):
        """Test adding unavailable product fails"""
        self.cap.available = False
        self.cap.save()
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_zero_quantity_fails(self):
        """Test adding zero quantity fails"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 0
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', response.data)
    
    def test_add_negative_quantity_fails(self):
        """Test adding negative quantity fails"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': -5
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_same_item_twice_increments_quantity(self):
        """Test adding same item twice increments quantity"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 2
        }
        
        # First add
        response1 = self.client.post(self.url, data, format='json')
        self.assertEqual(response1.data['cart_count'], 2)
        
        # Second add
        response2 = self.client.post(self.url, data, format='json')
        self.assertEqual(response2.data['cart_count'], 4)  # 2 + 2
    
    def test_add_with_override_replaces_quantity(self):
        """Test adding with override=true replaces quantity"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 2
        }
        
        # First add
        self.client.post(self.url, data, format='json')
        
        # Add with override
        data['quantity'] = 5
        data['override'] = True
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.data['cart_count'], 5)  # Replaced, not added
    
    def test_add_church_product(self):
        """Test adding church product with size"""
        church_category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        church = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=church_category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=False
        )
        
        data = {
            'product_type': 'church',
            'product_id': str(church.id),
            'quantity': 1,
            'size': 'L',
            'custom_name_text': 'PASTOR JOHN'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 1)
    
    def test_add_tour_product(self):
        """Test adding tour product with call_up_number"""
        tour_category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        tour = NyscTour.objects.create(
            name="Lagos",
            category=tour_category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        data = {
            'product_type': 'nysc_tour',
            'product_id': str(tour.id),
            'quantity': 1,
            'call_up_number': 'AB/22C/1234'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 1)


class UpdateCartItemViewTests(TestCase):
    """Test PATCH /api/cart/update/<item_key>/ - UpdateCartItemView"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create category and product
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Add item to cart and get item_key
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 2
        }, format='json')
        
        # Get cart to find item_key
        cart_url = reverse('cart:cart-detail')
        cart_response = self.client.get(cart_url)
        self.item_key = cart_response.data['items'][0]['item_key']
        self.update_url = reverse('cart:cart-update', kwargs={'item_key': self.item_key})
    
    def test_update_quantity_success(self):
        """Test updating item quantity"""
        data = {'quantity': 5}
        
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['cart_count'], 5)
    
    def test_update_quantity_to_zero_removes_item(self):
        """Test updating quantity to 0 removes item"""
        data = {'quantity': 0}
        
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('removed', response.data['message'].lower())
        self.assertEqual(response.data['cart_count'], 0)
    
    def test_update_nonexistent_item_fails(self):
        """Test updating non-existent item fails"""
        fake_key = 'nonexistent_key'
        url = reverse('cart:cart-update', kwargs={'item_key': fake_key})
        data = {'quantity': 5}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_update_with_negative_quantity_fails(self):
        """Test updating with negative quantity fails"""
        data = {'quantity': -1}
        
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', response.data)
    
    def test_update_without_quantity_fails(self):
        """Test updating without quantity field fails"""
        data = {}
        
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('quantity', response.data)
    
    def test_update_maintains_other_items(self):
        """Test updating one item doesn't affect others"""
        # Add second item
        vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(vest.id),
            'quantity': 3,
            'size': 'M'
        }, format='json')
        
        # Update first item
        data = {'quantity': 1}
        response = self.client.patch(self.update_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Total should be 1 (updated) + 3 (other item) = 4
        self.assertEqual(response.data['cart_count'], 4)


class RemoveFromCartViewTests(TestCase):
    """Test DELETE /api/cart/remove/<item_key>/ - RemoveFromCartView"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create category and product
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        # Add item to cart
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 2
        }, format='json')
        
        # Get item_key
        cart_url = reverse('cart:cart-detail')
        cart_response = self.client.get(cart_url)
        self.item_key = cart_response.data['items'][0]['item_key']
        self.remove_url = reverse('cart:cart-remove', kwargs={'item_key': self.item_key})
    
    def test_remove_item_success(self):
        """Test successfully removing item from cart"""
        response = self.client.delete(self.remove_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['cart_count'], 0)
    
    def test_remove_nonexistent_item_fails(self):
        """Test removing non-existent item fails"""
        fake_key = 'nonexistent_key'
        url = reverse('cart:cart-remove', kwargs={'item_key': fake_key})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
    
    def test_remove_maintains_other_items(self):
        """Test removing one item doesn't affect others"""
        # Add second item
        vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
        
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(vest.id),
            'quantity': 3,
            'size': 'M'
        }, format='json')
        
        # Remove first item
        response = self.client.delete(self.remove_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only vest should remain (3 items)
        self.assertEqual(response.data['cart_count'], 3)
    
    def test_remove_already_removed_item_fails(self):
        """Test removing already removed item fails"""
        # Remove once
        self.client.delete(self.remove_url)
        
        # Try to remove again
        response = self.client.delete(self.remove_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ClearCartViewTests(TestCase):
    """Test POST /api/cart/clear/ - ClearCartView"""
    
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('cart:cart-clear')
        
        # Create category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.cap = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("3000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_clear_cart_with_items(self):
        """Test clearing cart with multiple items"""
        # Add items
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 2
        }, format='json')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 3,
            'size': 'M'
        }, format='json')
        
        # Clear cart
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify cart is empty
        cart_url = reverse('cart:cart-detail')
        cart_response = self.client.get(cart_url)
        self.assertEqual(cart_response.data['total_items'], 0)
    
    def test_clear_empty_cart(self):
        """Test clearing already empty cart"""
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_clear_cart_is_permanent(self):
        """Test clearing cart permanently removes all items"""
        # Add item
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 5
        }, format='json')
        
        # Clear
        self.client.post(self.url)
        
        # Verify it's really gone
        cart_url = reverse('cart:cart-detail')
        cart_response = self.client.get(cart_url)
        self.assertEqual(len(cart_response.data['items']), 0)


class UserCartIsolationTests(TestCase):
    """Test cart isolation between different users"""
    
    def setUp(self):
        # Create users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create category and product
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
        
        self.client1 = APIClient()
        self.client2 = APIClient()
    
    def test_authenticated_users_have_separate_carts(self):
        """Test different authenticated users have isolated carts"""
        # User 1 adds to cart
        self.client1.force_authenticate(user=self.user1)
        add_url = reverse('cart:cart-add')
        self.client1.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 2
        }, format='json')
        
        # User 2 checks their cart (should be empty)
        self.client2.force_authenticate(user=self.user2)
        cart_url = reverse('cart:cart-detail')
        response = self.client2.get(cart_url)
        
        self.assertEqual(response.data['total_items'], 0)
        
        # User 1's cart should still have items
        response1 = self.client1.get(cart_url)
        self.assertEqual(response1.data['total_items'], 2)
    
    def test_anonymous_cart_migrates_to_authenticated(self):
        """Test anonymous cart migrates when user logs in"""
        # Add to cart as anonymous
        client = APIClient()
        add_url = reverse('cart:cart-add')
        client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 3
        }, format='json')
        
        # Authenticate as user1
        client.force_authenticate(user=self.user1)
        
        # Check cart (should have migrated)
        cart_url = reverse('cart:cart-detail')
        response = client.get(cart_url)
        
        self.assertEqual(response.data['total_items'], 3)


class CartAPIEdgeCasesTests(TestCase):
    """Test edge cases and unusual scenarios"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create category and product
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.product = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False
        )
    
    def test_add_very_large_quantity(self):
        """Test adding very large quantity"""
        add_url = reverse('cart:cart-add')
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 10000
        }
        
        response = self.client.post(add_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 10000)
    
    def test_cart_persists_across_requests(self):
        """Test cart persists across multiple requests"""
        add_url = reverse('cart:cart-add')
        cart_url = reverse('cart:cart-detail')
        
        # Add item
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(self.product.id),
            'quantity': 2
        }, format='json')
        
        # Get cart in separate request
        response = self.client.get(cart_url)
        
        self.assertEqual(response.data['total_items'], 2)
    
    def test_invalid_http_method_on_endpoints(self):
        """Test invalid HTTP methods return appropriate errors"""
        cart_url = reverse('cart:cart-detail')
        
        # POST to GET-only endpoint
        response = self.client.post(cart_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_malformed_json_request(self):
        """Test malformed JSON is rejected"""
        add_url = reverse('cart:cart-add')
        
        # Send invalid JSON
        response = self.client.post(
            add_url,
            data='{"invalid": json}',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unicode_in_custom_name_through_api(self):
        """Test unicode characters work through API"""
        church_category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        church = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=church_category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=False
        )
        
        add_url = reverse('cart:cart-add')
        data = {
            'product_type': 'church',
            'product_id': str(church.id),
            'quantity': 1,
            'size': 'M',
            'custom_name_text': '牧师 PASTOR'
        }
        
        response = self.client.post(add_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cart_total_cost_precision(self):
        """Test cart total maintains decimal precision"""
        # Create product with precise price
        precise_product = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("1234.56"),
            available=True,
            out_of_stock=False
        )
        
        add_url = reverse('cart:cart-add')
        self.client.post(add_url, {
            'product_type': 'nysc_kit',
            'product_id': str(precise_product.id),
            'quantity': 3,
            'size': 'M'
        }, format='json')
        
        cart_url = reverse('cart:cart-detail')
        response = self.client.get(cart_url)
        
        expected_total = Decimal("1234.56") * 3
        self.assertEqual(Decimal(response.data['total_cost']), expected_total)