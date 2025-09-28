# settings.py: Add django-csp for Content Security Policy headers
# Install django-csp in your environment

INSTALLED_APPS = INSTALLED_APPS + [
    'csp',
]

MIDDLEWARE = [
    'csp.middleware.CSPMiddleware',
] + MIDDLEWARE

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': ("'self'", 'cdn.jsdelivr.net'),
        'style-src': ("'self'", 'fonts.googleapis.com'),
        'font-src': ("'self'", 'fonts.gstatic.com'),
        'img-src': ("'self'", 'data:'),
    }
}

