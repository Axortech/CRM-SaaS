from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# SQLite for quick local dev (optional, or use PostgreSQL from .env)
DATABASES["default"]["NAME"] = os.getenv("DB_NAME", default=os.path.join(BASE_DIR, "db.sqlite3"))
DATABASES["default"]["ENGINE"] = os.getenv("DB_ENGINE", default="django.db.backends.sqlite3")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

INSTALLED_APPS += ["django_extensions"]  # optional utilities

# Celery - run tasks eagerly for dev
CELERY_TASK_ALWAYS_EAGER = True
