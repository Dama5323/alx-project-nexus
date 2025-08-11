"""
Development settings for djacommerce backend project.
"""

from .base import *
from decouple import config
import dj_database_url

DEBUG = True

# Override database configuration for development
DATABASE_URL = config('DATABASE_URL', default=None)

if DATABASE_URL:
    # Use DATABASE_URL from .env (e.g., Neon DB or other cloud DB)
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
    }
else:
    # Fallback to Docker/local DB config
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='djacommerce'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='password'),
            'HOST': config('DB_HOST', default='db'),
            'PORT': config('DB_PORT', default='5432'),
        }
    }

# Uncomment to enable Django Debug Toolbar (optional)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email backend logs emails to console in development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all CORS origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable HTTPS redirect in development
SECURE_SSL_REDIRECT = False

# Simple cache backend for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Increase logging level to DEBUG for development
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
