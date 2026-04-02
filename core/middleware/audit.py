"""
Audit Log Middleware

Logs every API request with: user, method, path, status code, and response time.
Useful for security auditing and debugging in production.
"""

import time
import logging

logger = logging.getLogger('audit')


class AuditLogMiddleware:
    """
    Lightweight middleware that logs every request.
    Format: [METHOD] /path/ — user@email — 200 OK — 45ms
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.monotonic()

        response = self.get_response(request)

        duration_ms = int((time.monotonic() - start_time) * 1000)

        # Resolve user identity
        user = getattr(request, 'user', None)
        user_label = user.email if user and user.is_authenticated else 'anonymous'

        logger.info(
            "[%s] %s — %s — %d — %dms",
            request.method,
            request.path,
            user_label,
            response.status_code,
            duration_ms,
        )

        return response
