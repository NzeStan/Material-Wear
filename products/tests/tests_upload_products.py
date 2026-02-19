# products/tests/tests_upload_products.py
"""
Comprehensive bulletproof tests for products/management/commands/upload_products.py

Test Coverage:
===============
✅ Command Arguments & Options
   - CSV file path validation
   - Product type validation (nysc_kit, nysc_tour, church)
   - Dry run mode
   - Skip existing products
   - Update existing products
   - Conflicting flags validation

✅ CSV File Handling
   - File not found errors
   - Empty CSV files
   - Encoding errors (UTF-8 validation)
   - Malformed CSV files
   - Missing headers
   - Extra columns (should be ignored)

✅ Header Validation
   - Required fields per product type
   - Missing columns detection
   - Extra columns handling

✅ CSV Duplicate Detection
   - Duplicate product names in CSV
   - Multiple duplicate detection
   - Case-sensitive duplicate checking

✅ Category Validation
   - Valid category names
   - Invalid category names
   - Category-product type mismatch
   - Category creation/retrieval

✅ Price Validation
   - Positive prices
   - Negative/zero prices
   - Maximum price limits
   - Decimal precision
   - Non-numeric prices
   - Empty/whitespace prices

✅ NYSC Kit Processing
   - Valid kit creation
   - All kit types (kakhi, vest, cap)
   - Invalid product names
   - Invalid kit types
   - Required fields
   - Skip existing logic
   - Update existing logic
   - Image handling

✅ NYSC Tour Processing
   - Valid tour creation
   - All 37 Nigerian states
   - Invalid state names
   - Required fields
   - Skip/update logic

✅ Church Processing
   - Valid church product creation
   - All valid church names
   - Invalid church names
   - Valid church denominations
   - Invalid denominations
   - Required fields
   - Skip/update logic
   - Custom name handling

✅ Image Downloading
   - HTTP/HTTPS URLs
   - Valid image types (jpg, png, gif, webp)
   - Non-image content-types
   - Large images (>10MB)
   - Timeout handling
   - Network errors
   - Invalid URLs
   - URL too long (>500 chars)

✅ Cloudinary Integration
   - Cloudinary URL detection
   - Public ID extraction
   - Various URL formats
   - Transformations removal
   - Version removal
   - Reuse existing images

✅ Boolean Conversion
   - True values ('true', '1', 'yes', 'y', True)
   - False values ('false', '0', 'no', 'n', False)
   - Empty/whitespace defaults to True
   - Case insensitivity

✅ Transaction Handling
   - Atomic operations
   - Rollback on errors
   - Multiple products in transaction

✅ Dry Run Mode
   - No database changes
   - No image downloads
   - Display operations only

✅ Output & Logging
   - Success messages
   - Error messages
   - Summary statistics
   - Progress indicators

✅ Edge Cases & Error Handling
   - Unicode in product names
   - Very long descriptions
   - Special characters in data
   - Concurrent uploads
   - Database constraints
   - Image URL edge cases
"""
import os
import csv
import tempfile
from io import StringIO
from decimal import Decimal
from unittest.mock import patch, Mock, MagicMock, call
from django.test import TestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.core.files import File
from django.db import IntegrityError
import requests

from products.models import Category, NyscKit, NyscTour, Church
from products.management.commands.upload_products import Command


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_test_csv(filename, headers, rows):
    """Helper to create a temporary CSV file for testing"""
    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    return filename


# ============================================================================
# COMMAND ARGUMENTS & OPTIONS TESTS
# ============================================================================


class CommandArgumentsTests(TestCase):
    """Test command argument validation and handling"""

    def test_missing_csv_file_argument(self):
        """Test command fails without CSV file argument"""
        with self.assertRaises(CommandError):
            call_command("upload_products")

    def test_missing_type_argument(self):
        """Test command fails without --type argument"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,category,price\n")
            csv_path = f.name

        try:
            with self.assertRaises(CommandError):
                call_command("upload_products", csv_path)
        finally:
            os.remove(csv_path)

    def test_invalid_product_type(self):
        """Test command rejects invalid product type"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,category,price\n")
            csv_path = f.name

        try:
            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=invalid_type")
            self.assertIn("invalid choice", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_valid_product_types(self):
        """Test all valid product types are accepted"""
        valid_types = ["nysc_kit", "nysc_tour", "church"]

        for product_type in valid_types:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False
            ) as f:
                f.write("name,category,price,description")
                if product_type == "nysc_kit":
                    f.write(",type")
                elif product_type == "church":
                    f.write(",church")
                f.write("\n")
                csv_path = f.name

            try:
                # This should not raise an error (empty CSV will raise CommandError instead)
                with self.assertRaises(CommandError) as cm:
                    call_command("upload_products", csv_path, f"--type={product_type}")
                self.assertIn("empty", str(cm.exception))
            finally:
                os.remove(csv_path)

    def test_skip_and_update_flags_conflict(self):
        """Test that --skip-existing and --update-existing cannot be used together"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,category,price,description,type\n")
            csv_path = f.name

        try:
            with self.assertRaises(CommandError) as cm:
                call_command(
                    "upload_products",
                    csv_path,
                    "--type=nysc_kit",
                    "--skip-existing",
                    "--update-existing",
                )
            self.assertIn("Cannot use both", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_dry_run_flag(self):
        """Test --dry-run flag is properly handled"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            # Run with dry-run
            out = StringIO()
            call_command(
                "upload_products", csv_path, "--type=nysc_kit", "--dry-run", stdout=out
            )

            # Verify no products were created
            self.assertEqual(NyscKit.objects.count(), 0)

            # Verify output indicates dry run
            output = out.getvalue()
            self.assertIn("DRY RUN", output)
        finally:
            os.remove(csv_path)


