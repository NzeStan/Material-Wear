# products/tests/tests_models.py
"""
Comprehensive tests for products models
Tests all models, methods, properties, validators, and edge cases
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
from products.models import Category, NyscKit, NyscTour, Church, BaseProduct
from products.constants import (
    NYSC_KIT_TYPE_CHOICES,
    CHURCH_CHOICES,
    STATES,
    NYSC_KIT_PRODUCT_NAME,
    CHURCH_PRODUCT_NAME,
)
import uuid


class CategoryModelTest(TestCase):
    """Test Category model functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="NYSC KIT",
            slug="nysc-kit",
            product_type="nysc_kit",
            description="NYSC Kit products",
        )

    def test_category_creation(self):
        """Test successful category creation"""
        self.assertEqual(self.category.name, "NYSC KIT")
        self.assertEqual(self.category.slug, "nysc-kit")
        self.assertEqual(self.category.product_type, "nysc_kit")
        self.assertIsNotNone(self.category.description)

    def test_category_str_representation(self):
        """Test string representation of category"""
        self.assertEqual(str(self.category), "NYSC KIT")

    def test_category_slug_uniqueness(self):
        """Test that slug must be unique"""
        with self.assertRaises(Exception):  # IntegrityError
            Category.objects.create(
                name="NYSC TOUR",
                slug="nysc-kit",  # Duplicate slug
                product_type="nysc_tour",
            )

    def test_category_soft_delete(self):
        """Test soft delete functionality"""
        self.assertIsNone(self.category.deleted_at)
        self.category.delete()
        self.assertIsNotNone(self.category.deleted_at)

        # Verify the category is soft-deleted
        self.assertTrue(Category.objects.dead().filter(id=self.category.id).exists())
        self.assertFalse(Category.objects.alive().filter(id=self.category.id).exists())

    def test_category_hard_delete(self):
        """Test hard delete functionality"""
        category_id = self.category.id
        self.category.delete(hard=True)
        self.assertFalse(Category.objects.filter(id=category_id).exists())

    def test_category_restore(self):
        """Test restore after soft delete"""
        self.category.delete()
        self.assertIsNotNone(self.category.deleted_at)

        self.category.restore()
        self.assertIsNone(self.category.deleted_at)
        self.assertTrue(Category.objects.alive().filter(id=self.category.id).exists())

    def test_category_get_absolute_url(self):
        """Test get_absolute_url method raises error when URL pattern missing"""
        from django.urls.exceptions import NoReverseMatch

        with self.assertRaises(NoReverseMatch):
            url = self.category.get_absolute_url()

    def test_multiple_categories_different_product_types(self):
        """Test creating categories for different product types"""
        nysc_tour_cat = Category.objects.create(
            name="NYSC TOUR", slug="nysc-tour", product_type="nysc_tour"
        )
        church_cat = Category.objects.create(
            name="CHURCH PROGRAMME", slug="church-prog", product_type="church"
        )

        self.assertEqual(Category.objects.count(), 3)
        self.assertNotEqual(self.category.product_type, nysc_tour_cat.product_type)
        self.assertNotEqual(self.category.product_type, church_cat.product_type)


