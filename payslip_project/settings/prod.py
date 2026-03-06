import os
import dj_database_url
from datetime import timedelta

# ─────────────────────────────────────────
#  CORE
# ─────────────────────────────────────────
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = [os.environ.get('RENDER_EXTERNAL_HOSTNAME', ''), 'localhost']
CSRF_TRUSTED_ORIGINS = [f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')}"]
ADMIN_URL = os.environ.get('ADMIN_URL', 'x92k-secret-admin/')
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    'corsheaders',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'two_factor',
    'axes',
    'payslip_app',
    'anymail',
]

# ─────────────────────────────────────────
#  MIDDLEWARE
# ─────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

# ─────────────────────────────────────────
#  AUTHENTICATION BACKENDS
# ─────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# ─────────────────────────────────────────
#  DATABASES
# ─────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.parse(
        os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    ),
    'mock_payslips': dj_database_url.parse(
        os.environ.get('MOCK_PAYSLIPS_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    ),
}
DATABASE_ROUTERS = ['payslip_app.db_routers.PayslipRouter']

# ─────────────────────────────────────────
#  CACHE
# ─────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# ─────────────────────────────────────────
#  EMAIL
# ─────────────────────────────────────────
EMAIL_BACKEND  = 'anymail.backends.mailgun.EmailBackend'
DEFAULT_FROM_EMAIL = 'MoF Payslip Portal <no-reply@sandbox0148a5d214cf4fe291f8906e3a497559.mailgun.org>'
ANYMAIL = {
    'MAILGUN_API_KEY':       os.environ.get('MAILGUN_API_KEY'),
    'MAILGUN_SENDER_DOMAIN': os.environ.get('MAILGUN_DOMAIN'),
}

# ─────────────────────────────────────────
#  STATIC & MEDIA
# ─────────────────────────────────────────
STATIC_URL   = '/static/'
STATIC_ROOT  = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL    = '/media/'
MEDIA_ROOT   = os.path.join(BASE_DIR, 'media')

# ─────────────────────────────────────────
#  TEMPLATES
# ─────────────────────────────────────────
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'templates')],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'django.template.context_processors.static',
    ]},
}]

ROOT_URLCONF       = 'payslip_project.urls'
WSGI_APPLICATION   = 'payslip_project.wsgi.application'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE      = 'en-us'
TIME_ZONE          = 'UTC'
USE_I18N           = True
USE_TZ             = True

# ─────────────────────────────────────────
#  SESSION & CSRF
# ─────────────────────────────────────────
SESSION_COOKIE_AGE              = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST      = True
SESSION_COOKIE_HTTPONLY         = True
SESSION_COOKIE_SECURE           = True
SESSION_COOKIE_SAMESITE         = 'Lax'
CSRF_COOKIE_HTTPONLY             = True
CSRF_COOKIE_SECURE               = True
CSRF_COOKIE_SAMESITE             = 'Lax'

# ─────────────────────────────────────────
#  SECURITY HEADERS
# ─────────────────────────────────────────
SECURE_SSL_REDIRECT               = True
SECURE_PROXY_SSL_HEADER           = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS               = 300
SECURE_HSTS_INCLUDE_SUBDOMAINS    = True
SECURE_HSTS_PRELOAD               = False
SECURE_CONTENT_TYPE_NOSNIFF       = True
SECURE_REFERRER_POLICY            = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS                   = 'SAMEORIGIN'

# ─────────────────────────────────────────
#  AXES
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
#  RATELIMIT
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