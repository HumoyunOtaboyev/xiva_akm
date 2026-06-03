"""
Local development settings — NOT for production.
Run with:  python manage.py runserver --settings=config.settings_local
Overrides the production static/media paths so the repo's assets serve locally.
"""
import os

os.environ.setdefault("DEBUG", "True")

from .settings import *  # noqa: F401,F403

DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
