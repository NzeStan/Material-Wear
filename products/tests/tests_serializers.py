# products/tests/tests_serializers.py
"""
Comprehensive tests for products serializers
Tests all serializers, validation, representation, and edge cases
"""

from django.test import TestCase
from rest_framework.test import APIRequestFactory
from decimal import Decimal
from products.models import Category, NyscKit, NyscTour, Church
from products.serializers import (
    CategorySerializer,
    NyscKitSerializer,
    NyscTourSerializer,
    ChurchSerializer,
    ProductListSerializer,
    BaseProductSerializer
)


class CategorySerializerTest(TestCase):
    """Test CategorySerializer functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit',
            description='NYSC Kit products'
        )
        
        # Create some products for product_count test
        self.kit1 = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00'),
            available=True
        )
        self.kit2 = NyscKit.objects.create(
            name='Quality Nysc Vest',
            type='vest',
            category=self.category,
            price=Decimal('2000.00'),
            available=True
        )
        
        self.serializer = CategorySerializer(instance=self.category)

    def test_category_serializer_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data
        
        expected_fields = ['id', 'name', 'slug', 'product_type', 'description', 'product_count']
        self.assertEqual(set(data.keys()), set(expected_fields))

    def test_category_serializer_data(self):
        """Test serializer data is correct"""
        data = self.serializer.data
        
        self.assertEqual(data['name'], 'NYSC KIT')
        self.assertEqual(data['slug'], 'nysc-kit')
        self.assertEqual(data['product_type'], 'nysc_kit')
        self.assertEqual(data['description'], 'NYSC Kit products')

    def test_category_product_count(self):
        """Test product_count field counts only available products"""
        data = self.serializer.data
        self.assertEqual(data['product_count'], 2)
        
        # Make one product unavailable
        self.kit1.available = False
        self.kit1.save()
        
        # Re-serialize and check count
        serializer = CategorySerializer(instance=self.category)
        data = serializer.data
        self.assertEqual(data['product_count'], 1)

    def test_category_product_count_empty(self):
        """Test product_count when no products exist"""
        empty_category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        
        serializer = CategorySerializer(instance=empty_category)
        data = serializer.data
        self.assertEqual(data['product_count'], 0)

    def test_category_serializer_validation(self):
        """Test serializer validation for creating categories"""
        data = {
            'name': 'NYSC TOUR',
            'slug': 'nysc-tour',
            'product_type': 'nysc_tour',
            'description': 'Tour products'
        }
        
        serializer = CategorySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        category = serializer.save()
        self.assertEqual(category.name, 'NYSC TOUR')

    def test_category_serializer_invalid_data(self):
        """Test serializer with invalid data"""
        data = {
            'name': 'INVALID',
            'slug': '',  # Empty slug should fail
            'product_type': 'nysc_tour'
        }
        
        serializer = CategorySerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_category_serializer_read_only_fields(self):
        """Test that id is read-only"""
        data = self.serializer.data
        
        # Try to update with a new ID
        update_data = data.copy()
        update_data['id'] = 99999
        
        serializer = CategorySerializer(instance=self.category, data=update_data)
        if serializer.is_valid():
            updated_category = serializer.save()
            # ID should not change
            self.assertEqual(updated_category.id, self.category.id)


class NyscKitSerializerTest(TestCase):
    """Test NyscKitSerializer functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00'),
            description='High quality NYSC Kakhi',
            available=True,
            out_of_stock=False
        )
        
        self.serializer = NyscKitSerializer(instance=self.kit)

    def test_nysc_kit_serializer_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data
        
        expected_fields = [
            'id', 'name', 'slug', 'type', 'type_display', 'category',
            'category_name', 'description', 'price', 'available', 'out_of_stock',
            'created', 'updated', 'thumbnail', 'can_be_purchased'
        ]

        # Check all expected fields are present
        for field in expected_fields:
            self.assertIn(field, data.keys())
            
        # Image fields should NOT be present (null images are removed)
        image_fields = ['image', 'image_1', 'image_2', 'image_3']
        for field in image_fields:
            self.assertNotIn(field, data.keys())

    def test_nysc_kit_serializer_data(self):
        """Test serializer data is correct"""
        data = self.serializer.data
        
        self.assertEqual(data['name'], 'Quality Nysc Kakhi')
        self.assertEqual(data['type'], 'kakhi')
        self.assertEqual(data['type_display'], 'Kakhi')
        self.assertEqual(data['price'], '5000.00')
        self.assertEqual(data['description'], 'High quality NYSC Kakhi')
        self.assertTrue(data['available'])
        self.assertFalse(data['out_of_stock'])
        self.assertTrue(data['can_be_purchased'])

    def test_nysc_kit_category_name_field(self):
        """Test category_name field populates correctly"""
        data = self.serializer.data
        self.assertEqual(data['category_name'], 'NYSC KIT')

    def test_nysc_kit_can_be_purchased_field(self):
        """Test can_be_purchased field reflects product status"""
        # Available and in stock
        data = self.serializer.data
        self.assertTrue(data['can_be_purchased'])
        
        # Out of stock
        self.kit.out_of_stock = True
        self.kit.save()
        serializer = NyscKitSerializer(instance=self.kit)
        data = serializer.data
        self.assertFalse(data['can_be_purchased'])
        
        # Not available
        self.kit.available = False
        self.kit.out_of_stock = False
        self.kit.save()
        serializer = NyscKitSerializer(instance=self.kit)
        data = serializer.data
        self.assertFalse(data['can_be_purchased'])

    def test_nysc_kit_to_representation_removes_null_images(self):
        """Test that null image fields are removed from response"""
        data = self.serializer.data
        
        # Since no images were set, these fields should not be in response
        self.assertNotIn('image', data)
        self.assertNotIn('image_1', data)
        self.assertNotIn('image_2', data)
        self.assertNotIn('image_3', data)

    def test_nysc_kit_thumbnail_field(self):
        """Test thumbnail field behavior"""
        data = self.serializer.data
        
        # Without image, thumbnail should be None
        self.assertIsNone(data.get('thumbnail'))

    def test_nysc_kit_serializer_read_only_fields(self):
        """Test that specified fields are read-only"""
        read_only_fields = ['id', 'slug', 'created', 'updated', 'can_be_purchased']
        
        for field in read_only_fields:
            self.assertIn(field, NyscKitSerializer.Meta.read_only_fields)

    def test_nysc_kit_serializer_validation(self):
        """Test serializer validation for creating kits"""
        data = {
            'name': 'Quality Nysc Vest',
            'type': 'vest',
            'category': self.category.id,
            'price': '2000.00',
            'description': 'Test vest'
        }
        
        serializer = NyscKitSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_nysc_kit_serializer_invalid_price(self):
        """Test validation fails for invalid price"""
        data = {
            'name': 'Quality Nysc Vest',
            'type': 'vest',
            'category': self.category.id,
            'price': '-100.00',  # Negative price
        }
        
        serializer = NyscKitSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_nysc_kit_serializer_all_types(self):
        """Test serializer works for all kit types"""
        types = ['kakhi', 'vest', 'cap']
        
        for kit_type in types:
            kit = NyscKit.objects.create(
                name=f'Quality Nysc {kit_type.title()}',
                type=kit_type,
                category=self.category,
                price=Decimal('2000.00')
            )
            
            serializer = NyscKitSerializer(instance=kit)
            data = serializer.data
            
            self.assertEqual(data['type'], kit_type)
            self.assertIsNotNone(data['type_display'])


