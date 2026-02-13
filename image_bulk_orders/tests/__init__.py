# image_bulk_orders/tests/__init__.py
"""
Comprehensive test suite for image_bulk_orders app.

This test suite provides extensive coverage of all image_bulk_orders functionality:

TEST MODULES:
=============

1. test_models.py (3 test classes, 100+ tests)
   - ImageBulkOrderLinkModelTest: Slug generation, expiry logic, organization name normalization
   - ImageCouponCodeModelTest: Uniqueness, usage tracking, relationships
   - ImageOrderEntryModelTest: Reference generation, serial numbers, image field, concurrent operations

2. test_serializers.py (4 test classes, 70+ tests)
   - ImageBulkOrderLinkSummarySerializerTest: Field validation, method fields
   - ImageCouponCodeSerializerTest: Read-only fields, related field serialization
   - ImageOrderEntrySerializerTest: Coupon validation, image validation, custom_name conditional logic
   - ImageBulkOrderLinkSerializerTest: Full CRUD serialization

3. test_views.py (4 test classes, 60+ tests)
   - ImageBulkOrderLinkViewSetTest: CRUD operations, permissions, actions
   - ImageOrderEntryViewSetTest: List/retrieve, payment initialization, payment verification
   - ImageCouponCodeViewSetTest: Admin-only access, validation endpoints
   - ImageBulkOrderPaymentWebhookTest: Paystack webhook handling, signature verification

4. test_utils.py (7 test classes, 50+ tests)
   - GenerateCouponCodesImageTest: Coupon generation, uniqueness validation
   - GetImageBulkOrderWithOrdersTest: Query optimization helper
   - GenerateImageBulkOrderPDFTest: PDF generation, content validation
   - GenerateImageBulkOrderWordTest: DOCX generation, formatting
   - GenerateImageBulkOrderExcelTest: XLSX generation, data integrity
   - DownloadImageFromCloudinaryTest: Image downloading
   - GenerateAdminPackageWithImagesTest: Complete package generation

5. test_admin.py (7 test classes, 60+ tests)
   - ImageBulkOrderLinkAdminTest: List display, actions, filters
   - ImageOrderEntryAdminTest: Custom display methods, image handling, filtering
   - ImageCouponCodeInlineTest: Inline behavior, permissions
   - HasCouponFilterTest: Custom filter functionality
   - AdminIntegrationTest: End-to-end admin workflows

COVERAGE AREAS:
===============

Models:
- Field validation and constraints
- Auto-generated fields (slug, reference, serial_number)
- Model save hooks and normalization
- Relationships and cascading deletes
- Concurrent operations and race conditions
- Image field handling (CloudinaryField)
- Ordering and indexing

Serializers:
- Field serialization and deserialization
- Image validation (file type, size using python-magic)
- Validation logic (coupon codes, expiry, custom names)
- Conditional field inclusion
- Nested serialization
- Read-only and write-only fields
- Context-dependent behavior

Views & API Endpoints:
- Authentication and permissions
- Public vs authenticated access
- Queryset filtering by user
- Custom actions (generate_coupons, submit_order, initialize_payment, verify_payment)
- Webhook handling with signature verification
- Stats endpoint with caching
- Error handling and edge cases

Utilities:
- Coupon code generation with uniqueness guarantees
- Document generation (PDF, DOCX, XLSX)
- Image downloading from Cloudinary
- Complete package generation with images
- Query optimization helpers
- Error handling and logging

Admin Interface:
- List display and filtering
- Custom display methods (image thumbnails, links)
- Inline editing
- Bulk actions (PDF/Word/Excel downloads, package generation)
- Permission checks
- Admin integration tests

Security:
- Permission enforcement
- Queryset filtering by ownership
- Webhook signature verification
- Rate limiting (via throttle classes)
- Input sanitization
- Image validation

RUNNING TESTS:
==============

Run all image_bulk_orders tests:
    python manage.py test image_bulk_orders.tests

Run specific test module:
    python manage.py test image_bulk_orders.tests.test_models
    python manage.py test image_bulk_orders.tests.test_serializers
    python manage.py test image_bulk_orders.tests.test_views
    python manage.py test image_bulk_orders.tests.test_utils
    python manage.py test image_bulk_orders.tests.test_admin

Run specific test class:
    python manage.py test image_bulk_orders.tests.test_models.ImageBulkOrderLinkModelTest
    python manage.py test image_bulk_orders.tests.test_views.ImageBulkOrderLinkViewSetTest

Run specific test method:
    python manage.py test image_bulk_orders.tests.test_models.ImageBulkOrderLinkModelTest.test_slug_auto_generation

Run with coverage:
    coverage run --source='image_bulk_orders' manage.py test image_bulk_orders.tests
    coverage report
    coverage html

Run with verbose output:
    python manage.py test image_bulk_orders.tests --verbosity=2

Run tests in parallel (faster):
    python manage.py test image_bulk_orders.tests --parallel

IMPORTANT NOTES:
================

1. Database: Tests use TransactionTestCase where needed for atomic operations
2. Mocking: External services (Paystack, WeasyPrint, Cloudinary) are mocked
3. Fixtures: Test data is created in setUp methods for isolation
4. Image Validation: Uses python-magic for proper MIME type checking
5. Concurrent Tests: Serial number generation tested for race conditions

DEVELOPMENT WORKFLOW:
====================

When adding new features:
1. Add tests FIRST (TDD approach)
2. Ensure new code has >90% coverage
3. Add integration tests for new workflows
4. Update this documentation
5. Run full test suite before committing

When fixing bugs:
1. Write failing test that reproduces bug
2. Fix the bug
3. Verify test now passes
4. Add regression test to prevent recurrence

Security testing:
1. Always test authentication and authorization
2. Test input validation and sanitization
3. Test file upload security (image validation)
4. Test webhook signature verification
5. Test for SQL injection and XSS vulnerabilities
6. Test race conditions for payment operations
7. Test idempotency for critical operations
"""

