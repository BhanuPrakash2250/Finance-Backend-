"""
Custom exception handler for consistent, meaningful error responses.

All errors follow the envelope:
{
    "success": false,
    "error": {
        "code": "validation_error",
        "message": "Human-readable summary",
        "details": { ... }   # field-level errors or extra context
    }
}
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Wrap DRF's default exception handler output in our standard envelope.
    Also logs server errors for monitoring.
    """
    # Let DRF handle the exception first
    response = exception_handler(exc, context)

    if response is not None:
        # Map HTTP status to a short error code
        error_code = _status_to_code(response.status_code)

        # DRF wraps field errors in a dict; flatten for readability
        details = response.data
        message = _extract_message(details, response.status_code)

        response.data = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message,
                'details': details,
            }
        }
    else:
        # Unhandled server exception — return 500
        logger.exception("Unhandled exception: %s", exc)
        response = Response(
            {
                'success': False,
                'error': {
                    'code': 'server_error',
                    'message': 'An unexpected error occurred. Please try again later.',
                    'details': {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response


def _status_to_code(status_code: int) -> str:
    mapping = {
        400: 'validation_error',
        401: 'authentication_failed',
        403: 'permission_denied',
        404: 'not_found',
        405: 'method_not_allowed',
        409: 'conflict',
        429: 'rate_limit_exceeded',
        500: 'server_error',
    }
    return mapping.get(status_code, 'error')


def _extract_message(details, status_code: int) -> str:
    """Produce a human-readable summary from DRF error details."""
    defaults = {
        400: 'Invalid request data. Please check the details and try again.',
        401: 'Authentication credentials were not provided or are invalid.',
        403: 'You do not have permission to perform this action.',
        404: 'The requested resource was not found.',
        405: 'This HTTP method is not allowed for this endpoint.',
    }
    if isinstance(details, dict) and 'detail' in details:
        return str(details['detail'])
    return defaults.get(status_code, 'An error occurred.')