class NyscTourSerializerTest(TestCase):
    """Test NyscTourSerializer functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        
        self.tour = NyscTour.objects.create(
            name='Lagos',
            category=self.category,
            price=Decimal('15000.00'),
            description='NYSC tour to Lagos'
        )
        
        self.serializer = NyscTourSerializer(instance=self.tour)

    def test_nysc_tour_serializer_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data
        
        expected_fields = [
            'id', 'name', 'slug', 'category', 'category_name', 'description',
            'price', 'available', 'out_of_stock', 'created', 'updated', 
            'thumbnail', 'can_be_purchased'
        ]

        # Then add check for absent image fields
        image_fields = ['image', 'image_1', 'image_2', 'image_3']
        for field in image_fields:
            self.assertNotIn(field, data.keys())
        
        for field in expected_fields:
            self.assertIn(field, data.keys())

    def test_nysc_tour_serializer_data(self):
        """Test serializer data is correct"""
        data = self.serializer.data
        
        self.assertEqual(data['name'], 'Lagos')
        self.assertEqual(data['price'], '15000.00')
        self.assertEqual(data['category_name'], 'NYSC TOUR')
        self.assertTrue(data['available'])
        self.assertTrue(data['can_be_purchased'])

    def test_nysc_tour_to_representation_removes_null_images(self):
        """Test that null image fields are removed"""
        data = self.serializer.data
        
        # No images set, so fields should be absent
        self.assertNotIn('image', data)
        self.assertNotIn('image_1', data)
        self.assertNotIn('image_2', data)
        self.assertNotIn('image_3', data)

    def test_nysc_tour_serializer_validation(self):
        """Test serializer validation"""
        data = {
            'name': 'Abuja',
            'category': self.category.id,
            'price': '12000.00',
            'description': 'Tour to Abuja'
        }
        
        serializer = NyscTourSerializer(data=data)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
        self.assertTrue(serializer.is_valid(), f"Serializer errors: {serializer.errors}")

    def test_nysc_tour_multiple_states(self):
        """Test serializer for multiple state tours"""
        states = ['Abuja', 'Kano', 'Rivers']
        
        for state in states:
            tour = NyscTour.objects.create(
                name=state,
                category=self.category,
                price=Decimal('15000.00')
            )
            
            serializer = NyscTourSerializer(instance=tour)
            data = serializer.data
            
            self.assertEqual(data['name'], state)


class ChurchSerializerTest(TestCase):
    """Test ChurchSerializer functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        
        self.church_product = Church.objects.create(
            name='Quality RCCG Shirt',
            church='RCCG',
            category=self.category,
            price=Decimal('3500.00'),
            description='Quality RCCG shirt'
        )
        
        self.serializer = ChurchSerializer(instance=self.church_product)

    def test_church_serializer_fields(self):
        """Test that serializer contains all expected fields"""
        data = self.serializer.data
        
        expected_fields = [
            'id', 'name', 'slug', 'church', 'church_display', 'category',
            'category_name', 'description', 'price', 'available', 'out_of_stock', 
            'created', 'updated', 'thumbnail', 'can_be_purchased'
        ]

        # Then add check for absent image fields
        image_fields = ['image', 'image_1', 'image_2', 'image_3']
        for field in image_fields:
            self.assertNotIn(field, data.keys())
        
        for field in expected_fields:
            self.assertIn(field, data.keys())

    def test_church_serializer_data(self):
        """Test serializer data is correct"""
        data = self.serializer.data
        
        self.assertEqual(data['name'], 'Quality RCCG Shirt')
        self.assertEqual(data['church'], 'RCCG')
        self.assertEqual(data['church_display'], 'Redeemed Christian Church of God (RCCG)')
        self.assertEqual(data['price'], '3500.00')
        self.assertEqual(data['category_name'], 'CHURCH PROG')

    def test_church_display_field(self):
        """Test church_display field shows full church name"""
        data = self.serializer.data
        
        # The church_display should be the human-readable version
        self.assertIn('RCCG', data['church_display'])
        self.assertNotEqual(data['church'], data['church_display'])

    def test_church_to_representation_removes_null_images(self):
        """Test that null image fields are removed"""
        data = self.serializer.data
        
        self.assertNotIn('image', data)
        self.assertNotIn('image_1', data)
        self.assertNotIn('image_2', data)
        self.assertNotIn('image_3', data)

    def test_church_serializer_validation(self):
        """Test serializer validation"""
        data = {
            'name': 'Quality Shilo Shirt',
            'church': 'WINNERS',
            'category': self.category.id,
            'price': '3000.00',
            'description': 'Shilo shirt'
        }
        
        serializer = ChurchSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_church_all_denominations(self):
        """Test serializer for all church denominations"""
        churches = [
            ('WINNERS', 'Quality Shilo Shirt'),
            ('DEEPER_LIFE', 'Quality Shilo jacket'),
            ('MOUNTAIN_OF_FIRE', 'Quality RCCG polo'),
        ]
        
        for church_code, product_name in churches:
            product = Church.objects.create(
                name=product_name,
                church=church_code,
                category=self.category,
                price=Decimal('3500.00')
            )
            
            serializer = ChurchSerializer(instance=product)
            data = serializer.data
            
            self.assertEqual(data['church'], church_code)
            self.assertIsNotNone(data['church_display'])