# Import all test classes for easy access
from .test_models import (
    ImageBulkOrderLinkModelTest,
    ImageCouponCodeModelTest,
    ImageOrderEntryModelTest,
)

from .test_serializers import (
    ImageBulkOrderLinkSummarySerializerTest,
    ImageCouponCodeSerializerTest,
    ImageOrderEntrySerializerTest,
    ImageBulkOrderLinkSerializerTest,
)

from .test_views import (
    ImageBulkOrderLinkViewSetTest,
    ImageOrderEntryViewSetTest,
    ImageCouponCodeViewSetTest,
    ImageBulkOrderPaymentWebhookTest,
)

from .test_utils import (
    GenerateCouponCodesImageTest,
    GetImageBulkOrderWithOrdersTest,
    GenerateImageBulkOrderPDFTest,
    GenerateImageBulkOrderWordTest,
    GenerateImageBulkOrderExcelTest,
    DownloadImageFromCloudinaryTest,
    GenerateAdminPackageWithImagesTest,
)

from .test_admin import (
    ImageBulkOrderLinkAdminTest,
    ImageOrderEntryAdminTest,
    ImageCouponCodeInlineTest,
    HasCouponFilterTest,
    AdminIntegrationTest,
)

__all__ = [
    # Models
    'ImageBulkOrderLinkModelTest',
    'ImageCouponCodeModelTest',
    'ImageOrderEntryModelTest',
    
    # Serializers
    'ImageBulkOrderLinkSummarySerializerTest',
    'ImageCouponCodeSerializerTest',
    'ImageOrderEntrySerializerTest',
    'ImageBulkOrderLinkSerializerTest',
    
    # Views
    'ImageBulkOrderLinkViewSetTest',
    'ImageOrderEntryViewSetTest',
    'ImageCouponCodeViewSetTest',
    'ImageBulkOrderPaymentWebhookTest',
    
    # Utils
    'GenerateCouponCodesImageTest',
    'GetImageBulkOrderWithOrdersTest',
    'GenerateImageBulkOrderPDFTest',
    'GenerateImageBulkOrderWordTest',
    'GenerateImageBulkOrderExcelTest',
    'DownloadImageFromCloudinaryTest',
    'GenerateAdminPackageWithImagesTest',
    
    # Admin
    'ImageBulkOrderLinkAdminTest',
    'ImageOrderEntryAdminTest',
    'ImageCouponCodeInlineTest',
    'HasCouponFilterTest',
    'AdminIntegrationTest',
]