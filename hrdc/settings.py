"""
Django settings for hrdc project.

Generated by 'django-admin startproject' using Django 1.11.3.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# Application definition

INSTALLED_APPS = [
    'config',
    'emailtracker',
    'basetemplates',
    'chat',
    'hrdc',
    'django.contrib.humanize',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_thumbs',
    'social_django',
    'rangefilter',
    'dramaorg',
    'venueapp',
    'casting',
    'publicity',
    'finance',
    'archive',
    'shortlinks',
    'crispy_forms',
    'anymail',
    'channels',
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "ROUTING": "hrdc.routing.channel_routing",
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hrdc.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'config.context_processors.configuration',
                'basetemplates.context_processor',
            ],
        },
    },
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

WSGI_APPLICATION = 'hrdc.wsgi.application'

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_URL_NAMESPACE = 'social'

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'dramaorg.utils.social_create_user',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'social_core.pipeline.social_auth.associate_by_email',
)


CSRF_USE_SESSIONS = True

SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGES = [
  ('en-us', _('English')),
]

LANGUAGE_CODE = 'en-us'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale')
]

TIME_ZONE = 'US/Eastern'

USE_I18N = True

USE_L10N = False

USE_TZ = True

DATETIME_FORMAT = "M j, Y, g:i A"

DATETIME_OUTPUT_FILTER_FORMAT = "l, F d, Y [at] g:i A"
DATETIME_INPUT_FORMAT = "%A, %B %-d, %Y at %-I:%M %p"

DATETIME_INPUT_FORMATS = [
    DATETIME_INPUT_FORMAT,
    "%A, %B %d, %Y at %I:%M %p",
    '%Y-%m-%d %I:%M %p',     # '2006-10-25 10:30 AM'
    '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
    '%Y-%m-%d %H:%M:%S.%f',  # '2006-10-25 14:30:59.000200'
    '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
    '%Y-%m-%d',              # '2006-10-25'
    '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
    '%m/%d/%Y %H:%M:%S.%f',  # '10/25/2006 14:30:59.000200'
    '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
    '%m/%d/%Y',              # '10/25/2006'
    '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
    '%m/%d/%y %H:%M:%S.%f',  # '10/25/06 14:30:59.000200'
    '%m/%d/%y %H:%M',        # '10/25/06 14:30'
    '%m/%d/%y',              # '10/25/06'
]

STATIC_URL = '/static/'

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

CELERY_BEAT_SCHEDULE = {
    'update-casting-releases': {
        'task': 'casting.tasks.update_releases',
        'schedule': 10.0,
        'relative': True,
    },
    'auto-finish-auditions': {
        'task': 'casting.tasks.force_complete_auditions',
        'schedule': 10.0,
        'relative': True,
    },
    'send-missed-emails': {
        'task': 'emailtracker.tasks.send_missing',
        'schedule': 60.0 * 10.0,
        'relative': False,
    },
}

AUTH_USER_MODEL = "dramaorg.User"

SHOW_MODEL = "dramaorg.Show"
SPACE_MODEL = "dramaorg.Space"
BUILDING_MODEL = "dramaorg.Building"


EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

CONFIGURATION_APP_TITLE = "Settings"

LOGIN_URL = "dramaorg:login"
LOGOUT_URL = "dramaorg:logout"
LOGIN_REDIRECT_URL = "dramaorg:home"
LOGOUT_REDIRECT_URL = LOGIN_REDIRECT_URL

BT_FAVICON_URL = STATIC_URL + "icon.png"
BT_POPPER_VERSION = "1.12.9"
BT_POPPER_INTEGRITY = "sha384-ApNbgh9B+Y1QKtv3Rn7W3mgPxhU9K/ScQsAP7hUibX39j7fakFPskvXusvfa0b4Q"
BT_BOOTSTRAP_VERSION = "4.4.1"

BT_THEME_COLOR = "#eb1c23"
BT_HEADER_IMAGE = "logo.png"
BT_HEADER_URL = "dramaorg:home"

BT_JS_FILES = ["profilefields.js"]
BT_CSS_FILES = ["global.css"]

ACTIVE_SEASON_KEY = "season"
ACTIVE_YEAR_KEY = "year"

THUMBS_JPG = False

# CORS_ALLOWED_ORIGINS = [
#     "https://hrdctheater.org"
# ]

from .local_settings import *
