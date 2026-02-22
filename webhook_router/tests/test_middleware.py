# jmw/tests/test_middleware.py
"""
Comprehensive tests for jmw/middleware.py

Coverage:
=========
✅ AdminIPWhitelistMiddleware
   - DEBUG=True  → middleware is completely skipped (always allows through)
   - DEBUG=False → enforcement is active

   IP Detection:
   ✅ get_client_ip — REMOTE_ADDR (direct connection)
   ✅ get_client_ip — X-Forwarded-For single IP (proxy)
   ✅ get_client_ip — X-Forwarded-For multiple IPs (chain of proxies)
   ✅ get_client_ip — X-Forwarded-For with whitespace padding
   ✅ get_client_ip — missing REMOTE_ADDR returns empty string

   Admin path enforcement (DEBUG=False):
   ✅ Whitelisted IP → 200 (access granted)
   ✅ Non-whitelisted IP → 403 Forbidden
   ✅ Empty whitelist → 403 for all IPs
   ✅ Non-admin path → always allowed, regardless of IP
   ✅ Non-admin path, non-whitelisted IP → still allowed
   ✅ Custom ADMIN_URL_PATH setting respected
   ✅ Default ADMIN_URL_PATH used when setting is absent
   ✅ Admin sub-paths blocked (e.g. /i_must_win/auth/user/)
   ✅ Path that merely contains admin string but isn't admin → allowed
   ✅ 403 response body contains expected content
   ✅ 403 response is HttpResponseForbidden (status 403)

   Logging:
   ✅ Blocked access → warning logged with IP and path
   ✅ Granted access → info logged with IP

   Middleware contract:
   ✅ get_response is called when access is granted
   ✅ get_response is NOT called when access is blocked
   ✅ Response from get_response is returned unchanged

   Edge cases:
   ✅ IPv6 address in whitelist
   ✅ Localhost variants (127.0.0.1, ::1)
   ✅ Whitelist with extra whitespace around IPs (env.list artefact)
   ✅ Multiple IPs in whitelist — correct one matches
   ✅ Multiple IPs in whitelist — wrong IP still blocked
"""

from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse, HttpResponseForbidden
from unittest.mock import Mock, patch, call
import logging

from jmw.middleware import AdminIPWhitelistMiddleware


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_middleware(get_response=None):
    """Instantiate the middleware with a mock get_response."""
    if get_response is None:
        get_response = Mock(return_value=HttpResponse("OK", status=200))
    return AdminIPWhitelistMiddleware(get_response), get_response


def make_request(factory, path='/', remote_addr='1.2.3.4', forwarded_for=None):
    """Build a GET request with optional proxy headers."""
    request = factory.get(path, REMOTE_ADDR=remote_addr)
    if forwarded_for:
        request.META['HTTP_X_FORWARDED_FOR'] = forwarded_for
    return request


ADMIN_PATH = '/i_must_win/'
NON_ADMIN_PATH = '/api/products/'
BLOCKED_IP = '9.9.9.9'
ALLOWED_IP = '102.88.34.56'
WHITELIST = [ALLOWED_IP, '41.184.123.45']


# ===========================================================================
# 1. INITIALISATION
# ===========================================================================

class TestMiddlewareInit(TestCase):
    """Middleware stores get_response correctly."""

    def test_get_response_stored(self):
        mock_response = Mock(return_value=HttpResponse())
        mw = AdminIPWhitelistMiddleware(mock_response)
        self.assertIs(mw.get_response, mock_response)


# ===========================================================================
# 2. DEBUG MODE — middleware is a no-op
# ===========================================================================

class TestDebugModeBypass(TestCase):
    """When DEBUG=True the middleware never blocks anything."""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(DEBUG=True, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_admin_path_blocked_ip_allowed_in_debug(self):
        """Non-whitelisted IP can hit admin when DEBUG=True."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=BLOCKED_IP)

        response = mw(request)

        get_response.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=True, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_non_admin_path_allowed_in_debug(self):
        """Non-admin path is always allowed in debug mode."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, NON_ADMIN_PATH, remote_addr=BLOCKED_IP)

        response = mw(request)

        get_response.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)


# ===========================================================================
# 3. PRODUCTION MODE — enforcement active
# ===========================================================================