class NyscKitModelTest(TestCase):
    """Test NyscKit model functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )
        self.nysc_kit = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("5000.00"),
            description="High quality NYSC Kakhi uniform",
        )

    def test_nysc_kit_creation(self):
        """Test successful NYSC Kit creation"""
        self.assertEqual(self.nysc_kit.name, "Quality Nysc Kakhi")
        self.assertEqual(self.nysc_kit.type, "kakhi")
        self.assertEqual(self.nysc_kit.price, Decimal("5000.00"))
        self.assertTrue(self.nysc_kit.available)
        self.assertFalse(self.nysc_kit.out_of_stock)

    def test_nysc_kit_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.nysc_kit), "Quality Nysc Kakhi")

    def test_nysc_kit_auto_slug_generation(self):
        """Test automatic slug generation on save"""
        kit = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2000.00"),
        )
        expected_slug = slugify("Quality Nysc Vest")
        self.assertEqual(kit.slug, expected_slug)

    def test_nysc_kit_duplicate_slug_handling(self):
        """Test that duplicate names generate unique slugs"""
        kit1 = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2000.00"),
        )
        kit2 = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2500.00"),
        )

        self.assertNotEqual(kit1.slug, kit2.slug)
        self.assertTrue(kit1.slug.startswith("quality-nysc-vest"))
        self.assertTrue(kit2.slug.startswith("quality-nysc-vest"))

    def test_nysc_kit_uuid_id(self):
        """Test that ID is a UUID"""
        self.assertIsInstance(self.nysc_kit.id, uuid.UUID)

    def test_nysc_kit_can_be_purchased_property(self):
        """Test can_be_purchased property"""
        # Available and in stock
        self.assertTrue(self.nysc_kit.can_be_purchased)

        # Not available
        self.nysc_kit.available = False
        self.assertFalse(self.nysc_kit.can_be_purchased)

        # Available but out of stock
        self.nysc_kit.available = True
        self.nysc_kit.out_of_stock = True
        self.assertFalse(self.nysc_kit.can_be_purchased)

    def test_nysc_kit_display_status_property(self):
        """Test display_status property"""
        # Available
        status = self.nysc_kit.display_status
        self.assertEqual(status["text"], "Available")
        self.assertIn("success", status["badge_class"])

        # Out of stock
        self.nysc_kit.out_of_stock = True
        status = self.nysc_kit.display_status
        self.assertEqual(status["text"], "Out of Stock")
        self.assertIn("warning", status["badge_class"])

        # Not available
        self.nysc_kit.available = False
        self.nysc_kit.out_of_stock = False
        status = self.nysc_kit.display_status
        self.assertEqual(status["text"], "Not Available")
        self.assertIn("ghost", status["badge_class"])

    def test_nysc_kit_price_validation(self):
        """Test that price must be positive"""
        with self.assertRaises(ValidationError):
            kit = NyscKit(
                name="Quality Nysc Cap",
                type="cap",
                category=self.category,
                price=Decimal("-100.00"),
            )
            kit.full_clean()

    def test_nysc_kit_zero_price_validation(self):
        """Test that price cannot be zero"""
        with self.assertRaises(ValidationError):
            kit = NyscKit(
                name="Quality Nysc Cap",
                type="cap",
                category=self.category,
                price=Decimal("0.00"),
            )
            kit.full_clean()

    def test_nysc_kit_minimum_price(self):
        """Test minimum valid price"""
        kit = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("0.01"),
        )
        self.assertEqual(kit.price, Decimal("0.01"))

    def test_nysc_kit_timestamps(self):
        """Test created and updated timestamps"""
        self.assertIsNotNone(self.nysc_kit.created)
        self.assertIsNotNone(self.nysc_kit.updated)

        # Update and check timestamp changes
        old_updated = self.nysc_kit.updated
        self.nysc_kit.price = Decimal("6000.00")
        self.nysc_kit.save()
        self.assertGreater(self.nysc_kit.updated, old_updated)

    def test_nysc_kit_product_type_attribute(self):
        """Test product_type class attribute"""
        self.assertEqual(self.nysc_kit.product_type, "nysc_kit")

    def test_nysc_kit_category_relationship(self):
        """Test category foreign key relationship"""
        self.assertEqual(self.nysc_kit.category, self.category)
        self.assertIn(self.nysc_kit, self.category.nysckits.all())

    def test_nysc_kit_category_set_null_on_delete(self):
        """Test that category is set to NULL when deleted"""
        category_id = self.category.id
        self.category.delete(hard=True)

        self.nysc_kit.refresh_from_db()
        self.assertIsNone(self.nysc_kit.category)

    def test_nysc_kit_queryset_available(self):
        """Test available() queryset method"""
        # Create mix of available and unavailable products
        NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2000.00"),
            available=False,
        )
        NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("1500.00"),
            out_of_stock=True,
        )

        available_kits = NyscKit.objects.available()
        self.assertEqual(available_kits.count(), 1)
        self.assertIn(self.nysc_kit, available_kits)

    def test_nysc_kit_queryset_out_of_stock(self):
        """Test out_of_stock() queryset method"""
        kit = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("1500.00"),
            out_of_stock=True,
        )

        out_of_stock_kits = NyscKit.objects.out_of_stock()
        self.assertEqual(out_of_stock_kits.count(), 1)
        self.assertIn(kit, out_of_stock_kits)

    def test_nysc_kit_queryset_by_category(self):
        """Test by_category() queryset method"""
        other_category = Category.objects.create(
            name="CHURCH PROGRAMME", slug="church-prog", product_type="church"
        )

        kits = NyscKit.objects.by_category("nysc-kit")
        self.assertGreater(kits.count(), 0)

        # All kits should be in the specified category
        for kit in kits:
            self.assertEqual(kit.category.slug, "nysc-kit")

    def test_nysc_kit_queryset_search(self):
        """Test search() queryset method"""
        NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2000.00"),
            description="Premium quality vest for NYSC",
        )

        # Search by name
        results = NyscKit.objects.search("Vest")
        self.assertGreater(results.count(), 0)

        # Search by description
        results = NyscKit.objects.search("Premium")
        self.assertGreater(results.count(), 0)

    def test_nysc_kit_all_types(self):
        """Test creating all NYSC Kit types"""
        vest = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2000.00"),
        )
        cap = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("1500.00"),
        )

        self.assertEqual(NyscKit.objects.count(), 3)
        types = set(NyscKit.objects.values_list("type", flat=True))
        self.assertEqual(len(types), 3)


class NyscTourModelTest(TestCase):
    """Test NyscTour model functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="NYSC TOUR", slug="nysc-tour", product_type="nysc_tour"
        )
        self.nysc_tour = NyscTour.objects.create(
            name="Lagos",
            category=self.category,
            price=Decimal("15000.00"),
            description="NYSC tour to Lagos state",
        )

    def test_nysc_tour_creation(self):
        """Test successful NYSC Tour creation"""
        self.assertEqual(self.nysc_tour.name, "Lagos")
        self.assertEqual(self.nysc_tour.price, Decimal("15000.00"))
        self.assertTrue(self.nysc_tour.available)
        self.assertFalse(self.nysc_tour.out_of_stock)

    def test_nysc_tour_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.nysc_tour), "Lagos")

    def test_nysc_tour_auto_slug_generation(self):
        """Test automatic slug generation"""
        tour = NyscTour.objects.create(
            name="FCT", category=self.category, price=Decimal("12000.00")
        )
        self.assertEqual(tour.slug, "fct")

    def test_nysc_tour_duplicate_slug_handling(self):
        """Test unique slug generation for duplicates"""
        tour1 = NyscTour.objects.create(
            name="FCT", category=self.category, price=Decimal("12000.00")
        )
        tour2 = NyscTour.objects.create(
            name="FCT", category=self.category, price=Decimal("13000.00")
        )

        self.assertNotEqual(tour1.slug, tour2.slug)
        self.assertTrue(tour1.slug.startswith("fct"))
        self.assertTrue(tour2.slug.startswith("fct"))

    def test_nysc_tour_product_type_attribute(self):
        """Test product_type class attribute"""
        self.assertEqual(self.nysc_tour.product_type, "nysc_tour")

    def test_nysc_tour_can_be_purchased_property(self):
        """Test can_be_purchased property"""
        self.assertTrue(self.nysc_tour.can_be_purchased)

        self.nysc_tour.available = False
        self.assertFalse(self.nysc_tour.can_be_purchased)

    def test_nysc_tour_multiple_states(self):
        """Test creating tours for multiple states"""
        states_to_create = ["FCT", "Kano", "Rivers"]
        for state in states_to_create:
            NyscTour.objects.create(
                name=state, category=self.category, price=Decimal("15000.00")
            )

        self.assertEqual(NyscTour.objects.count(), 4)  # Including setUp tour

    def test_nysc_tour_queryset_methods(self):
        """Test queryset methods work correctly"""
        # Test available
        available_tours = NyscTour.objects.available()
        self.assertIn(self.nysc_tour, available_tours)

        # Test search
        results = NyscTour.objects.search("Lagos")
        self.assertIn(self.nysc_tour, results)


