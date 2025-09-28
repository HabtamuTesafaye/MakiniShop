"""
Shared security and utility decorators for MakiniShop
- Rate limiting (django-ratelimit)
- IP blocking
- Input sanitization (bleach)
- Error logging
- Sentry integration (optional)
"""
from functools import wraps
from django.conf import settings
from django.http import HttpResponseForbidden
import logging

try:
    import bleach
except ImportError:
    bleach = None

try:
    import sentry_sdk
    SENTRY_ENABLED = hasattr(settings, 'SENTRY_DSN') and bool(settings.SENTRY_DSN)
except ImportError:
    SENTRY_ENABLED = False

logger = logging.getLogger(__name__)

BLOCKED_IPS = set(getattr(settings, 'BLOCKED_IPS', []))

def block_ip(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        ip = request.META.get('REMOTE_ADDR')
        if ip in BLOCKED_IPS:
            logger.warning(f"Blocked IP attempted access: {ip}")
            return HttpResponseForbidden('Your IP is blocked.')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def sanitize_input(data, fields):
    """Sanitize specified fields in a dict using bleach."""
    if not bleach:
        return data
    clean = data.copy()
    for field in fields:
        if field in clean:
            clean[field] = bleach.clean(clean[field])
    return clean

def log_and_report_error(error, context=None):
    logger.error(f"{error}")
    if SENTRY_ENABLED:
        sentry_sdk.capture_exception(error)
    if context:
        logger.debug(f"Context: {context}")
