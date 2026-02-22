# jmw/middleware.py
"""
Admin Security Middleware

Implements IP-based access control for the Django admin panel.
In production, only whitelisted IPs can access /i_must_win/ (admin).
"""

from django.conf import settings
from django.http import HttpResponseForbidden
import logging

logger = logging.getLogger(__name__)


class AdminIPWhitelistMiddleware:
    """
    Middleware that restricts admin access to whitelisted IP addresses.

    Only active in production (DEBUG=False).
    Blocks any non-whitelisted IP from accessing the admin URL.

    Configuration in settings.py:
        ADMIN_IP_WHITELIST = ['your.ip.address.here', '192.168.1.1']
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only enforce in production
        if not settings.DEBUG:
            # Get admin URL path (default is 'admin/', but we use 'i_must_win/')
            admin_path = getattr(settings, 'ADMIN_URL_PATH', 'i_must_win/')

            # Check if this is an admin request
            if request.path.startswith(f'/{admin_path}'):
                client_ip = self.get_client_ip(request)
                whitelist = getattr(settings, 'ADMIN_IP_WHITELIST', [])

                if client_ip not in whitelist:
                    logger.warning(
                        f"Blocked admin access attempt from IP: {client_ip} "
                        f"to path: {request.path}"
                    )
                    return HttpResponseForbidden(
                        b"<h1>403 Forbidden</h1>"
                        b"<p>You don't have permission to access this resource.</p>"
                    )

                logger.info(f"Admin access granted to IP: {client_ip}")

        return self.get_response(request)

    def get_client_ip(self, request):
        """
        Get the client's real IP address.

        Handles proxy headers (X-Forwarded-For) for deployments
        behind load balancers like Render, Heroku, etc.
        """
        # Check for proxy headers first
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs; the first is the client
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Fall back to REMOTE_ADDR
            ip = request.META.get('REMOTE_ADDR', '')

        return ip