class ChurchModelTest(TestCase):
    """Test Church model functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="CHURCH PROGRAMME", slug="church-prog", product_type="church"
        )
        self.church_product = Church.objects.create(
            name="Quality RCCG Shirt",
            church="RCCG",
            category=self.category,
            price=Decimal("3500.00"),
            description="Quality RCCG church shirt",
        )

    def test_church_creation(self):
        """Test successful Church product creation"""
        self.assertEqual(self.church_product.name, "Quality RCCG Shirt")
        self.assertEqual(self.church_product.church, "RCCG")
        self.assertEqual(self.church_product.price, Decimal("3500.00"))
        self.assertTrue(self.church_product.available)

    def test_church_str_representation(self):
        """Test string representation"""
        self.assertEqual(str(self.church_product), "Quality RCCG Shirt")

    def test_church_auto_slug_generation(self):
        """Test automatic slug generation"""
        product = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=self.category,
            price=Decimal("3000.00"),
        )
        expected_slug = slugify("Quality Shilo Shirt")
        self.assertEqual(product.slug, expected_slug)

    def test_church_duplicate_slug_handling(self):
        """Test unique slug generation for duplicates"""
        product1 = Church.objects.create(
            name="Quality Shilo Shirt",
            church="WINNERS",
            category=self.category,
            price=Decimal("3000.00"),
        )
        product2 = Church.objects.create(
            name="Quality Shilo Shirt",
            church="RCCG",
            category=self.category,
            price=Decimal("3200.00"),
        )

        self.assertNotEqual(product1.slug, product2.slug)

    def test_church_product_type_attribute(self):
        """Test product_type class attribute"""
        self.assertEqual(self.church_product.product_type, "church")

    def test_church_can_be_purchased_property(self):
        """Test can_be_purchased property"""
        self.assertTrue(self.church_product.can_be_purchased)

        self.church_product.out_of_stock = True
        self.assertFalse(self.church_product.can_be_purchased)

    def test_church_multiple_denominations(self):
        """Test creating products for multiple churches"""
        churches = [
            ("WINNERS", "Quality Shilo Shirt"),
            ("DEEPER_LIFE", "Quality Shilo jacket"),
            ("MOUNTAIN_OF_FIRE", "Quality RCCG polo"),
        ]

        for church_code, product_name in churches:
            Church.objects.create(
                name=product_name,
                church=church_code,
                category=self.category,
                price=Decimal("3500.00"),
            )

        self.assertEqual(Church.objects.count(), 4)  # Including setUp product

    def test_church_queryset_methods(self):
        """Test queryset methods work correctly"""
        # Test available
        available_products = Church.objects.available()
        self.assertIn(self.church_product, available_products)

        # Test search
        results = Church.objects.search("RCCG")
        self.assertIn(self.church_product, results)


class BaseProductTest(TestCase):
    """Test BaseProduct abstract model functionality through concrete models"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

    def test_base_product_fields_exist(self):
        """Test that BaseProduct fields are inherited"""
        kit = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("5000.00"),
        )

        # Check all BaseProduct fields exist
        self.assertTrue(hasattr(kit, "id"))
        self.assertTrue(hasattr(kit, "category"))
        self.assertTrue(hasattr(kit, "image"))
        self.assertTrue(hasattr(kit, "image_1"))
        self.assertTrue(hasattr(kit, "image_2"))
        self.assertTrue(hasattr(kit, "image_3"))
        self.assertTrue(hasattr(kit, "description"))
        self.assertTrue(hasattr(kit, "price"))
        self.assertTrue(hasattr(kit, "available"))
        self.assertTrue(hasattr(kit, "out_of_stock"))
        self.assertTrue(hasattr(kit, "created"))
        self.assertTrue(hasattr(kit, "updated"))

    def test_base_product_methods_exist(self):
        """Test that BaseProduct methods are inherited"""
        kit = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("5000.00"),
        )

        # Check properties exist
        self.assertTrue(hasattr(kit, "can_be_purchased"))
        self.assertTrue(hasattr(kit, "display_status"))

    def test_price_decimal_places(self):
        """Test price stores exactly 2 decimal places"""
        kit = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("5000.123"),  # Extra decimal places
        )

        # Should be rounded to 2 decimal places
        kit.refresh_from_db()
        self.assertEqual(kit.price, Decimal("5000.12"))

    def test_large_price_values(self):
        """Test handling of large price values"""
        kit = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("99999999.99"),  # Max value for DecimalField(10, 2)
        )

        kit.refresh_from_db()
        self.assertEqual(kit.price, Decimal("99999999.99"))


