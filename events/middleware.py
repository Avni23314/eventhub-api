
import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "%s %s - Status: %s - Duration: %.2f ms",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )

        return response