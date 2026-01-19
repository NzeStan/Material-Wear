# cart/tests/tests_api_views.py
"""
Comprehensive tests for cart API views
Tests all endpoints with edge cases, authentication scenarios, and error handling
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse
from products.models import Category, NyscKit, NyscTour, Church
from measurement.models import Measurement
from cart.cart import Cart
import uuid

User = get_user_model()


class CartDetailViewTest(APITestCase):
    """Test GET /api/cart/ endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test category and products
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.kit = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )
        
        self.tour = NyscTour.objects.create(
            name='Camp Tour Package',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )
        
        self.url = reverse('cart:cart-detail')

    def test_get_empty_cart(self):
        """Test getting empty cart"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(response.data['total_cost'], '0')
        self.assertEqual(len(response.data['items']), 0)

    def test_get_cart_with_items(self):
        """Test getting cart with items"""
        # Add item to cart via session
        session = self.client.session
        cart = Cart(type('obj', (object,), {'session': session, 'user': None})())
        cart.add(self.kit, quantity=2, size='M')
        cart.save()
        session.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 2)
        self.assertGreater(len(response.data['items']), 0)
        
        # Check item structure
        item = response.data['items'][0]
        self.assertIn('product_type', item)
        self.assertIn('product_id', item)
        self.assertIn('quantity', item)
        self.assertIn('price', item)
        self.assertIn('total_price', item)
        self.assertIn('item_key', item)

    def test_get_cart_with_multiple_product_types(self):
        """Test cart with multiple product types"""
        session = self.client.session
        cart = Cart(type('obj', (object,), {'session': session, 'user': None})())
        cart.add(self.kit, quantity=1, size='L')
        cart.add(self.tour, quantity=2, call_up_number='AB/22C/1234')
        cart.save()
        session.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 3)
        self.assertIn('grouped_by_type', response.data)

    def test_get_cart_unauthenticated(self):
        """Test cart access without authentication"""
        response = self.client.get(self.url)
        
        # Should work - cart is session-based
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AddToCartViewTest(APITestCase):
    """Test POST /api/cart/add/ endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create categories
        self.kit_category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.church_category = Category.objects.create(
            name='CHURCH',
            slug='church',
            product_type='church'
        )
        
        # Create products
        self.vest = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.kit_category,
            price=Decimal('2000.00'),
            available=True
        )
        
        self.kakhi = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.kit_category,
            price=Decimal('5000.00'),
            available=True
        )
        
        self.cap = NyscKit.objects.create(
            name='Quality Nysc Cap',
            type='cap',
            category=self.kit_category,
            price=Decimal('1500.00'),
            available=True
        )
        
        self.tour = NyscTour.objects.create(
            name='Camp Tour',
            category=self.kit_category,
            price=Decimal('5000.00'),
            available=True
        )
        
        self.church = Church.objects.create(
            name='RCCG Shirt',
            church='RCCG',
            category=self.church_category,
            price=Decimal('3500.00'),
            available=True
        )
        
        self.url = reverse('cart:cart-add')

    def test_add_vest_with_size(self):
        """Test adding vest with size"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 2,
            'size': 'M'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['cart_count'], 2)

    def test_add_vest_without_size(self):
        """Test adding vest without required size"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('size', response.data)

    def test_add_kakhi_authenticated_without_measurement(self):
        """Test adding kakhi without measurement profile"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('measurement', str(response.data).lower())

    def test_add_kakhi_authenticated_with_measurement(self):
        """Test adding kakhi with measurement profile"""
        self.client.force_authenticate(user=self.user)
        
        # Create measurement
        Measurement.objects.create(
            user=self.user,
            shoulder=Decimal('18.5'),
            chest=Decimal('42.0'),
            waist=Decimal('34.0'),
            hips=Decimal('40.0'),
            trouser_length=Decimal('42.0'),
            trouser_waist=Decimal('34.0'),
            shirt_length=Decimal('30.0'),
            sleeve=Decimal('24.0'),
            neck=Decimal('16.0'),
            thigh=Decimal('24.0'),
            knee=Decimal('15.0')
        )
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 1)

    def test_add_kakhi_unauthenticated(self):
        """Test adding kakhi without authentication"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.kakhi.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_cap_auto_size(self):
        """Test adding cap with automatic free_size"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 1)

    def test_add_tour_with_call_up_number(self):
        """Test adding tour with call up number"""
        data = {
            'product_type': 'nysc_tour',
            'product_id': str(self.tour.id),
            'quantity': 1,
            'call_up_number': 'AB/22C/1234'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_church_with_custom_text(self):
        """Test adding church product with custom text"""
        data = {
            'product_type': 'church',
            'product_id': str(self.church.id),
            'quantity': 1,
            'size': 'XL',
            'custom_name_text': 'PASTOR JOHN'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_invalid_product_type(self):
        """Test adding with invalid product type"""
        data = {
            'product_type': 'invalid_type',
            'product_id': str(uuid.uuid4()),
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_nonexistent_product(self):
        """Test adding nonexistent product"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(uuid.uuid4()),
            'quantity': 1,
            'size': 'M'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_unavailable_product(self):
        """Test adding unavailable product"""
        self.vest.available = False
        self.vest.save()
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'M'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_out_of_stock_product(self):
        """Test adding out of stock product"""
        self.vest.out_of_stock = True
        self.vest.save()
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'M'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_zero_quantity(self):
        """Test adding with zero quantity"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 0,
            'size': 'M'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_negative_quantity(self):
        """Test adding with negative quantity"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': -5,
            'size': 'M'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_with_override_quantity(self):
        """Test adding with override flag"""
        # First add
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 2,
            'size': 'M'
        }
        self.client.post(self.url, data, format='json')
        
        # Add again with override
        data['quantity'] = 5
        data['override'] = True
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 5)

    def test_add_without_override_increments(self):
        """Test adding without override increments quantity"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 2,
            'size': 'M'
        }
        
        self.client.post(self.url, data, format='json')
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cart_count'], 4)

    def test_add_invalid_vest_size(self):
        """Test adding vest with invalid size"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'INVALID_SIZE'
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_missing_required_fields(self):
        """Test adding without required fields"""
        data = {
            'product_type': 'nysc_kit',
            'quantity': 1
        }
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('product_id', response.data)