class ProductListSerializerTest(TestCase):
    """Test ProductListSerializer functionality"""

    def setUp(self):
        """Set up test data"""
        # Create categories
        self.kit_category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        self.tour_category = Category.objects.create(
            name='NYSC TOUR',
            slug='nysc-tour',
            product_type='nysc_tour'
        )
        self.church_category = Category.objects.create(
            name='CHURCH PROG',
            slug='church-prog',
            product_type='church'
        )
        
        # Create products
        self.kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.kit_category,
            price=Decimal('5000.00')
        )
        self.tour = NyscTour.objects.create(
            name='Lagos',
            category=self.tour_category,
            price=Decimal('15000.00')
        )
        self.church = Church.objects.create(
            name='Quality RCCG Shirt',
            church='RCCG',
            category=self.church_category,
            price=Decimal('3500.00')
        )

    def test_product_list_serializer_fields(self):
        """Test that serializer contains all expected fields"""
        data = {
            'nysc_kits': NyscKit.objects.all(),
            'nysc_tours': NyscTour.objects.all(),
            'churches': Church.objects.all(),
            'categories': Category.objects.all(),
            'current_category': None,
            'pagination': {}
        }
        
        serializer = ProductListSerializer(data)
        serialized_data = serializer.data
        
        expected_fields = [
            'nysc_kits', 'nysc_tours', 'churches',
            'categories', 'current_category', 'pagination'
        ]
        
        for field in expected_fields:
            self.assertIn(field, serialized_data.keys())

    def test_product_list_serializer_with_data(self):
        """Test serializer with actual product data"""
        data = {
            'nysc_kits': NyscKit.objects.all(),
            'nysc_tours': NyscTour.objects.all(),
            'churches': Church.objects.all(),
            'categories': Category.objects.all(),
            'current_category': self.kit_category,
            'pagination': {'page': 1, 'total_pages': 1}
        }
        
        serializer = ProductListSerializer(data)
        serialized_data = serializer.data
        
        self.assertGreater(len(serialized_data['nysc_kits']), 0)
        self.assertGreater(len(serialized_data['nysc_tours']), 0)
        self.assertGreater(len(serialized_data['churches']), 0)
        self.assertGreater(len(serialized_data['categories']), 0)
        self.assertIsNotNone(serialized_data['current_category'])

    def test_product_list_serializer_empty_data(self):
        """Test serializer with empty querysets"""
        NyscKit.objects.all().delete()
        NyscTour.objects.all().delete()
        Church.objects.all().delete()
        
        data = {
            'nysc_kits': NyscKit.objects.all(),
            'nysc_tours': NyscTour.objects.all(),
            'churches': Church.objects.all(),
            'categories': Category.objects.all(),
            'current_category': None,
            'pagination': {}
        }
        
        serializer = ProductListSerializer(data)
        serialized_data = serializer.data
        
        self.assertEqual(len(serialized_data['nysc_kits']), 0)
        self.assertEqual(len(serialized_data['nysc_tours']), 0)
        self.assertEqual(len(serialized_data['churches']), 0)

    def test_product_list_serializer_null_current_category(self):
        """Test serializer with null current_category"""
        data = {
            'nysc_kits': NyscKit.objects.all(),
            'nysc_tours': NyscTour.objects.all(),
            'churches': Church.objects.all(),
            'categories': Category.objects.all(),
            'current_category': None,
            'pagination': {}
        }
        
        serializer = ProductListSerializer(data)
        serialized_data = serializer.data
        
        self.assertIsNone(serialized_data['current_category'])


