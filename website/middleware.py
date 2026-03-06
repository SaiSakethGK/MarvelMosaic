"""
Request logging middleware.

Author: Sai Saketh Gooty Kase
"""

import logging
import time

logger = logging.getLogger(__name__)


class RequestLogMiddleware:
    """Log every request with method, path, status code, and elapsed time."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        elapsed_ms = (time.monotonic() - start) * 1000
        logger.info(
            "%s %s — %d (%.1f ms)",
            request.method,
            request.path,
            response.status_code,
            elapsed_ms,
        )
        return response