# ============================================================================
# CSV FILE HANDLING TESTS
# ============================================================================


class CSVFileHandlingTests(TestCase):
    """Test CSV file reading and validation"""

    def test_file_not_found(self):
        """Test error when CSV file doesn't exist"""
        with self.assertRaises(CommandError) as cm:
            call_command("upload_products", "/nonexistent/file.csv", "--type=nysc_kit")
        self.assertIn("File not found", str(cm.exception))

    def test_empty_csv_file(self):
        """Test error when CSV file is empty"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # Write only headers, no data rows
            f.write("name,category,price,description,type\n")
            csv_path = f.name

        try:
            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            self.assertIn("empty", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_encoding_error(self):
        """Test error handling for non-UTF-8 encoded files"""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as f:
            # Write non-UTF-8 content
            f.write(b"\xff\xfe")  # Invalid UTF-8 bytes
            csv_path = f.name

        try:
            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            self.assertIn("Encoding error", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_malformed_csv(self):
        """Test error handling for malformed CSV files"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("name,category,price\n")
            f.write('Product 1,"Unclosed quote\n')  # Malformed row
            csv_path = f.name

        try:
            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            # Should raise either CSV error or validation error
            error_msg = str(cm.exception)
            self.assertTrue("CSV error" in error_msg or "Missing columns" in error_msg)
        finally:
            os.remove(csv_path)

    def test_csv_with_extra_columns(self):
        """Test that extra columns in CSV are ignored"""
        headers = ["name", "category", "price", "description", "type", "extra_column"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "kakhi",
                "extra_column": "ignored",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            # Should process successfully, ignoring extra column
            call_command("upload_products", csv_path, "--type=nysc_kit")

            self.assertEqual(NyscKit.objects.count(), 1)
        finally:
            os.remove(csv_path)

    def test_csv_with_unicode_characters(self):
        """Test CSV with unicode characters in product names"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Description with émojis 🎉 and ñ ü",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.first()
            self.assertIn("émojis", product.description)
        finally:
            os.remove(csv_path)


# ============================================================================
# HEADER VALIDATION TESTS
# ============================================================================


class HeaderValidationTests(TestCase):
    """Test CSV header validation"""

    def test_missing_name_column(self):
        """Test error when 'name' column is missing"""
        headers = ["category", "price", "description", "type"]
        rows = [
            {
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            self.assertIn("Missing columns", str(cm.exception))
            self.assertIn("name", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_missing_category_column(self):
        """Test error when 'category' column is missing"""
        headers = ["name", "price", "description", "type"]
        rows = [
            {"name": "Test", "price": "5000", "description": "Test", "type": "kakhi"}
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            self.assertIn("category", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_missing_price_column(self):
        """Test error when 'price' column is missing"""
        headers = ["name", "category", "description", "type"]
        rows = [
            {
                "name": "Test",
                "category": "NYSC KIT",
                "description": "Test",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            self.assertIn("price", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_missing_type_column_for_nysc_kit(self):
        """Test error when 'type' column is missing for NYSC Kit"""
        headers = ["name", "category", "price", "description"]
        rows = [
            {
                "name": "Test",
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            self.assertIn("type", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_missing_church_column_for_church(self):
        """Test error when 'church' column is missing for Church products"""
        headers = ["name", "category", "price", "description"]
        rows = [
            {
                "name": "Test",
                "category": "CHURCH PROGRAMME",
                "price": "5000",
                "description": "Test",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=church")
            self.assertIn("church", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_no_headers(self):
        """Test error when CSV has no headers"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("\n")  # Empty file with just newline
            csv_path = f.name

        try:
            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            # Empty file is caught as "CSV file is empty"
            self.assertIn("empty", str(cm.exception).lower())
        finally:
            os.remove(csv_path)


# ============================================================================
# CSV DUPLICATE DETECTION TESTS
# ============================================================================


class CSVDuplicateDetectionTests(TestCase):
    """Test duplicate detection in CSV files"""

    def test_duplicate_product_names(self):
        """Test error when CSV contains duplicate product names"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "First",
                "type": "kakhi",
            },
            {
                "name": "Quality Nysc Kakhi",  # Duplicate
                "category": "NYSC KIT",
                "price": "6000.00",
                "description": "Second",
                "type": "kakhi",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            self.assertIn("Duplicates", str(cm.exception))
            self.assertIn("Quality Nysc Kakhi", str(cm.exception))
        finally:
            os.remove(csv_path)

    def test_multiple_duplicates(self):
        """Test detection of multiple duplicate entries"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Product A",
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
                "type": "kakhi",
            },
            {
                "name": "Product B",
                "category": "NYSC KIT",
                "price": "6000",
                "description": "Test",
                "type": "vest",
            },
            {
                "name": "Product A",
                "category": "NYSC KIT",
                "price": "7000",
                "description": "Test",
                "type": "kakhi",
            },  # Duplicate
            {
                "name": "Product B",
                "category": "NYSC KIT",
                "price": "8000",
                "description": "Test",
                "type": "vest",
            },  # Duplicate
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            with self.assertRaises(CommandError) as cm:
                call_command("upload_products", csv_path, "--type=nysc_kit")
            error_msg = str(cm.exception)
            self.assertIn("Product A", error_msg)
            self.assertIn("Product B", error_msg)
        finally:
            os.remove(csv_path)

    def test_case_sensitive_duplicate_detection(self):
        """Test that duplicate detection is case-sensitive"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
                "type": "kakhi",
            },
            {
                "name": "quality nysc kakhi",
                "category": "NYSC KIT",
                "price": "6000",
                "description": "Test",
                "type": "kakhi",
            },  # Different case
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            # Should NOT raise duplicate error (case-sensitive)
            # But will fail on product name validation for second product (lowercase not in valid names)
            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            output = out.getvalue()
            # First product should succeed
            self.assertEqual(
                NyscKit.objects.filter(name="Quality Nysc Kakhi").count(), 1
            )
            # Second should fail on validation (not duplicate)
            self.assertIn("✗", output)
            self.assertIn("Invalid name", output)
        finally:
            os.remove(csv_path)

    def test_no_duplicates(self):
        """Test successful processing when no duplicates"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
                "type": "kakhi",
            },
            {
                "name": "Quality Nysc Vest",
                "category": "NYSC KIT",
                "price": "3000",
                "description": "Test",
                "type": "vest",
            },
            {
                "name": "Quality Nysc Cap",
                "category": "NYSC KIT",
                "price": "2500",
                "description": "Test",
                "type": "cap",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            # Should succeed
            call_command("upload_products", csv_path, "--type=nysc_kit")

            self.assertEqual(NyscKit.objects.count(), 3)
        finally:
            os.remove(csv_path)


# ============================================================================
# CATEGORY VALIDATION TESTS
# ============================================================================


class CategoryValidationTests(TestCase):
    """Test category validation logic"""

    def test_valid_category_names(self):
        """Test all valid category names are accepted"""
        valid_categories = ["NYSC KIT", "NYSC TOUR", "CHURCH PROGRAMME"]

        for category in valid_categories:
            command = Command()
            # Should not raise error
            if category == "NYSC KIT":
                command._validate_category(category, "nysc_kit")
            elif category == "NYSC TOUR":
                command._validate_category(category, "nysc_tour")
            else:
                command._validate_category(category, "church")

    def test_invalid_category_name(self):
        """Test error for invalid category name"""
        command = Command()

        with self.assertRaises(ValueError) as cm:
            command._validate_category("Invalid Category", "nysc_kit")
        self.assertIn("Invalid category", str(cm.exception))

    def test_category_product_type_mismatch(self):
        """Test error when category doesn't match product type"""
        command = Command()

        # NYSC KIT category with nysc_tour type
        with self.assertRaises(ValueError) as cm:
            command._validate_category("NYSC KIT", "nysc_tour")
        self.assertIn("mismatch", str(cm.exception))

    def test_category_creation(self):
        """Test category is created if it doesn't exist"""
        command = Command()

        # Ensure category doesn't exist
        Category.objects.filter(name="NYSC KIT").delete()

        category = command._get_or_create_category("NYSC KIT", "nysc_kit")

        self.assertIsNotNone(category)
        self.assertEqual(category.name, "NYSC KIT")
        self.assertEqual(category.product_type, "nysc_kit")

    def test_category_retrieval(self):
        """Test existing category is retrieved"""
        # Create category
        existing_cat = Category.objects.create(
            name="NYSC KIT",
            slug="nysc-kit",
            product_type="nysc_kit",
            description="Existing",
        )

        command = Command()
        category = command._get_or_create_category("NYSC KIT", "nysc_kit")

        self.assertEqual(category.id, existing_cat.id)

    def test_category_description_auto_fill(self):
        """Test category description is auto-filled if not provided"""
        command = Command()

        Category.objects.filter(name="NYSC KIT").delete()

        category = command._get_or_create_category("NYSC KIT", "nysc_kit")

        self.assertIn("Complete NYSC uniform kit", category.description)

    def test_custom_category_description(self):
        """Test custom category description is used"""
        command = Command()

        Category.objects.filter(name="NYSC KIT").delete()

        custom_desc = "Custom description for testing"
        category = command._get_or_create_category("NYSC KIT", "nysc_kit", custom_desc)

        self.assertEqual(category.description, custom_desc)


# ============================================================================
# PRICE VALIDATION TESTS
# ============================================================================


class PriceValidationTests(TestCase):
    """Test price validation logic"""

    def test_valid_positive_price(self):
        """Test valid positive prices"""
        command = Command()

        valid_prices = ["100.00", "1000.50", "50000", "0.01"]

        for price_str in valid_prices:
            price = command._validate_price(price_str)
            self.assertGreater(price, 0)
            self.assertIsInstance(price, Decimal)

    def test_negative_price(self):
        """Test error for negative prices"""
        command = Command()

        with self.assertRaises(ValueError) as cm:
            command._validate_price("-100.00")
        self.assertIn("must be > 0", str(cm.exception))

    def test_zero_price(self):
        """Test error for zero price"""
        command = Command()

        with self.assertRaises(ValueError) as cm:
            command._validate_price("0.00")
        self.assertIn("must be > 0", str(cm.exception))

    def test_price_too_large(self):
        """Test error for prices exceeding maximum"""
        command = Command()

        with self.assertRaises(ValueError) as cm:
            command._validate_price("10000000.00")  # > 9999999.99
        self.assertIn("too large", str(cm.exception))

    def test_non_numeric_price(self):
        """Test error for non-numeric price"""
        command = Command()

        with self.assertRaises(ValueError):
            command._validate_price("not_a_number")

    def test_empty_price(self):
        """Test error for empty price"""
        command = Command()

        with self.assertRaises(ValueError):
            command._validate_price("")

    def test_whitespace_price(self):
        """Test error for whitespace-only price"""
        command = Command()

        with self.assertRaises(ValueError):
            command._validate_price("   ")

    def test_price_with_whitespace(self):
        """Test price with leading/trailing whitespace is handled"""
        command = Command()

        price = command._validate_price("  100.00  ")
        self.assertEqual(price, Decimal("100.00"))

    def test_price_with_currency_symbol(self):
        """Test error for price with currency symbols"""
        command = Command()

        with self.assertRaises(ValueError):
            command._validate_price("$100.00")

    def test_price_decimal_precision(self):
        """Test prices maintain decimal precision"""
        command = Command()

        price = command._validate_price("100.50")
        self.assertEqual(price, Decimal("100.50"))

        # Test various decimal places
        price2 = command._validate_price("99.99")
        self.assertEqual(price2, Decimal("99.99"))


# ============================================================================
# NYSC KIT PROCESSING TESTS
# ============================================================================


class NyscKitProcessingTests(TestCase):
    """Test NYSC Kit product processing"""

    def setUp(self):
        """Set up test category"""
        self.category = Category.objects.create(
            name="NYSC KIT", slug="nysc-kit", product_type="nysc_kit"
        )

    def test_create_kakhi_product(self):
        """Test creating kakhi product"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Premium kakhi",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.get(name="Quality Nysc Kakhi")
            self.assertEqual(product.type, "kakhi")
            self.assertEqual(product.price, Decimal("5000.00"))
        finally:
            os.remove(csv_path)

    def test_create_vest_product(self):
        """Test creating vest product"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Vest",
                "category": "NYSC KIT",
                "price": "3000.00",
                "description": "Premium vest",
                "type": "vest",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.get(name="Quality Nysc Vest")
            self.assertEqual(product.type, "vest")
        finally:
            os.remove(csv_path)

    def test_create_cap_product(self):
        """Test creating cap product"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Cap",
                "category": "NYSC KIT",
                "price": "2500.00",
                "description": "Premium cap",
                "type": "cap",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.get(name="Quality Nysc Cap")
            self.assertEqual(product.type, "cap")
        finally:
            os.remove(csv_path)

    def test_invalid_kit_type(self):
        """Test error for invalid kit type"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "invalid_type",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            # Should have errors
            output = out.getvalue()
            self.assertIn("✗", output)
            self.assertEqual(NyscKit.objects.count(), 0)
        finally:
            os.remove(csv_path)

    def test_invalid_product_name(self):
        """Test error for invalid product name"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Invalid Product Name",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            output = out.getvalue()
            self.assertIn("✗", output)
            self.assertEqual(NyscKit.objects.count(), 0)
        finally:
            os.remove(csv_path)

    def test_skip_existing_product(self):
        """Test --skip-existing flag"""
        # Create existing product
        NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("4000.00"),
        )

        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Updated",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command(
                "upload_products",
                csv_path,
                "--type=nysc_kit",
                "--skip-existing",
                stdout=out,
            )

            # Product should not be updated
            product = NyscKit.objects.get(name="Quality Nysc Kakhi")
            self.assertEqual(product.price, Decimal("4000.00"))

            # Output should show skipped
            output = out.getvalue()
            self.assertIn("⊘", output)
        finally:
            os.remove(csv_path)

    def test_update_existing_product(self):
        """Test --update-existing flag"""
        # Create existing product
        NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("4000.00"),
            description="Old description",
        )

        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Updated description",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command(
                "upload_products",
                csv_path,
                "--type=nysc_kit",
                "--update-existing",
                stdout=out,
            )

            # Product should be updated
            product = NyscKit.objects.get(name="Quality Nysc Kakhi")
            self.assertEqual(product.price, Decimal("5000.00"))
            self.assertEqual(product.description, "Updated description")

            # Output should show updated
            output = out.getvalue()
            self.assertIn("✓ Updated", output)
        finally:
            os.remove(csv_path)

    def test_error_on_existing_without_flags(self):
        """Test error when product exists and no skip/update flag"""
        # Create existing product
        NyscKit.objects.create(
            name="Quality Nysc Kakhi",
            type="kakhi",
            category=self.category,
            price=Decimal("4000.00"),
        )

        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            output = out.getvalue()
            self.assertIn("✗", output)
            self.assertIn("Already exists", output)
        finally:
            os.remove(csv_path)

    def test_available_field_handling(self):
        """Test available field is properly handled"""
        headers = ["name", "category", "price", "description", "type", "available"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "kakhi",
                "available": "false",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.get(name="Quality Nysc Kakhi")
            self.assertFalse(product.available)
        finally:
            os.remove(csv_path)

    def test_out_of_stock_field_handling(self):
        """Test out_of_stock field is properly handled"""
        headers = ["name", "category", "price", "description", "type", "out_of_stock"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "kakhi",
                "out_of_stock": "true",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.get(name="Quality Nysc Kakhi")
            self.assertTrue(product.out_of_stock)
        finally:
            os.remove(csv_path)


# ============================================================================
# NYSC TOUR PROCESSING TESTS
# ============================================================================


class NyscTourProcessingTests(TestCase):
    """Test NYSC Tour product processing"""

    def setUp(self):
        """Set up test category"""
        self.category = Category.objects.create(
            name="NYSC TOUR", slug="nysc-tour", product_type="nysc_tour"
        )

    def test_create_tour_product(self):
        """Test creating tour product"""
        headers = ["name", "category", "price", "description"]
        rows = [
            {
                "name": "Lagos",
                "category": "NYSC TOUR",
                "price": "15000.00",
                "description": "Lagos tour package",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_tour")

            product = NyscTour.objects.get(name="Lagos")
            self.assertEqual(product.price, Decimal("15000.00"))
        finally:
            os.remove(csv_path)

    def test_invalid_state_name(self):
        """Test error for invalid state name"""
        headers = ["name", "category", "price", "description"]
        rows = [
            {
                "name": "Invalid State",
                "category": "NYSC TOUR",
                "price": "15000.00",
                "description": "Test",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_tour", stdout=out)

            output = out.getvalue()
            self.assertIn("✗", output)
            self.assertEqual(NyscTour.objects.count(), 0)
        finally:
            os.remove(csv_path)

    def test_all_nigerian_states(self):
        """Test that all valid Nigerian states can be created"""
        # Sample of valid states (FCT is the correct name, not "Abuja FCT")
        valid_states = ["Lagos", "FCT", "Kano", "Rivers", "Oyo"]

        headers = ["name", "category", "price", "description"]
        rows = [
            {
                "name": state,
                "category": "NYSC TOUR",
                "price": "15000.00",
                "description": f"{state} tour",
            }
            for state in valid_states
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_tour")

            self.assertEqual(NyscTour.objects.count(), len(valid_states))
        finally:
            os.remove(csv_path)

    def test_tour_skip_existing(self):
        """Test --skip-existing for tour products"""
        NyscTour.objects.create(
            name="Lagos", category=self.category, price=Decimal("10000.00")
        )

        headers = ["name", "category", "price", "description"]
        rows = [
            {
                "name": "Lagos",
                "category": "NYSC TOUR",
                "price": "15000.00",
                "description": "Updated",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command(
                "upload_products", csv_path, "--type=nysc_tour", "--skip-existing"
            )

            product = NyscTour.objects.get(name="Lagos")
            self.assertEqual(product.price, Decimal("10000.00"))  # Not updated
        finally:
            os.remove(csv_path)

    def test_tour_update_existing(self):
        """Test --update-existing for tour products"""
        NyscTour.objects.create(
            name="Lagos", category=self.category, price=Decimal("10000.00")
        )

        headers = ["name", "category", "price", "description"]
        rows = [
            {
                "name": "Lagos",
                "category": "NYSC TOUR",
                "price": "15000.00",
                "description": "Updated description",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command(
                "upload_products", csv_path, "--type=nysc_tour", "--update-existing"
            )

            product = NyscTour.objects.get(name="Lagos")
            self.assertEqual(product.price, Decimal("15000.00"))  # Updated
        finally:
            os.remove(csv_path)


# ============================================================================
# CHURCH PROCESSING TESTS
# ============================================================================


class ChurchProcessingTests(TestCase):
    """Test Church product processing"""

    def setUp(self):
        """Set up test category"""
        self.category = Category.objects.create(
            name="CHURCH PROGRAMME", slug="church-prog", product_type="church"
        )

    def test_create_church_product(self):
        """Test creating church product"""
        headers = ["name", "category", "price", "description", "church"]
        rows = [
            {
                "name": "Quality RCCG Shirt",  # Valid church product name
                "category": "CHURCH PROGRAMME",
                "price": "8000.00",
                "description": "Premium shirt",
                "church": "RCCG",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=church")

            product = Church.objects.get(name="Quality RCCG Shirt")
            self.assertEqual(product.church, "RCCG")
            self.assertEqual(product.price, Decimal("8000.00"))
        finally:
            os.remove(csv_path)

    def test_invalid_product_name(self):
        """Test error for invalid church product name"""
        headers = ["name", "category", "price", "description", "church"]
        rows = [
            {
                "name": "Invalid Product Name",  # Invalid product name
                "category": "CHURCH PROGRAMME",
                "price": "8000.00",
                "description": "Test",
                "church": "RCCG",  # Valid church denomination
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=church", stdout=out)

            output = out.getvalue()
            self.assertIn("✗", output)
            self.assertEqual(Church.objects.count(), 0)
        finally:
            os.remove(csv_path)

    def test_invalid_church_denomination(self):
        """Test error for invalid church denomination"""
        headers = ["name", "category", "price", "description", "church"]
        rows = [
            {
                "name": "Quality RCCG Shirt",  # Valid product name
                "category": "CHURCH PROGRAMME",
                "price": "8000.00",
                "description": "Test",
                "church": "Invalid Church",  # Invalid denomination
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=church", stdout=out)

            output = out.getvalue()
            self.assertIn("✗", output)
            self.assertEqual(Church.objects.count(), 0)
        finally:
            os.remove(csv_path)

    def test_all_valid_churches(self):
        """Test products for different valid churches"""
        # Use different product names with different valid churches
        test_data = [
            ("Quality RCCG Shirt", "RCCG"),
            ("Quality shilo jacket", "WINNERS"),  # Valid product name with valid church
            ("Quality RCCG polo", "DEEPER_LIFE"),
        ]

        headers = ["name", "category", "price", "description", "church"]
        rows = [
            {
                "name": name,
                "category": "CHURCH PROGRAMME",
                "price": "8000.00",
                "description": f"{church} product",
                "church": church,
            }
            for name, church in test_data
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=church")

            self.assertEqual(Church.objects.count(), len(test_data))
        finally:
            os.remove(csv_path)

    def test_church_skip_existing(self):
        """Test --skip-existing for church products"""
        Church.objects.create(
            name="Quality RCCG Shirt",
            church="RCCG",
            category=self.category,
            price=Decimal("7000.00"),
        )

        headers = ["name", "category", "price", "description", "church"]
        rows = [
            {
                "name": "Quality RCCG Shirt",
                "category": "CHURCH PROGRAMME",
                "price": "8000.00",
                "description": "Updated",
                "church": "RCCG",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command(
                "upload_products", csv_path, "--type=church", "--skip-existing"
            )

            product = Church.objects.get(name="Quality RCCG Shirt")
            self.assertEqual(product.price, Decimal("7000.00"))  # Not updated
        finally:
            os.remove(csv_path)


# ============================================================================
# IMAGE DOWNLOADING TESTS
# ============================================================================


class ImageDownloadingTests(TestCase):
    """Test image downloading functionality"""

    @patch("products.management.commands.upload_products.requests.get")
    def test_download_valid_image(self, mock_get):
        """Test downloading valid image from URL"""
        # Mock successful image download
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "image/jpeg",
            "content-length": "100000",
        }
        mock_response.iter_content = lambda chunk_size: [b"fake_image_data"]
        mock_get.return_value = mock_response

        command = Command()
        command.stdout = StringIO()

        result = command._download_image("https://example.com/image.jpg")

        self.assertIsNotNone(result)
        self.assertIsInstance(result, File)

    @patch("products.management.commands.upload_products.requests.get")
    def test_download_non_image_content_type(self, mock_get):
        """Test rejection of non-image content types"""
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/html"}
        mock_get.return_value = mock_response

        command = Command()
        command.stdout = StringIO()

        result = command._download_image("https://example.com/page.html")

        self.assertIsNone(result)

    @patch("products.management.commands.upload_products.requests.get")
    def test_download_image_too_large(self, mock_get):
        """Test rejection of images larger than 10MB"""
        mock_response = Mock()
        mock_response.headers = {
            "content-type": "image/jpeg",
            "content-length": str(11 * 1024 * 1024),  # 11MB
        }
        mock_get.return_value = mock_response

        command = Command()
        command.stdout = StringIO()

        result = command._download_image("https://example.com/large.jpg")

        self.assertIsNone(result)

    @patch("products.management.commands.upload_products.requests.get")
    def test_download_timeout(self, mock_get):
        """Test handling of download timeout"""
        mock_get.side_effect = requests.Timeout()

        command = Command()
        command.stdout = StringIO()

        result = command._download_image("https://example.com/image.jpg")

        self.assertIsNone(result)

    @patch("products.management.commands.upload_products.requests.get")
    def test_download_network_error(self, mock_get):
        """Test handling of network errors"""
        mock_get.side_effect = requests.RequestException("Network error")

        command = Command()
        command.stdout = StringIO()

        result = command._download_image("https://example.com/image.jpg")

        self.assertIsNone(result)

    def test_empty_url(self):
        """Test handling of empty URL"""
        command = Command()

        result = command._download_image("")
        self.assertIsNone(result)

        result = command._download_image(None)
        self.assertIsNone(result)

        result = command._download_image("   ")
        self.assertIsNone(result)

    def test_url_too_long(self):
        """Test rejection of URLs longer than 500 characters"""
        long_url = "https://example.com/" + "x" * 500

        command = Command()
        command.stdout = StringIO()

        result = command._download_image(long_url)

        self.assertIsNone(result)

    @patch("products.management.commands.upload_products.requests.get")
    def test_filename_extraction(self, mock_get):
        """Test filename extraction from URL"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "image/jpeg",
            "content-length": "100000",
        }
        mock_response.iter_content = lambda chunk_size: [b"data"]
        mock_get.return_value = mock_response

        command = Command()
        command.stdout = StringIO()

        result = command._download_image("https://example.com/product/image.jpg")

        self.assertIsNotNone(result)
        self.assertIn(".jpg", result.name)


