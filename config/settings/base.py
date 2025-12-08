import os
from datetime import timedelta

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(path):
        return False
# import environ

# -----------------------------------------------------------------------------
# BASE PATHS
# -----------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))
# env = os.getenv("DEBUG", "False")

# env.read_env(os.path.join(BASE_DIR, ".env"))  # optional .env file


# -----------------------------------------------------------------------------
# CORE SETTINGS
# -----------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", default="unsafe-secret-key")
DEBUG = (os.getenv("DEBUG", "False"))
ALLOWED_HOSTS = ["*"]

# -----------------------------------------------------------------------------
# APPLICATIONS
# -----------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "django_prometheus",
    "guardian",
    "auditlog",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.organizations",
    "apps.subscriptions",
    "apps.contacts",
    "apps.companies",
    "apps.opportunities",
    "apps.tasks",
    "apps.activities",
    "apps.emails",
    "apps.reports",
    "apps.customization",
    "apps.integrations",
    "apps.notifications",
    "apps.dashboard",
    "apps.leads",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# -----------------------------------------------------------------------------
# MIDDLEWARE
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

# -----------------------------------------------------------------------------
# TEMPLATES
# -----------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# -----------------------------------------------------------------------------
# DATABASE
# -----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", default="crm"),
        "USER": os.getenv("DB_USER", default="postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", default="sakar@7"),
        "HOST": os.getenv("DB_HOST", default="localhost"),
        "PORT": os.getenv("DB_PORT", default="5432"),
    }
}

# -----------------------------------------------------------------------------
# AUTHENTICATION
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "core.filters.AdvancedQueryFilterBackend",
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_RENDERER_CLASSES": ("core.renderers.StandardJSONRenderer",),
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsSetPagination",
    "DEFAULT_SCHEMA_CLASS": "core.schema.TaggedAutoSchema",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "CRM SaaS API",
    "DESCRIPTION": "Interactive documentation for the CRM SaaS platform.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}

# -----------------------------------------------------------------------------
# CELERY / REDIS
# -----------------------------------------------------------------------------
REDIS_URL = os.getenv("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# -----------------------------------------------------------------------------
# CACHING
# -----------------------------------------------------------------------------
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# -----------------------------------------------------------------------------
# STATIC & MEDIA
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# -----------------------------------------------------------------------------
# STRIPE
# -----------------------------------------------------------------------------
# STRIPE_TEST_PUBLIC_KEY = os.getenv("STRIPE_TEST_PUBLIC_KEY", default="")
# STRIPE_TEST_SECRET_KEY = os.getenv("STRIPE_TEST_SECRET_KEY", default="")
# DJSTRIPE_WEBHOOK_SECRET = os.getenv("DJSTRIPE_WEBHOOK_SECRET", default="")
# DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

# -----------------------------------------------------------------------------
# DEFAULTS
# -----------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
TIME_ZONE = "UTC"
USE_TZ = True
LANGUAGE_CODE = "en-us"