class TestProductionEnforcement(TestCase):
    """Core allow/block logic when DEBUG=False."""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_whitelisted_ip_granted_access(self):
        """Whitelisted IP receives a 200 from get_response."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=ALLOWED_IP)

        response = mw(request)

        get_response.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_non_whitelisted_ip_blocked(self):
        """Non-whitelisted IP receives 403."""
        mw, _ = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=BLOCKED_IP)

        response = mw(request)

        self.assertIsInstance(response, HttpResponseForbidden)
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_get_response_not_called_when_blocked(self):
        """get_response must not be invoked for blocked requests."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=BLOCKED_IP)

        mw(request)

        get_response.assert_not_called()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_empty_whitelist_blocks_everyone(self):
        """Empty whitelist denies access to all IPs."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=ALLOWED_IP)

        response = mw(request)

        self.assertEqual(response.status_code, 403)
        get_response.assert_not_called()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_non_admin_path_always_allowed(self):
        """Non-admin paths are passed through regardless of IP."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, NON_ADMIN_PATH, remote_addr=BLOCKED_IP)

        response = mw(request)

        get_response.assert_called_once_with(request)
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_non_admin_path_not_blocked_even_with_empty_whitelist(self):
        """/api/ paths are never blocked, even with an empty whitelist."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, '/api/bulk_orders/', remote_addr=BLOCKED_IP)

        response = mw(request)

        get_response.assert_called_once_with(request)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_admin_sub_path_is_blocked(self):
        """Sub-paths under admin (e.g. /i_must_win/auth/user/) are also blocked."""
        mw, get_response = make_middleware()
        request = make_request(
            self.factory,
            '/i_must_win/auth/user/1/change/',
            remote_addr=BLOCKED_IP
        )

        response = mw(request)

        self.assertEqual(response.status_code, 403)
        get_response.assert_not_called()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_admin_sub_path_whitelisted_ip_passes(self):
        """Sub-paths under admin are accessible for whitelisted IPs."""
        mw, get_response = make_middleware()
        request = make_request(
            self.factory,
            '/i_must_win/auth/user/1/change/',
            remote_addr=ALLOWED_IP
        )

        response = mw(request)

        get_response.assert_called_once_with(request)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_path_containing_admin_string_but_not_admin(self):
        """A path like /api/i_must_win_report/ should NOT be treated as admin."""
        mw, get_response = make_middleware()
        # Starts with /api/, not /i_must_win/
        request = make_request(self.factory, '/api/i_must_win_report/', remote_addr=BLOCKED_IP)

        response = mw(request)

        # Should pass through because it doesn't start with /i_must_win/
        get_response.assert_called_once_with(request)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_get_response_return_value_is_returned(self):
        """The response object from get_response is returned unchanged."""
        expected = HttpResponse("Exact response", status=201)
        mw, get_response = make_middleware(get_response=Mock(return_value=expected))
        request = make_request(self.factory, NON_ADMIN_PATH, remote_addr=BLOCKED_IP)

        response = mw(request)

        self.assertIs(response, expected)


# ===========================================================================
# 4. CUSTOM ADMIN URL PATH
# ===========================================================================

class TestCustomAdminUrlPath(TestCase):
    """ADMIN_URL_PATH setting is respected."""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='secret_panel/')
    def test_custom_path_is_blocked(self):
        """Custom admin path is blocked for non-whitelisted IPs."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, '/secret_panel/', remote_addr=BLOCKED_IP)

        response = mw(request)

        self.assertEqual(response.status_code, 403)
        get_response.assert_not_called()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='secret_panel/')
    def test_default_admin_path_not_blocked_with_custom_setting(self):
        """The old /i_must_win/ path is not blocked when custom path is configured."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, '/i_must_win/', remote_addr=BLOCKED_IP)

        response = mw(request)

        # /i_must_win/ is no longer the admin path, so it passes through
        get_response.assert_called_once_with(request)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[])
    def test_default_admin_url_path_used_when_setting_absent(self):
        """Falls back to 'i_must_win/' when ADMIN_URL_PATH is not configured."""
        # Temporarily remove ADMIN_URL_PATH from settings
        from django.conf import settings as dj_settings
        if hasattr(dj_settings, 'ADMIN_URL_PATH'):
            original = dj_settings.ADMIN_URL_PATH
            del dj_settings.ADMIN_URL_PATH
        else:
            original = None

        try:
            mw, get_response = make_middleware()
            request = make_request(self.factory, '/i_must_win/', remote_addr=BLOCKED_IP)
            response = mw(request)
            self.assertEqual(response.status_code, 403)
        finally:
            if original is not None:
                dj_settings.ADMIN_URL_PATH = original


# ===========================================================================
# 5. IP DETECTION — get_client_ip
# ===========================================================================

class TestGetClientIp(TestCase):
    """Unit tests for the IP extraction helper."""

    def setUp(self):
        self.factory = RequestFactory()
        # get_response doesn't matter here; we call get_client_ip directly
        self.mw, _ = make_middleware()

    def test_remote_addr_used_when_no_proxy_header(self):
        request = make_request(self.factory, remote_addr='5.6.7.8')
        self.assertEqual(self.mw.get_client_ip(request), '5.6.7.8')

    def test_x_forwarded_for_single_ip(self):
        request = make_request(self.factory, forwarded_for='10.0.0.1')
        self.assertEqual(self.mw.get_client_ip(request), '10.0.0.1')

    def test_x_forwarded_for_multiple_ips_returns_first(self):
        """First IP in X-Forwarded-For is the originating client."""
        request = make_request(
            self.factory,
            forwarded_for='203.0.113.5, 70.41.3.18, 150.172.238.178'
        )
        self.assertEqual(self.mw.get_client_ip(request), '203.0.113.5')

    def test_x_forwarded_for_with_whitespace_padding(self):
        """Leading/trailing whitespace around IPs is stripped."""
        request = make_request(
            self.factory,
            forwarded_for='  203.0.113.5  , 10.0.0.1'
        )
        self.assertEqual(self.mw.get_client_ip(request), '203.0.113.5')

    def test_x_forwarded_for_takes_priority_over_remote_addr(self):
        """X-Forwarded-For overrides REMOTE_ADDR."""
        request = make_request(
            self.factory,
            remote_addr='192.168.1.1',
            forwarded_for='203.0.113.99'
        )
        self.assertEqual(self.mw.get_client_ip(request), '203.0.113.99')

    def test_missing_remote_addr_returns_empty_string(self):
        """Gracefully handles missing REMOTE_ADDR."""
        request = self.factory.get('/')
        request.META.pop('REMOTE_ADDR', None)
        request.META.pop('HTTP_X_FORWARDED_FOR', None)
        self.assertEqual(self.mw.get_client_ip(request), '')


# ===========================================================================
# 6. 403 RESPONSE CONTENT
# ===========================================================================

class TestForbiddenResponseContent(TestCase):
    """The 403 response body is meaningful."""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_403_response_contains_forbidden_heading(self):
        mw, _ = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=BLOCKED_IP)

        response = mw(request)

        self.assertIn(b'403', response.content)
        self.assertIn(b'Forbidden', response.content)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_403_response_contains_permission_message(self):
        mw, _ = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=BLOCKED_IP)

        response = mw(request)

        self.assertIn(b"permission", response.content.lower())

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_403_response_is_correct_type(self):
        mw, _ = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=BLOCKED_IP)

        response = mw(request)

        self.assertIsInstance(response, HttpResponseForbidden)


# ===========================================================================
# 7. LOGGING
# ===========================================================================

class TestLogging(TestCase):
    """Correct log messages are emitted."""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_blocked_access_logs_warning(self):
        mw, _ = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=BLOCKED_IP)

        with self.assertLogs('jmw.middleware', level='WARNING') as cm:
            mw(request)

        self.assertTrue(
            any('Blocked' in msg and BLOCKED_IP in msg for msg in cm.output),
            msg=f"Expected a WARNING log containing 'Blocked' and '{BLOCKED_IP}'. Got: {cm.output}"
        )

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_granted_access_logs_info(self):
        mw, _ = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=ALLOWED_IP)

        with self.assertLogs('jmw.middleware', level='INFO') as cm:
            mw(request)

        self.assertTrue(
            any('granted' in msg.lower() and ALLOWED_IP in msg for msg in cm.output),
            msg=f"Expected an INFO log containing 'granted' and '{ALLOWED_IP}'. Got: {cm.output}"
        )

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_blocked_log_includes_path(self):
        mw, _ = make_middleware()
        request = make_request(self.factory, '/i_must_win/auth/user/', remote_addr=BLOCKED_IP)

        with self.assertLogs('jmw.middleware', level='WARNING') as cm:
            mw(request)

        self.assertTrue(
            any('/i_must_win/auth/user/' in msg for msg in cm.output),
            msg=f"Expected path in log. Got: {cm.output}"
        )

    @override_settings(DEBUG=True, ADMIN_IP_WHITELIST=[], ADMIN_URL_PATH='i_must_win/')
    def test_no_log_in_debug_mode(self):
        """No middleware logs are emitted in debug mode."""
        mw, _ = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr=BLOCKED_IP)

        # assertLogs raises AssertionError if no logs are emitted — that's what we want
        with self.assertRaises(AssertionError):
            with self.assertLogs('jmw.middleware', level='DEBUG'):
                mw(request)


# ===========================================================================
# 8. EDGE CASES
# ===========================================================================

class TestEdgeCases(TestCase):
    """Edge cases that could trip up production deployments."""

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=['::1'], ADMIN_URL_PATH='i_must_win/')
    def test_ipv6_localhost_whitelisted(self):
        """IPv6 addresses can be whitelisted."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr='::1')

        response = mw(request)

        get_response.assert_called_once_with(request)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=['127.0.0.1'], ADMIN_URL_PATH='i_must_win/')
    def test_ipv4_localhost_whitelisted(self):
        """127.0.0.1 can be whitelisted (useful for local production testing)."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr='127.0.0.1')

        response = mw(request)

        get_response.assert_called_once_with(request)

    @override_settings(
        DEBUG=False,
        ADMIN_IP_WHITELIST=[ALLOWED_IP, '41.184.123.45'],
        ADMIN_URL_PATH='i_must_win/'
    )
    def test_second_ip_in_whitelist_also_granted(self):
        """All IPs in the whitelist are granted, not just the first."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr='41.184.123.45')

        response = mw(request)

        get_response.assert_called_once_with(request)

    @override_settings(
        DEBUG=False,
        ADMIN_IP_WHITELIST=[ALLOWED_IP, '41.184.123.45'],
        ADMIN_URL_PATH='i_must_win/'
    )
    def test_ip_not_in_multi_ip_whitelist_blocked(self):
        """An IP not in a multi-entry whitelist is still blocked."""
        mw, get_response = make_middleware()
        request = make_request(self.factory, ADMIN_PATH, remote_addr='8.8.8.8')

        response = mw(request)

        self.assertEqual(response.status_code, 403)
        get_response.assert_not_called()

    @override_settings(
        DEBUG=False,
        ADMIN_IP_WHITELIST=['  102.88.34.56  '],   # env.list can leave whitespace
        ADMIN_URL_PATH='i_must_win/'
    )
    def test_whitelist_ip_with_surrounding_whitespace(self):
        """
        Note: env.list() strips whitespace, but if someone adds IPs manually
        with spaces, the middleware should still handle the comparison correctly.
        This test documents the current behaviour — exact string match.
        """
        mw, get_response = make_middleware()
        # '102.88.34.56' (no spaces) against whitelist entry '  102.88.34.56  ' (with spaces)
        request = make_request(self.factory, ADMIN_PATH, remote_addr='102.88.34.56')

        response = mw(request)

        # Current middleware does an exact `in` check — spaces would cause a miss.
        # This test documents that behaviour. If you strip whitelist entries in
        # get_client_ip or __call__, update the assertion to expect 200.
        # As-is the middleware does NOT strip whitelist entries.
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_proxied_whitelisted_ip_via_forwarded_for(self):
        """Whitelisted IP coming through a proxy (X-Forwarded-For) is granted."""
        mw, get_response = make_middleware()
        # The load balancer is 10.0.0.1, but the real client is ALLOWED_IP
        request = make_request(
            self.factory,
            ADMIN_PATH,
            remote_addr='10.0.0.1',
            forwarded_for=f'{ALLOWED_IP}, 10.0.0.1'
        )

        response = mw(request)

        get_response.assert_called_once_with(request)

    @override_settings(DEBUG=False, ADMIN_IP_WHITELIST=WHITELIST, ADMIN_URL_PATH='i_must_win/')
    def test_proxied_blocked_ip_via_forwarded_for(self):
        """Non-whitelisted IP spoofing via X-Forwarded-For is still blocked."""
        mw, get_response = make_middleware()
        request = make_request(
            self.factory,
            ADMIN_PATH,
            remote_addr='10.0.0.1',
            forwarded_for=f'{BLOCKED_IP}, 10.0.0.1'
        )

        response = mw(request)

        self.assertEqual(response.status_code, 403)
        get_response.assert_not_called()