class ProductManagerQuerySetTest(TestCase):
    """Test ProductManager and ProductQuerySet functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

        # Create products with different states
        self.available_kit = NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("5000.00"),
            available=True,
            out_of_stock=False,
        )

        self.out_of_stock_kit = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2000.00"),
            available=True,
            out_of_stock=True,
        )

        self.unavailable_kit = NyscKit.objects.create(
            name="Quality Nysc Cap",
            type="cap",
            category=self.category,
            price=Decimal("1500.00"),
            available=False,
            out_of_stock=False,
        )

    def test_manager_available_method(self):
        """Test ProductManager.available() method"""
        available = NyscKit.objects.available()

        self.assertEqual(available.count(), 1)
        self.assertIn(self.available_kit, available)
        self.assertNotIn(self.out_of_stock_kit, available)
        self.assertNotIn(self.unavailable_kit, available)

    def test_manager_out_of_stock_method(self):
        """Test ProductManager.out_of_stock() method"""
        out_of_stock = NyscKit.objects.out_of_stock()

        self.assertEqual(out_of_stock.count(), 1)
        self.assertIn(self.out_of_stock_kit, out_of_stock)

    def test_manager_by_category_method(self):
        """Test ProductManager.by_category() method"""
        other_category = Category.objects.create(
            name="NYSC TOUR", slug="nysc-tour", product_type="nysc_tour"
        )

        NyscTour.objects.create(
            name="Lagos", category=other_category, price=Decimal("15000.00")
        )

        kits_in_category = NyscKit.objects.by_category("nysc-kit")
        self.assertEqual(kits_in_category.count(), 3)

    def test_manager_search_method(self):
        """Test ProductManager.search() method"""
        # Search by name
        results = NyscKit.objects.search("Kakhi")
        self.assertIn(self.available_kit, results)

        # Search by description
        kit_with_description = NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2500.00"),
            description="Premium quality NYSC vest",
        )

        results = NyscKit.objects.search("Premium")
        self.assertIn(kit_with_description, results)

    def test_queryset_chaining(self):
        """Test chaining queryset methods"""
        # Create more test data
        NyscKit.objects.create(
            name="Quality Nysc Vest",
            type="vest",
            category=self.category,
            price=Decimal("2500.00"),
            description="Premium vest",
            available=True,
            out_of_stock=False,
        )

        # Chain available() and search()
        results = NyscKit.objects.available().search("vest")
        self.assertGreater(results.count(), 0)


class SoftDeleteTest(TestCase):
    """Test soft delete functionality"""

    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

    def test_soft_delete_sets_deleted_at(self):
        """Test that soft delete sets deleted_at timestamp"""
        self.assertIsNone(self.category.deleted_at)

        self.category.delete()

        self.assertIsNotNone(self.category.deleted_at)
        self.assertIsInstance(self.category.deleted_at, timezone.datetime)

    def test_soft_delete_preserves_data(self):
        """Test that soft delete preserves all data"""
        category_id = self.category.id
        category_name = self.category.name

        self.category.delete()

        # Data should still exist in database
        deleted_category = Category.objects.get(id=category_id)
        self.assertEqual(deleted_category.name, category_name)
        self.assertIsNotNone(deleted_category.deleted_at)

    def test_alive_queryset(self):
        """Test alive() queryset method"""
        other_category = Category.objects.create(
            name="NYSC TOUR", slug="nysc-tour", product_type="nysc_tour"
        )

        self.category.delete()

        alive_categories = Category.objects.alive()
        self.assertEqual(alive_categories.count(), 1)
        self.assertIn(other_category, alive_categories)
        self.assertNotIn(self.category, alive_categories)

    def test_dead_queryset(self):
        """Test dead() queryset method"""
        self.category.delete()

        dead_categories = Category.objects.dead()
        self.assertEqual(dead_categories.count(), 1)
        self.assertIn(self.category, dead_categories)

    def test_restore_functionality(self):
        """Test restore() method"""
        self.category.delete()
        self.assertIsNotNone(self.category.deleted_at)

        self.category.restore()

        self.assertIsNone(self.category.deleted_at)
        self.assertIn(self.category, Category.objects.alive())

    def test_hard_delete_removes_completely(self):
        """Test hard delete removes from database"""
        category_id = self.category.id

        self.category.delete(hard=True)

        self.assertFalse(Category.objects.filter(id=category_id).exists())

    def test_queryset_soft_delete(self):
        """Test soft delete on queryset"""
        categories = Category.objects.filter(product_type="nysc_kit")
        categories.delete()

        # All should be soft-deleted
        self.assertEqual(Category.objects.dead().count(), 1)
        self.assertEqual(Category.objects.alive().count(), 0)

    def test_queryset_hard_delete(self):
        """Test hard delete on queryset"""
        Category.objects.create(
            name="NYSC TOUR", slug="nysc-tour", product_type="nysc_tour"
        )

        initial_count = Category.objects.count()

        Category.objects.filter(product_type="nysc_kit").hard_delete()

        self.assertEqual(Category.objects.count(), initial_count - 1)