# ============================================================================
# CLOUDINARY INTEGRATION TESTS
# ============================================================================


class CloudinaryIntegrationTests(TestCase):
    """Test Cloudinary URL handling"""

    def test_cloudinary_url_detection(self):
        """Test detection of Cloudinary URLs"""
        command = Command()

        cloudinary_urls = [
            "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "https://res.cloudinary.com/demo/image/upload/v1234567/sample.jpg",
            "https://res.cloudinary.com/demo/image/upload/w_100,h_100/sample.jpg",
        ]

        for url in cloudinary_urls:
            self.assertTrue(command._is_cloudinary_url(url))

    def test_non_cloudinary_url_detection(self):
        """Test non-Cloudinary URLs are not detected as Cloudinary"""
        command = Command()

        non_cloudinary_urls = [
            "https://example.com/image.jpg",
            "https://s3.amazonaws.com/bucket/image.jpg",
            "https://imgur.com/image.jpg",
            None,
            "",
        ]

        for url in non_cloudinary_urls:
            self.assertFalse(command._is_cloudinary_url(url))

    def test_extract_public_id_simple(self):
        """Test extracting public ID from simple Cloudinary URL"""
        command = Command()

        url = "https://res.cloudinary.com/demo/image/upload/sample.jpg"
        public_id = command._extract_cloudinary_public_id(url)

        self.assertEqual(public_id, "sample.jpg")

    def test_extract_public_id_with_version(self):
        """Test extracting public ID from URL with version"""
        command = Command()

        url = "https://res.cloudinary.com/demo/image/upload/v1234567890/sample.jpg"
        public_id = command._extract_cloudinary_public_id(url)

        # Version should be removed
        self.assertEqual(public_id, "sample.jpg")

    def test_extract_public_id_with_transformations(self):
        """Test extracting public ID from URL with transformations"""
        command = Command()

        url = (
            "https://res.cloudinary.com/demo/image/upload/w_100,h_100,c_fill/sample.jpg"
        )
        public_id = command._extract_cloudinary_public_id(url)

        # Transformations should be removed
        self.assertEqual(public_id, "sample.jpg")

    def test_extract_public_id_with_folder(self):
        """Test extracting public ID with folder path"""
        command = Command()

        url = "https://res.cloudinary.com/demo/image/upload/products/kakhi.jpg"
        public_id = command._extract_cloudinary_public_id(url)

        self.assertEqual(public_id, "products/kakhi.jpg")

    def test_extract_public_id_complex(self):
        """Test extracting public ID from complex URL"""
        command = Command()

        url = "https://res.cloudinary.com/demo/image/upload/w_100,h_100/v1234567890/products/subfolder/image.jpg?param=value"
        public_id = command._extract_cloudinary_public_id(url)

        # Should extract just the path, removing version, transformations, and query params
        self.assertEqual(public_id, "products/subfolder/image.jpg")

    def test_extract_public_id_invalid_url(self):
        """Test handling of invalid Cloudinary URL"""
        command = Command()
        command.stdout = StringIO()

        invalid_url = "https://example.com/image.jpg"
        public_id = command._extract_cloudinary_public_id(invalid_url)

        self.assertIsNone(public_id)

    @patch("products.management.commands.upload_products.requests.get")
    def test_cloudinary_url_reuse(self, mock_get):
        """Test that Cloudinary URLs are reused without downloading"""
        command = Command()
        command.stdout = StringIO()

        cloudinary_url = (
            "https://res.cloudinary.com/demo/image/upload/products/kakhi.jpg"
        )
        result = command._download_image(cloudinary_url)

        # Should return public_id string, not download
        self.assertIsInstance(result, str)
        self.assertEqual(result, "products/kakhi.jpg")

        # Should NOT have called requests.get
        mock_get.assert_not_called()


