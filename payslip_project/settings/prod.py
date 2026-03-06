import os
from pathlib import Path
from datetime import timedelta
import dj_database_url

# ─────────────────────────────────────────
# BASE DIRECTORY
# ─────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────
# CORE
# ─────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-secret-key")

DEBUG = False

ALLOWED_HOSTS = [
    "mof-payslip-portal.onrender.com",
    ".onrender.com",
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = [
    "https://mof-payslip-portal.onrender.com"
]

ADMIN_URL = os.environ.get("ADMIN_URL", "secure-admin/")

# ─────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
    "two_factor",
    "axes",
    "anymail",
    "payslip_app",
]

# ─────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_otp.middleware.OTPMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
]

# ─────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# ─────────────────────────────────────────
# DATABASES
# ─────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'), conn_max_age=600),
    'mock_payslips': dj_database_url.config(default=os.environ.get('MOCK_PAYSLIPS_URL'), conn_max_age=600),
}
DATABASE_ROUTERS = ["payslip_app.db_routers.PayslipRouter"]

# ─────────────────────────────────────────
# CACHE (REDIS)
# ─────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL"),
    }
}

# ─────────────────────────────────────────
# EMAIL (MAILGUN)
# ─────────────────────────────────────────
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Payslip Portal <no-reply@example.com>",
)

ANYMAIL = {
    "MAILGUN_API_KEY": os.environ.get("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": os.environ.get("MAILGUN_DOMAIN"),
}

# ─────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ─────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────
TEMPLATES = [
{
"BACKEND": "django.template.backends.django.DjangoTemplates",
"DIRS": [BASE_DIR / "templates"],
"APP_DIRS": True,
"OPTIONS": {
"context_processors": [
"django.template.context_processors.debug",
"django.template.context_processors.request",
"django.contrib.auth.context_processors.auth",
"django.contrib.messages.context_processors.messages",
"django.template.context_processors.static",
],
},
}
]

ROOT_URLCONF = "payslip_project.urls"
WSGI_APPLICATION = "payslip_project.wsgi.application"

# ─────────────────────────────────────────
# SESSION & CSRF
# ─────────────────────────────────────────
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Strict"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Strict"

SESSION_COOKIE_AGE = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ─────────────────────────────────────────
# SECURITY HEADERS
# ─────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

X_FRAME_OPTIONS = "SAMEORIGIN"

# ─────────────────────────────────────────
# DJANGO AXES (Login protection)
# ─────────────────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=30)
AXES_RESET_ON_SUCCESS = True

# ─────────────────────────────────────────
# RATE LIMITING
# ─────────────────────────────────────────
RATELIMIT_USE_CACHE = "default"
RATELIMIT_FAIL_OPEN = False

# ─────────────────────────────────────────
# CELERY
# ─────────────────────────────────────────
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL")

CELERY_TASK_ACKS_LATE = True
CELERY_TASK_TIME_LIMIT = 300

# ─────────────────────────────────────────
# DJANGO DEFAULTS
# ─────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"

USE_I18N = True
USE_TZ = True