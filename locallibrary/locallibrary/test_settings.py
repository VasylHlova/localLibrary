# ruff: noqa: F403, F405
from .settings import *

# Strip out Django Silk
if "silk" in INSTALLED_APPS:
    INSTALLED_APPS.remove("silk")

if "silk.middleware.SilkyMiddleware" in MIDDLEWARE:
    MIDDLEWARE.remove("silk.middleware.SilkyMiddleware")

# Use fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use Local Memory Cache instead of Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Use InMemoryStorage instead of hitting S3/Cloudflare R2 during tests
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Ensure Celery runs tasks synchronously in tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
