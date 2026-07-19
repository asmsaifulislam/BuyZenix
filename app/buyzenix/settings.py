import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required. Generate one with: python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\"")

DEBUG = os.getenv("DEBUG", "0") == "1"

# Local development mode: run on localhost without Postgres/Redis/Docker.
# Set RUN_LOCAL=1 in your shell (or .env) to use SQLite + in-memory cache.
RUN_LOCAL = os.getenv("RUN_LOCAL", "0") == "1"

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

CSRF_TRUSTED_ORIGINS = [
    "https://buyzenix.com",
    "https://www.buyzenix.com",
    "http://buyzenix.com",
    "http://www.buyzenix.com",
]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django_celery_results",
    "rest_framework",
    "core",
    "accounts",
    "cart",
    "orders",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "dashboard.tracking.PageViewTracker",
    "dashboard.audit.AuditLogMiddleware",
]

ROOT_URLCONF = "buyzenix.urls"

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
                "cart.context_processors.cart_counts",
                "core.context_processors.currency_context",
                "core.context_processors.nav_categories",
                "dashboard.analytics_context.analytics_context",
            ],
        },
    },
]

WSGI_APPLICATION = "buyzenix.wsgi.application"

if RUN_LOCAL:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "buyzenix"),
            "USER": os.getenv("POSTGRES_USER", "buyzenix"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

if RUN_LOCAL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}/1",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

CART_SESSION_ID = "buyzenix_cart"

# Multi-currency support for the Bangladesh market. Prices are stored in the
# base currency (BDT) and converted for display using these static rates.
# BDT is the default display currency.
CURRENCIES = {
    "BDT": {"symbol": "৳", "rate": 1.0, "name": "Bangladeshi Taka"},
    "USD": {"symbol": "$", "rate": 0.0091, "name": "US Dollar"},
    "CNY": {"symbol": "¥", "rate": 0.065, "name": "Chinese Yuan"},
}
DEFAULT_CURRENCY = "BDT"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom Admin Site
ADMIN_SITE = "buyzenix.admin_site.BuyZenixAdminSite"

# ─── Analytics & Tracking (configured via API Control Panel) ───
# These are fallback defaults; real values come from APIKey model
ANALYTICS_CONFIG = {
    "google_analytics_id": "",
    "matomo_url": "",
    "matomo_site_id": "",
    "smartlook_key": "",
}

# ─── GDPR / Privacy Settings ───
GDPR_COOKIE_CONSENT_REQUIRED = True
GDPR_ANONYMIZE_IP = True
GDPR_DATA_RETENTION_DAYS = 365
GDPR_CONTACT_EMAIL = "privacy@buyzenix.com"
GDPR_DPO_EMAIL = "dpo@buyzenix.com"

# Celery
if RUN_LOCAL:
    CELERY_BROKER_URL = "memory://localhost/"
else:
    CELERY_BROKER_URL = f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}/0"
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Email
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@buyzenix.com")
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