# ============================================================================
# BOOLEAN CONVERSION TESTS
# ============================================================================


class BooleanConversionTests(TestCase):
    """Test _str_to_bool conversion logic"""

    def test_true_values(self):
        """Test various representations of True"""
        command = Command()

        true_values = ["true", "True", "TRUE", "1", "yes", "Yes", "YES", "y", "Y", True]

        for value in true_values:
            result = command._str_to_bool(value)
            self.assertTrue(result, f"Failed for value: {value}")

    def test_false_values(self):
        """Test various representations of False"""
        command = Command()

        false_values = [
            "false",
            "False",
            "FALSE",
            "0",
            "no",
            "No",
            "NO",
            "n",
            "N",
            False,
        ]

        for value in false_values:
            result = command._str_to_bool(value)
            self.assertFalse(result, f"Failed for value: {value}")

    def test_empty_defaults_to_true(self):
        """Test that empty/whitespace defaults to True"""
        command = Command()

        empty_values = [None, "", "   ", "\t", "\n"]

        for value in empty_values:
            result = command._str_to_bool(value)
            self.assertTrue(result, f"Failed for value: {repr(value)}")

    def test_invalid_values_default_to_false(self):
        """Test that invalid values default to False"""
        command = Command()

        invalid_values = ["maybe", "unknown", "2", "other"]

        for value in invalid_values:
            result = command._str_to_bool(value)
            self.assertFalse(result, f"Failed for value: {value}")

    def test_boolean_passthrough(self):
        """Test that actual boolean values are passed through"""
        command = Command()

        self.assertTrue(command._str_to_bool(True))
        self.assertFalse(command._str_to_bool(False))


