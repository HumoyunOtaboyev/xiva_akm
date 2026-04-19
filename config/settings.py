from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# =====================
# SECRET & DEBUG
# =====================
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-placeholder-key-for-development')

DEBUG = False

ALLOWED_HOSTS = ["xiva-akm.uz"]


# =====================
# APPS
# =====================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'whitenoise.runserver_nostatic',

    # THIRD PARTY
    'django_ckeditor_5',

    # CUSTOM APPS
    'app',
    'news',
    'hodimlar',
    'elonlar',
    'kutubxona',
    'tadbirlar'
]


# =====================
# MIDDLEWARE
# =====================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


# =====================
# TEMPLATES
# =====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# =====================
# DATABASE
# =====================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# =====================
# INTERNATIONALIZATION
# =====================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# =====================
# STATIC FILES (CSS, JS)
# =====================
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# =====================
# MEDIA FILES (images, uploads)
# =====================
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# =====================
# CKEDITOR 5 CONFIG
# =====================
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading", "|", "bold", "italic", "link",
            "bulletedList", "numberedList", "blockQuote",
            "imageUpload", "insertTable", "mediaEmbed",
            "undo", "redo"
        ],
        "image": {
            "toolbar": [
                "imageTextAlternative",
                "imageStyle:alignLeft",
                "imageStyle:alignCenter",
                "imageStyle:alignRight",
                "imageStyle:side",
            ]
        },
        "table": {
            "contentToolbar": [
                "tableColumn", "tableRow",
                "mergeTableCells",
                "tableCellProperties",
                "tableProperties"
            ]
        },
        "mediaEmbed": {
            "previewsInData": True
        }
    }
}


# =====================
# DEFAULT AUTO FIELD
# =====================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'