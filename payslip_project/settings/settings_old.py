# ══════════════════════════════════════════════════════════
#  SECURITY SETTINGS
#  Add/merge these into your payslip_project/settings/dev.py
#  For production, copy to prod.py and toggle the HTTPS flags
# ══════════════════════════════════════════════════════════

# ──────────────────────────────────────────
# 1. INSTALLED APPS  (add to your existing list)
# ──────────────────────────────────────────
INSTALLED_APPS = [
    # ... your existing apps ...
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'axes',          # ← ADD
    'payslip_app',
]


# ──────────────────────────────────────────
# 2. MIDDLEWARE  (order matters — axes MUST be last)
# ──────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',   # ← ADD — must be last
]


# ──────────────────────────────────────────
# 3. AUTHENTICATION BACKENDS  (axes needs its own backend)
# ──────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # ← ADD — must be first
    'django.contrib.auth.backends.ModelBackend',
]


# ──────────────────────────────────────────
# 4. DJANGO-AXES CONFIGURATION
# ──────────────────────────────────────────

# Lock account after 5 failed attempts
AXES_FAILURE_LIMIT = 5

# Lock by both IP address and username (most secure)
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']

# How long the lockout lasts (30 minutes)
from datetime import timedelta
AXES_COOLOFF_TIME = timedelta(minutes=30)

# Show a clear message when locked out
AXES_LOCKOUT_TEMPLATE = 'payslip_app/lockout.html'

# Reset failure count on successful login
AXES_RESET_ON_SUCCESS = True

# Don't lock out staff from Django admin if you use it
AXES_NEVER_LOCKOUT_WHITELIST = False


# Write to database (default) — gives you a queryable access log
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'


# ──────────────────────────────────────────
# 5. DJANGO-RATELIMIT CONFIGURATION
# ──────────────────────────────────────────

# Use cache for rate limiting counters
RATELIMIT_USE_CACHE = 'default'

# Return 429 instead of raising exception
# (we handle this with handler429 in urls.py)
RATELIMIT_FAIL_OPEN = False


# ──────────────────────────────────────────
# 6. HTTPS & SECURITY HEADERS
#    Toggle HTTPS_ENABLED = True when deploying
# ──────────────────────────────────────────

HTTPS_ENABLED = False   # ← Set to True in production

# HTTPS redirect
SECURE_SSL_REDIRECT = HTTPS_ENABLED

# HSTS — tells browsers to always use HTTPS
# Start with a short value (300s), increase to 31536000 once confirmed working
SECURE_HSTS_SECONDS = 300 if HTTPS_ENABLED else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = HTTPS_ENABLED
SECURE_HSTS_PRELOAD = False   # Only enable after you're confident

# Secure cookies — only sent over HTTPS
SESSION_COOKIE_SECURE = HTTPS_ENABLED
CSRF_COOKIE_SECURE    = HTTPS_ENABLED

# Already good in your settings — keeping them:
SESSION_COOKIE_HTTPONLY = True      # JS cannot read session cookie
CSRF_COOKIE_HTTPONLY    = True      # JS cannot read CSRF cookie
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE    = 'Lax'

# Session expires in 30 minutes of inactivity (already set)
SESSION_COOKIE_AGE          = 1800
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST  = True

# Prevent browsers guessing content type
SECURE_CONTENT_TYPE_NOSNIFF = True

# Clickjacking protection (already set to SAMEORIGIN — keep it)
X_FRAME_OPTIONS = 'SAMEORIGIN'

# Referrer policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Cross-origin opener policy
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'


# ──────────────────────────────────────────
# 7. CACHE CONFIGURATION
#    Axes and ratelimit both use Django cache
#    Your existing LocMemCache is fine for dev
#    Use Redis in production
# ──────────────────────────────────────────

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'payslip-rate-limit',
    }
    # Production — swap to:
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    #     'LOCATION': 'redis://127.0.0.1:6379/1',
    # }
}