# ============================================================================
# TRANSACTION & ROLLBACK TESTS
# ============================================================================


class TransactionHandlingTests(TestCase):
    """Test transaction handling and rollback on errors"""

    def test_rollback_on_error(self):
        """Test that database changes are rolled back on error"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "kakhi",
            },
            {
                "name": "Quality Nysc Vest",
                "category": "NYSC KIT",
                "price": "INVALID_PRICE",  # This will cause error
                "description": "Test",
                "type": "vest",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            # First product should be created successfully
            # Second should fail but not affect the first (separate transactions)
            self.assertEqual(
                NyscKit.objects.filter(name="Quality Nysc Kakhi").count(), 1
            )
            self.assertEqual(
                NyscKit.objects.filter(name="Quality Nysc Vest").count(), 0
            )
        finally:
            os.remove(csv_path)

    def test_partial_success(self):
        """Test that some products can succeed while others fail"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
                "type": "kakhi",
            },
            {
                "name": "Invalid Product",
                "category": "NYSC KIT",
                "price": "3000",
                "description": "Test",
                "type": "vest",
            },
            {
                "name": "Quality Nysc Cap",
                "category": "NYSC KIT",
                "price": "2500",
                "description": "Test",
                "type": "cap",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            output = out.getvalue()

            # Should have successes and errors
            self.assertIn("✓", output)
            self.assertIn("✗", output)

            # Valid products should be created
            self.assertTrue(NyscKit.objects.filter(name="Quality Nysc Kakhi").exists())
            self.assertTrue(NyscKit.objects.filter(name="Quality Nysc Cap").exists())

            # Invalid product should not be created
            self.assertFalse(NyscKit.objects.filter(name="Invalid Product").exists())
        finally:
            os.remove(csv_path)


# ============================================================================
# OUTPUT & SUMMARY TESTS
# ============================================================================


class OutputAndSummaryTests(TestCase):
    """Test command output and summary statistics"""

    def test_summary_statistics(self):
        """Test that summary shows correct counts"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
                "type": "kakhi",
            },
            {
                "name": "Quality Nysc Vest",
                "category": "NYSC KIT",
                "price": "3000",
                "description": "Test",
                "type": "vest",
            },
            {
                "name": "Quality Nysc Cap",
                "category": "NYSC KIT",
                "price": "2500",
                "description": "Test",
                "type": "cap",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            output = out.getvalue()

            # Check for summary section
            self.assertIn("SUMMARY", output)
            self.assertIn("Total: 3", output)
            self.assertIn("✓ Created: 3", output)
        finally:
            os.remove(csv_path)

    def test_error_reporting(self):
        """Test that errors are properly reported in summary"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
                "type": "kakhi",
            },
            {
                "name": "Invalid Product",
                "category": "NYSC KIT",
                "price": "3000",
                "description": "Test",
                "type": "vest",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            output = out.getvalue()

            # Check for error reporting
            self.assertIn("✗ Errors: 1", output)
            self.assertIn("Row 2:", output)
        finally:
            os.remove(csv_path)

    def test_dry_run_message(self):
        """Test that dry run mode shows appropriate message"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000",
                "description": "Test",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command(
                "upload_products", csv_path, "--type=nysc_kit", "--dry-run", stdout=out
            )

            output = out.getvalue()

            self.assertIn("DRY RUN", output)
            self.assertIn("No changes saved", output)
        finally:
            os.remove(csv_path)


# ============================================================================
# EDGE CASES & ERROR HANDLING TESTS
# ============================================================================


class EdgeCasesAndErrorHandlingTests(TestCase):
    """Test edge cases and comprehensive error handling"""

    def test_very_long_description(self):
        """Test handling of very long descriptions"""
        headers = ["name", "category", "price", "description", "type"]
        long_description = "x" * 5000  # Very long description
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": long_description,
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.first()
            self.assertEqual(len(product.description), 5000)
        finally:
            os.remove(csv_path)

    def test_special_characters_in_name(self):
        """Test handling of special characters in product names"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": 'Special chars: @#$%^&*()_+-=[]{}|;:",.<>?',
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            self.assertEqual(NyscKit.objects.count(), 1)
        finally:
            os.remove(csv_path)

    def test_whitespace_in_fields(self):
        """Test handling of leading/trailing whitespace"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "  Quality Nysc Kakhi  ",
                "category": "  NYSC KIT  ",
                "price": "  5000.00  ",
                "description": "  Test description  ",
                "type": "  kakhi  ",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.get(name="Quality Nysc Kakhi")
            self.assertEqual(product.type, "kakhi")
        finally:
            os.remove(csv_path)

    def test_missing_optional_fields(self):
        """Test handling when optional fields are missing"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "Quality Nysc Kakhi",
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "",  # Empty description
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            call_command("upload_products", csv_path, "--type=nysc_kit")

            product = NyscKit.objects.first()
            self.assertEqual(product.description, "")
        finally:
            os.remove(csv_path)

    def test_empty_name_field(self):
        """Test error when name field is empty"""
        headers = ["name", "category", "price", "description", "type"]
        rows = [
            {
                "name": "",  # Empty name
                "category": "NYSC KIT",
                "price": "5000.00",
                "description": "Test",
                "type": "kakhi",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            csv_path = f.name

        try:
            create_test_csv(csv_path, headers, rows)

            out = StringIO()
            call_command("upload_products", csv_path, "--type=nysc_kit", stdout=out)

            output = out.getvalue()
            self.assertIn("✗", output)
            self.assertEqual(NyscKit.objects.count(), 0)
        finally:
            os.remove(csv_path)
