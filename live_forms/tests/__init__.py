# live_forms/tests/__init__.py
"""
Comprehensive test suite for live_forms app.

TEST MODULES:
=============

1. test_models.py  (3 test classes, 80+ tests)
   - LiveFormLinkModelTest     : slug generation, expiry logic, is_open guards,
                                 name normalisation, shareable URL, Meta
   - LiveFormEntryModelTest    : serial_number auto-increment, name normalisation,
                                 social-proof counter update, __str__, Meta
   - ConcurrentEntryModelTest  : race-condition safety for serial_number

2. test_serializers.py  (4 test classes, 60+ tests)
   - LiveFormLinkSummarySerializerTest : read-only fields, social_proof block,
                                        seconds_remaining, is_open/is_expired
   - LiveFormLinkSerializerTest        : create validation, expires_at guard,
                                        read-only enforcement
   - LiveFormEntrySerializerTest       : custom_name conditional logic,
                                        form-open guards, to_representation
   - LiveFormEntryPublicSerializerTest : lean feed serializer, custom_name strip

3. test_views.py  (5 test classes, 80+ tests)
   - SheetViewTest             : Django template view, 404, view_count bump
   - LiveFormLinkViewSetTest   : CRUD, permission matrix, queryset scoping,
                                 submit, live_feed (?since=), admin_entries,
                                 download_pdf/word/excel
   - LiveFormEntryViewSetTest  : list (admin), retrieve (public), delete (admin)
   - PublicSubmitFlowTest      : end-to-end submit against closed/expired/full forms
   - LiveFeedPollingTest       : ?since= filtering, server_time, social_proof block

4. test_utils.py  (3 test classes, 40+ tests)
   - GetLiveFormWithEntriesTest  : slug vs instance, prefetch, 404
   - GenerateLiveFormPDFTest     : content-type, filename, ImportError handling
   - GenerateLiveFormWordTest    : docx content-type, custom_branding flag
   - GenerateLiveFormExcelTest   : xlsx content-type, row counts

5. test_admin.py  (5 test classes, 50+ tests)
   - LiveFormEntryAdminTest      : custom_name_display, live_form_link, read-only
   - LiveFormLinkAdminTest       : list display, shareable_link_display, actions,
                                   download PDF/Word/Excel actions, copy_link_action
   - IsExpiredFilterTest         : yes/no filtering by expires_at
   - HasSubmissionsFilterTest    : yes/no filtering by entry_count
   - LiveFormEntryInlineTest     : add permission denied, readonly fields

COVERAGE TARGETS: 95%+
"""