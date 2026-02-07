# excel_bulk_orders/tests/__init__.py
"""
Comprehensive test suite for excel_bulk_orders app.

SECURITY FOCUS:
===============
This test suite prioritizes security testing including:
- Payment webhook signature verification
- SQL injection prevention
- XSS attack prevention
- CSRF protection
- File upload validation (size limits, extensions)
- Input sanitization
- Authentication and authorization
- Idempotency in payment processing
- Race condition handling

TEST MODULES:
=============

1. test_models.py (3 test classes, 100+ tests)
   - ExcelBulkOrderModelTest: Reference generation, validation status, payment handling
   - ExcelCouponCodeModelTest: Code generation, uniqueness, case handling
   - ExcelParticipantModelTest: Data storage, coupon relationships, concurrent operations

2. test_serializers.py (6 test classes, 60+ tests)
   - ExcelBulkOrderCreateSerializerTest: Field validation, user assignment
   - ExcelBulkOrderListSerializerTest: Method fields, read-only behavior
   - ExcelBulkOrderDetailSerializerTest: Nested data, context handling
   - ExcelParticipantSerializerTest: Conditional fields, coupon status
   - ExcelUploadSerializerTest: File validation, security checks
   - ValidationErrorSerializerTest: Error response structure

3. test_views.py (8 test classes, 150+ tests)
   - ExcelBulkOrderViewSetTest: CRUD operations, permissions
   - ExcelUploadActionTest: File upload, Cloudinary integration
   - ExcelValidateActionTest: Excel validation, error reporting
   - ExcelInitializePaymentActionTest: Payment initialization
   - ExcelVerifyPaymentActionTest: Payment verification, participant creation
   - ExcelParticipantViewSetTest: List/retrieve, filtering
   - ExcelBulkOrderWebhookTest: Signature verification, idempotency
   - SecurityAndEdgeCaseTests: SQL injection, XSS, Unicode handling

4. test_utils.py (7 test classes, 40+ tests)
   - GenerateExcelCouponCodesTest: Coupon generation, uniqueness
   - GenerateExcelTemplateTest: Template creation, validation rules
   - ValidateExcelFileTest: Data validation, error detection
   - CreateParticipantsFromExcelTest: Participant creation, coupon handling
   - GenerateParticipantsPDFTest: PDF document generation
   - GenerateParticipantsWordTest: Word document generation
   - GenerateParticipantsExcelTest: Excel report generation

5. test_admin.py (3 test classes, 20+ tests)
   - ExcelBulkOrderAdminTest: List display, filters, actions
   - ExcelCouponCodeInlineTest: Inline behavior, permissions
   - ExcelParticipantInlineTest: Inline behavior, permissions

6. test_email_utils.py (1 test class, 10+ tests)
   - SendBulkOrderConfirmationEmailTest: Email sending, template rendering

COVERAGE AREAS:
===============

Models:
- Field validation and constraints
- Auto-generated fields (reference, coupon codes)
- Model save hooks and data normalization
- Relationships and cascading deletes
- Concurrent operations and race conditions
- Unique constraints and indexes

Serializers:
- Input validation and sanitization
- Email normalization
- File upload validation (size, extension)
- Conditional field inclusion
- Read-only and write-only fields
- Context-dependent behavior

Views & API Endpoints:
- Authentication and permissions
- Public vs authenticated access
- Queryset filtering by user
- Custom actions (upload, validate, initialize-payment, verify-payment)
- Webhook handling with signature verification
- Cloudinary integration
- Error handling and edge cases
- Idempotency in payment processing

Security:
- Webhook signature verification (CRITICAL)
- Payment verification before participant creation
- File upload validation (extensions, size limits)
- SQL injection prevention (parameterized queries)
- XSS prevention (proper serialization)
- CSRF protection (where applicable)
- Input sanitization
- Authorization checks
- Race condition handling

Utilities:
- Excel template generation with validation rules
- Excel file parsing and validation
- Participant creation with coupon handling
- Document generation (PDF, Word, Excel)
- Coupon code generation with uniqueness
- Error handling

Admin:
- List display and filters
- Inline displays
- Permissions and access control
- Read-only fields

Email:
- Template rendering
- Context data
- Error handling
- Plain text fallback

RUNNING TESTS:
==============

Run all tests:
    python manage.py test excel_bulk_orders

Run specific test module:
    python manage.py test excel_bulk_orders.tests.test_models
    python manage.py test excel_bulk_orders.tests.test_views
    python manage.py test excel_bulk_orders.tests.test_serializers
    python manage.py test excel_bulk_orders.tests.test_utils
    python manage.py test excel_bulk_orders.tests.test_admin
    python manage.py test excel_bulk_orders.tests.test_email_utils

Run specific test class:
    python manage.py test excel_bulk_orders.tests.test_models.ExcelBulkOrderModelTest

Run specific test method:
    python manage.py test excel_bulk_orders.tests.test_models.ExcelBulkOrderModelTest.test_reference_auto_generation_format

Run with coverage:
    coverage run --source='excel_bulk_orders' manage.py test excel_bulk_orders
    coverage report
    coverage html

BEST PRACTICES:
===============

When adding new features:
1. Write tests FIRST (TDD approach)
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
3. Test file upload security
4. Test webhook signature verification
5. Test for SQL injection and XSS vulnerabilities
6. Test race conditions for payment operations
7. Test idempotency for critical operations
"""