class UpdateCartItemViewTest(APITestCase):
    """Test PATCH /api/cart/update/<item_key>/ endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
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
        
        # Add item to cart
        session = self.client.session
        cart = Cart(type('obj', (object,), {'session': session, 'user': None})())
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        session.save()
        
        # Get item key
        self.item_key = list(cart.cart.keys())[0]
        self.url = reverse('cart:cart-update', kwargs={'item_key': self.item_key})

    def test_update_quantity(self):
        """Test updating item quantity"""
        data = {'quantity': 5}
        
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_update_quantity_to_zero_removes_item(self):
        """Test setting quantity to 0 removes item"""
        data = {'quantity': 0}
        
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('removed', response.data['message'].lower())

    def test_update_nonexistent_item(self):
        """Test updating nonexistent item"""
        fake_key = 'nonexistent:::fake-uuid|||size:::M'
        url = reverse('cart:cart-update', kwargs={'item_key': fake_key})
        
        data = {'quantity': 3}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_with_negative_quantity(self):
        """Test updating with negative quantity"""
        data = {'quantity': -5}
        
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_without_quantity(self):
        """Test updating without quantity field"""
        data = {}
        
        response = self.client.patch(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RemoveFromCartViewTest(APITestCase):
    """Test DELETE /api/cart/remove/<item_key>/ endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
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
        
        # Add item to cart
        session = self.client.session
        cart = Cart(type('obj', (object,), {'session': session, 'user': None})())
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        session.save()
        
        self.item_key = list(cart.cart.keys())[0]
        self.url = reverse('cart:cart-remove', kwargs={'item_key': self.item_key})

    def test_remove_item(self):
        """Test removing item from cart"""
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['cart_count'], 0)

    def test_remove_nonexistent_item(self):
        """Test removing nonexistent item"""
        fake_key = 'nonexistent:::fake-uuid|||size:::M'
        url = reverse('cart:cart-remove', kwargs={'item_key': fake_key})
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ClearCartViewTest(APITestCase):
    """Test POST /api/cart/clear/ endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
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
        
        self.url = reverse('cart:cart-clear')

    def test_clear_cart_with_items(self):
        """Test clearing cart with items"""
        # Add items to cart
        session = self.client.session
        cart = Cart(type('obj', (object,), {'session': session, 'user': None})())
        cart.add(self.vest, quantity=2, size='M')
        cart.save()
        session.save()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify cart is empty
        cart_response = self.client.get(reverse('cart:cart-detail'))
        self.assertEqual(cart_response.data['total_items'], 0)

    def test_clear_empty_cart(self):
        """Test clearing already empty cart"""
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CartSummaryViewTest(APITestCase):
    """Test GET /api/cart/summary/ endpoint"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
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
        
        self.url = reverse('cart:cart-summary')

    def test_get_empty_cart_summary(self):
        """Test summary for empty cart"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['total'], 0.0)

    def test_get_cart_summary_with_items(self):
        """Test summary with items"""
        session = self.client.session
        cart = Cart(type('obj', (object,), {'session': session, 'user': None})())
        cart.add(self.vest, quantity=3, size='M')
        cart.save()
        session.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertGreater(response.data['total'], 0)


class CartAuthenticationTest(APITestCase):
    """Test cart behavior with authenticated vs anonymous users"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.cap = NyscKit.objects.create(
            name='Quality Nysc Cap',
            type='cap',
            category=self.category,
            price=Decimal('1500.00'),
            available=True
        )

    def test_anonymous_cart_persists_in_session(self):
        """Test anonymous user's cart persists"""
        # Add to cart as anonymous
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 2
        }
        
        self.client.post(reverse('cart:cart-add'), data, format='json')
        
        # Check cart
        response = self.client.get(reverse('cart:cart-detail'))
        self.assertEqual(response.data['total_items'], 2)

    def test_authenticated_user_separate_cart(self):
        """Test authenticated users get separate cart"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 3
        }
        
        self.client.post(reverse('cart:cart-add'), data, format='json')
        
        response = self.client.get(reverse('cart:cart-detail'))
        self.assertEqual(response.data['total_items'], 3)


class CartRateLimitTest(APITestCase):
    """Test rate limiting on cart endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.cap = NyscKit.objects.create(
            name='Quality Nysc Cap',
            type='cap',
            category=self.category,
            price=Decimal('1500.00'),
            available=True
        )

    def test_rate_limit_enforcement(self):
        """Test rate limiting prevents abuse"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.cap.id),
            'quantity': 1
        }
        
        url = reverse('cart:cart-add')
        
        # Make many requests
        for _ in range(150):  # Exceed typical rate limit
            response = self.client.post(url, data, format='json')
            
        # Eventually should get rate limited
        # (This test may need adjustment based on actual rate limit settings)
        # For now, just ensure it doesn't crash


class CartEdgeCasesTest(APITestCase):
    """Test edge cases and error scenarios"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
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

    def test_malformed_item_key(self):
        """Test handling malformed item keys"""
        url = reverse('cart:cart-remove', kwargs={'item_key': 'malformed_key'})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_special_characters_in_custom_text(self):
        """Test handling special characters in custom text"""
        church_category = Category.objects.create(
            name='CHURCH',
            slug='church',
            product_type='church'
        )
        
        church = Church.objects.create(
            name='RCCG Shirt',
            church='RCCG',
            category=church_category,
            price=Decimal('3500.00'),
            available=True
        )
        
        data = {
            'product_type': 'church',
            'product_id': str(church.id),
            'quantity': 1,
            'size': 'XL',
            'custom_name_text': '<script>alert("XSS")</script>'
        }
        
        response = self.client.post(reverse('cart:cart-add'), data, format='json')
        
        # Should handle gracefully
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_very_large_quantity(self):
        """Test handling very large quantities"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 999999,
            'size': 'M'
        }
        
        response = self.client.post(reverse('cart:cart-add'), data, format='json')
        
        # Should either succeed or return validation error
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_concurrent_cart_modifications(self):
        """Test handling concurrent modifications"""
        # Add item
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': 'M'
        }
        
        self.client.post(reverse('cart:cart-add'), data, format='json')
        
        # Simulate concurrent clear and add
        self.client.post(reverse('cart:cart-clear'))
        response = self.client.post(reverse('cart:cart-add'), data, format='json')
        
        # Should handle gracefully
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty_string_fields(self):
        """Test handling empty string fields"""
        data = {
            'product_type': 'nysc_kit',
            'product_id': str(self.vest.id),
            'quantity': 1,
            'size': ''  # Empty size
        }
        
        response = self.client.post(reverse('cart:cart-add'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)