class BaseProductSerializerTest(TestCase):
    """Test BaseProductSerializer functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )
        
        self.kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00')
        )

    def test_base_serializer_category_name_field(self):
        """Test that category_name is populated from category relationship"""
        serializer = NyscKitSerializer(instance=self.kit)
        data = serializer.data
        
        self.assertEqual(data['category_name'], self.category.name)

    def test_base_serializer_thumbnail_without_image(self):
        """Test thumbnail field when no image exists"""
        serializer = NyscKitSerializer(instance=self.kit)
        data = serializer.data
        
        self.assertIsNone(data.get('thumbnail'))

    def test_base_serializer_can_be_purchased_property(self):
        """Test can_be_purchased is read-only and computed"""
        serializer = NyscKitSerializer(instance=self.kit)
        
        # Verify it's in read-only fields
        self.assertIn('can_be_purchased', NyscKitSerializer.Meta.read_only_fields)
        
        data = serializer.data
        self.assertTrue(data['can_be_purchased'])


class SerializerEdgeCasesTest(TestCase):
    """Test edge cases and special scenarios"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='NYSC KIT',
            slug='nysc-kit',
            product_type='nysc_kit'
        )

    def test_serializer_with_very_long_description(self):
        """Test serializer handles long descriptions"""
        long_description = 'A' * 10000
        kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00'),
            description=long_description
        )
        
        serializer = NyscKitSerializer(instance=kit)
        data = serializer.data
        
        self.assertEqual(len(data['description']), len(long_description))

    def test_serializer_with_special_characters(self):
        """Test serializer handles special characters"""
        special_description = "Test with special chars: <>&\"'éñ中文"
        kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00'),
            description=special_description
        )
        
        serializer = NyscKitSerializer(instance=kit)
        data = serializer.data
        
        self.assertEqual(data['description'], special_description)

    def test_serializer_with_max_decimal_price(self):
        """Test serializer with maximum price value"""
        kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('99999999.99')
        )
        
        serializer = NyscKitSerializer(instance=kit)
        data = serializer.data
        
        self.assertEqual(data['price'], '99999999.99')

    def test_serializer_with_min_decimal_price(self):
        """Test serializer with minimum price value"""
        kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('0.01')
        )
        
        serializer = NyscKitSerializer(instance=kit)
        data = serializer.data
        
        self.assertEqual(data['price'], '0.01')

    def test_serializer_many_true(self):
        """Test serializer with many=True"""
        kits = [
            NyscKit.objects.create(
                name='Quality Nysc Kakhi',
                type='kakhi',
                category=self.category,
                price=Decimal('5000.00')
            ),
            NyscKit.objects.create(
                name='Quality Nysc Vest',
                type='vest',
                category=self.category,
                price=Decimal('2000.00')
            )
        ]
        
        serializer = NyscKitSerializer(kits, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'Quality Nysc Kakhi')
        self.assertEqual(data[1]['name'], 'Quality Nysc Vest')

    def test_serializer_partial_update(self):
        """Test serializer with partial=True for updates"""
        kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00')
        )
        
        update_data = {'price': '6000.00'}
        serializer = NyscKitSerializer(instance=kit, data=update_data, partial=True)
        
        self.assertTrue(serializer.is_valid())
        updated_kit = serializer.save()
        
        self.assertEqual(updated_kit.price, Decimal('6000.00'))
        self.assertEqual(updated_kit.name, 'Quality Nysc Kakhi')  # Should remain unchanged

    def test_serializer_with_null_category(self):
        """Test serializer when category is null"""
        kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=None,
            price=Decimal('5000.00')
        )
        
        serializer = NyscKitSerializer(instance=kit)
        data = serializer.data
        
        self.assertIsNone(data['category'])
        self.assertIsNone(data.get('category_name'))

    def test_serializer_empty_string_description(self):
        """Test serializer with empty description"""
        kit = NyscKit.objects.create(
            name='Quality Nysc Kakhi',
            type='kakhi',
            category=self.category,
            price=Decimal('5000.00'),
            description=''
        )
        
        serializer = NyscKitSerializer(instance=kit)
        data = serializer.data
        
        self.assertEqual(data['description'], '')