# Import all test classes for easy access
from .test_models import (
    ExcelBulkOrderModelTest,
    ExcelCouponCodeModelTest,
    ExcelParticipantModelTest,
)

from .test_serializers import (
    ExcelBulkOrderCreateSerializerTest,
    ExcelBulkOrderListSerializerTest,
    ExcelBulkOrderDetailSerializerTest,
    ExcelParticipantSerializerTest,
    ExcelUploadSerializerTest,
    ValidationErrorSerializerTest,
)

from .test_views import (
    ExcelBulkOrderViewSetTest,
    ExcelUploadActionTest,
    ExcelValidateActionTest,
    ExcelInitializePaymentActionTest,
    ExcelVerifyPaymentActionTest,
    ExcelParticipantViewSetTest,
    ExcelBulkOrderWebhookTest,
    SecurityAndEdgeCaseTests,
)

from .test_utils import (
    GenerateExcelCouponCodesTest,
    GenerateExcelTemplateTest,
    ValidateExcelFileTest,
    CreateParticipantsFromExcelTest,
    GenerateParticipantsPDFTest,
    GenerateParticipantsWordTest,
    GenerateParticipantsExcelTest,
)

from .test_admin import (
    ExcelBulkOrderAdminTest,
    ExcelCouponCodeInlineTest,
    ExcelParticipantInlineTest,
)

from .test_email_utils import (
    SendBulkOrderConfirmationEmailTest,
)

__all__ = [
    # Models
    'ExcelBulkOrderModelTest',
    'ExcelCouponCodeModelTest',
    'ExcelParticipantModelTest',
    
    # Serializers
    'ExcelBulkOrderCreateSerializerTest',
    'ExcelBulkOrderListSerializerTest',
    'ExcelBulkOrderDetailSerializerTest',
    'ExcelParticipantSerializerTest',
    'ExcelUploadSerializerTest',
    'ValidationErrorSerializerTest',
    
    # Views
    'ExcelBulkOrderViewSetTest',
    'ExcelUploadActionTest',
    'ExcelValidateActionTest',
    'ExcelInitializePaymentActionTest',
    'ExcelVerifyPaymentActionTest',
    'ExcelParticipantViewSetTest',
    'ExcelBulkOrderWebhookTest',
    'SecurityAndEdgeCaseTests',
    
    # Utils
    'GenerateExcelCouponCodesTest',
    'GenerateExcelTemplateTest',
    'ValidateExcelFileTest',
    'CreateParticipantsFromExcelTest',
    'GenerateParticipantsPDFTest',
    'GenerateParticipantsWordTest',
    'GenerateParticipantsExcelTest',
    
    # Admin
    'ExcelBulkOrderAdminTest',
    'ExcelCouponCodeInlineTest',
    'ExcelParticipantInlineTest',
    
    # Email
    'SendBulkOrderConfirmationEmailTest',
]