from .base import *
import os
from datetime import timedelta

# ─────────────────────────────────────────
#  CORE
# ─────────────────────────────────────────
DEBUG = False

ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']  # ← update when deploying

CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]

ADMIN_URL = 'x92k-secret-admin/'

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
#  CACHE  (Redis in production)
# ─────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# ─────────────────────────────────────────
#  EMAIL  — Mailgun SMTP in production
# ─────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.mailgun.org'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.environ.get('MAILGUN_SMTP_USER', 'postmaster@sandbox0148a5d214cf4fe291f8906e3a497559.mailgun.org')
EMAIL_HOST_PASSWORD = os.environ.get('MAILGUN_API_KEY', '')
DEFAULT_FROM_EMAIL  = 'MoF Payslip Portal <no-reply@sandbox0148a5d214cf4fe291f8906e3a497559.mailgun.org>'

# ─────────────────────────────────────────
#  SESSION
# ─────────────────────────────────────────
SESSION_COOKIE_AGE              = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST      = True
SESSION_COOKIE_HTTPONLY         = True
SESSION_COOKIE_SECURE           = True   # HTTPS only
SESSION_COOKIE_SAMESITE         = 'Lax'

# ─────────────────────────────────────────
#  CSRF
# ─────────────────────────────────────────
CSRF_COOKIE_HTTPONLY  = True
CSRF_COOKIE_SECURE    = True   # HTTPS only
CSRF_COOKIE_SAMESITE  = 'Lax'

# ─────────────────────────────────────────
#  SECURITY HEADERS
# ─────────────────────────────────────────
SECURE_SSL_REDIRECT               = True
SECURE_HSTS_SECONDS               = 300        # increase to 31536000 after HTTPS confirmed working
SECURE_HSTS_INCLUDE_SUBDOMAINS    = True
SECURE_HSTS_PRELOAD               = False      # enable only after HSTS is stable
SECURE_CONTENT_TYPE_NOSNIFF       = True
SECURE_REFERRER_POLICY            = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS                   = 'SAMEORIGIN'

# ─────────────────────────────────────────
#  DJANGO-AXES
# ─────────────────────────────────────────
AXES_FAILURE_LIMIT        = 5
AXES_LOCKOUT_PARAMETERS   = ['ip_address', 'username']
AXES_COOLOFF_TIME         = timedelta(minutes=30)
AXES_LOCKOUT_TEMPLATE     = 'payslip_app/lockout.html'
AXES_RESET_ON_SUCCESS     = True
AXES_HANDLER              = 'axes.handlers.database.AxesDatabaseHandler'
AXES_COOLOFF_MESSAGE      = 'Account locked: too many login attempts. Please try again later.'
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = True
AXES_ACCESS_FAILURE_LOG_PER_USER_LIMIT        = 1000

# ─────────────────────────────────────────
#  DJANGO-RATELIMIT
# ─────────────────────────────────────────
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_FAIL_OPEN = False

# ─────────────────────────────────────────
#  CELERY
# ─────────────────────────────────────────
CELERY_BROKER_URL      = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND  = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_TASK_ACKS_LATE  = True
CELERY_TASK_TIME_LIMIT = 300

# Use Nginx internal redirect for private media downloads.
USE_X_ACCEL_REDIRECT = True
X_ACCEL_REDIRECT_PREFIX = "/protected-media"
