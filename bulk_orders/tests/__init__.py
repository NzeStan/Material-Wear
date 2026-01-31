# bulk_orders/tests/__init__.py
"""
Comprehensive test suite for bulk_orders app.

This test suite provides extensive coverage of all bulk_orders functionality:

TEST MODULES:
=============

1. test_models.py (3 test classes, 100+ tests)
   - BulkOrderLinkModelTest: Slug generation, expiry logic, organization name normalization
   - CouponCodeModelTest: Uniqueness, usage tracking, relationships
   - OrderEntryModelTest: Reference generation, serial numbers, concurrent operations

2. test_serializers.py (4 test classes, 50+ tests)
   - BulkOrderLinkSummarySerializerTest: Field validation, method fields
   - CouponCodeSerializerTest: Read-only fields, related field serialization
   - OrderEntrySerializerTest: Coupon validation, custom_name conditional logic
   - BulkOrderLinkSerializerTest: Full CRUD serialization

3. test_views.py (5 test classes, 60+ tests)
   - BulkOrderLinkViewSetTest: CRUD operations, permissions, actions
   - OrderEntryViewSetTest: List/retrieve, payment initialization, payment verification
   - CouponCodeViewSetTest: Admin-only access, validation endpoints
   - BulkOrderPaymentWebhookTest: Paystack webhook handling, signature verification
   - Integration tests for end-to-end flows

4. test_utils.py (5 test classes, 40+ tests)
   - GenerateCouponCodesTest: Coupon generation, uniqueness validation
   - GetBulkOrderWithOrdersTest: Query optimization helper
   - GenerateBulkOrderPDFTest: PDF generation, content validation
   - GenerateBulkOrderWordTest: DOCX generation, formatting
   - GenerateBulkOrderExcelTest: XLSX generation, data integrity

5. test_admin.py (6 test classes, 50+ tests)
   - BulkOrderLinkAdminTest: List display, actions, filters
   - OrderEntryAdminTest: Custom display methods, filtering
   - CouponCodeInlineTest: Inline behavior, permissions
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
- Ordering and indexing

Serializers:
- Field serialization and deserialization
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
- Error handling and edge cases

Utilities:
- Coupon code generation with uniqueness guarantees
- Document generation (PDF, DOCX, XLSX)
- Query optimization helpers
- Background task integration
- Error handling and logging

Admin Interface:
- List display and filtering
- Custom display methods
- Inline editing
- Bulk actions
- Permission checks
- Admin integration tests

Security:
- Permission enforcement
- Queryset filtering by ownership
- Webhook signature verification
- Rate limiting (via throttle classes)
- Input sanitization

RUNNING TESTS:
==============

Run all bulk_orders tests:
    python manage.py test bulk_orders.tests

Run specific test module:
    python manage.py test bulk_orders.tests.test_models
    python manage.py test bulk_orders.tests.test_serializers
    python manage.py test bulk_orders.tests.test_views
    python manage.py test bulk_orders.tests.test_utils
    python manage.py test bulk_orders.tests.test_admin

Run specific test class:
    python manage.py test bulk_orders.tests.test_models.BulkOrderLinkModelTest
    python manage.py test bulk_orders.tests.test_views.BulkOrderLinkViewSetTest

Run specific test method:
    python manage.py test bulk_orders.tests.test_models.BulkOrderLinkModelTest.test_slug_auto_generation

Run with coverage:
    coverage run --source='bulk_orders' manage.py test bulk_orders.tests
    coverage report
    coverage html

Run with verbose output:
    python manage.py test bulk_orders.tests --verbosity=2

Run tests in parallel (faster):
    python manage.py test bulk_orders.tests --parallel

IMPORTANT NOTES:
================

1. Database: Tests use TransactionTestCase where needed for atomic operations
2. Mocking: External services (Paystack, WeasyPrint, etc.) are mocked
3. Fixtures: Test data is created in setUp methods for isolation
4. Cleanup: Django handles test database cleanup automatically

TEST DATA PATTERNS:
===================

All tests follow consistent patterns:
- User: email='test@example.com', password='testpass123'
- Bulk Orders: organization_name='Test Church', price_per_item=Decimal('5000.00')
- Orders: email='user@example.com', full_name='Test User', size='M'
- Coupons: code='TEST1234' (8 uppercase alphanumeric)
- Timestamps: timezone.now() + timedelta(days=30) for future deadlines

EDGE CASES COVERED:
===================

- Empty bulk orders (no orders)
- Expired bulk orders
- Concurrent order creation
- Duplicate coupon codes
- Invalid payment references
- Missing required fields
- Cross-bulk-order operations
- Very long names and slugs
- Special characters in names
- Already-paid orders
- Used coupons
- Webhook replay attacks
- Invalid signatures
- Network failures
- Background task failures

PRODUCTION READINESS:
=====================

These tests are designed to catch production bugs before deployment:
✓ Security vulnerabilities (permission bypasses, injection attacks)
✓ Race conditions (concurrent serial number generation)
✓ Data integrity issues (orphaned records, invalid references)
✓ API contract violations (unexpected response formats)
✓ Business logic errors (coupon reuse, payment verification)
✓ Performance issues (N+1 queries, missing indexes)
✓ Edge cases (expired orders, empty data, malformed input)

CONTINUOUS INTEGRATION:
=======================

Recommended CI configuration:
- Run tests on every commit
- Require 90%+ coverage
- Run with --parallel for speed
- Run with --failfast during development
- Include linting and type checking
- Test against multiple Python/Django versions

MAINTENANCE:
============

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
"""

# Import all test classes for easy access
from .test_models import (
    BulkOrderLinkModelTest,
    CouponCodeModelTest,
    OrderEntryModelTest,
)

from .test_serializers import (
    BulkOrderLinkSummarySerializerTest,
    CouponCodeSerializerTest,
    OrderEntrySerializerTest,
    BulkOrderLinkSerializerTest,
)

from .test_views import (
    BulkOrderLinkViewSetTest,
    OrderEntryViewSetTest,
    CouponCodeViewSetTest,
    BulkOrderPaymentWebhookTest,
)

from .test_utils import (
    GenerateCouponCodesTest,
    GetBulkOrderWithOrdersTest,
    GenerateBulkOrderPDFTest,
    GenerateBulkOrderWordTest,
    GenerateBulkOrderExcelTest,
    DocumentGenerationIntegrationTest,
)

from .test_admin import (
    BulkOrderLinkAdminTest,
    OrderEntryAdminTest,
    CouponCodeInlineTest,
    HasCouponFilterTest,
    AdminIntegrationTest,
)

__all__ = [
    # Models
    'BulkOrderLinkModelTest',
    'CouponCodeModelTest',
    'OrderEntryModelTest',
    
    # Serializers
    'BulkOrderLinkSummarySerializerTest',
    'CouponCodeSerializerTest',
    'OrderEntrySerializerTest',
    'BulkOrderLinkSerializerTest',
    
    # Views
    'BulkOrderLinkViewSetTest',
    'OrderEntryViewSetTest',
    'CouponCodeViewSetTest',
    'BulkOrderPaymentWebhookTest',
    
    # Utils
    'GenerateCouponCodesTest',
    'GetBulkOrderWithOrdersTest',
    'GenerateBulkOrderPDFTest',
    'GenerateBulkOrderWordTest',
    'GenerateBulkOrderExcelTest',
    'DocumentGenerationIntegrationTest',
    
    # Admin
    'BulkOrderLinkAdminTest',
    'OrderEntryAdminTest',
    'CouponCodeInlineTest',
    'HasCouponFilterTest',
    'AdminIntegrationTest',
]