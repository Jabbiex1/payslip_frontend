from .base import *
import os
from datetime import timedelta

# ─────────────────────────────────────────
#  CORE
# ─────────────────────────────────────────
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '10.27.10.122', '192.168.100.162']

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://10.27.10.122:8000',
    'http://192.168.100.141:8000',
]

ADMIN_URL = 'admin/'

# ─────────────────────────────────────────
#  INSTALLED APPS
# ─────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'axes',
    'payslip_app',
]

# ─────────────────────────────────────────
#  MIDDLEWARE
# ─────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',  # must be last
]

# ─────────────────────────────────────────
#  AUTHENTICATION BACKENDS
# ─────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # must be first
    'django.contrib.auth.backends.ModelBackend',
]

# ─────────────────────────────────────────
#  DATABASE
# ─────────────────────────────────────────
DATABASE_ROUTERS = ['payslip_app.db_routers.PayslipRouter']

# ─────────────────────────────────────────
#  CACHE  (LocMemCache is fine for dev)
# ─────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'payslip-rate-limit',
    }
}

# ─────────────────────────────────────────
#  EMAIL  — prints to terminal in dev
# ─────────────────────────────────────────
EMAIL_BACKEND   = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'MoF Payslip Portal <no-reply@mof-portal.com>'

# ─────────────────────────────────────────
#  SESSION
# ─────────────────────────────────────────
SESSION_COOKIE_AGE           = 1800   # 30 minutes
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST   = True
SESSION_COOKIE_HTTPONLY      = True
SESSION_COOKIE_SECURE        = False  # HTTP allowed in dev
SESSION_COOKIE_SAMESITE      = 'Lax'

# ─────────────────────────────────────────
#  CSRF
# ─────────────────────────────────────────
CSRF_COOKIE_HTTPONLY  = True
CSRF_COOKIE_SECURE    = False  # HTTP allowed in dev
CSRF_COOKIE_SAMESITE  = 'Lax'

# ─────────────────────────────────────────
#  SECURITY HEADERS
# ─────────────────────────────────────────
SECURE_SSL_REDIRECT              = False
SECURE_HSTS_SECONDS              = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS   = False
SECURE_HSTS_PRELOAD              = False
SECURE_CONTENT_TYPE_NOSNIFF      = True
SECURE_REFERRER_POLICY           = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS                  = 'SAMEORIGIN'

# ─────────────────────────────────────────
#  DJANGO-AXES  (brute force protection)
# ─────────────────────────────────────────
AXES_FAILURE_LIMIT        = 5
AXES_LOCKOUT_PARAMETERS   = ['ip_address', 'username']
AXES_COOLOFF_TIME         = timedelta(minutes=30)
AXES_LOCKOUT_TEMPLATE     = 'payslip_app/lockout.html'
AXES_RESET_ON_SUCCESS     = True
AXES_HANDLER              = 'axes.handlers.database.AxesDatabaseHandler'
AXES_COOLOFF_MESSAGE      = 'Account locked: too many login attempts. Please try again later.'
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = True
AXES_ACCESS_FAILURE_LOG_PER_USER_LIMIT = 1000
AXES_ALLOWED_CORS_ORIGINS = '*'

# ─────────────────────────────────────────
#  DJANGO-RATELIMIT
# ─────────────────────────────────────────
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_FAIL_OPEN = False

# ─────────────────────────────────────────
#  CELERY
# ─────────────────────────────────────────
CELERY_BROKER_URL      = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND  = 'redis://localhost:6379/0'
CELERY_TASK_ACKS_LATE  = True
CELERY_TASK_TIME_LIMIT = 300

# Private media acceleration is disabled in local dev.
USE_X_ACCEL_REDIRECT = False
