
import os
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SECRET_KEY = ''

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', ".ngrok.io"]


SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = ''

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


ANYMAIL = {
    "MAILGUN_API_KEY": "",
    "MAILGUN_SENDER_DOMAIN": ""
}

DEFAULT_FROM_EMAIL = "From Email <email@example.com>"


ADMIN_SITE_TITLE = "HRDC Apps"

ADMIN_GROUP_NAME = "HRDC Board"


BT_SITE_TITLE = "HRDC Apps"
FOOTER_OWNER = "Harvard-Radcliffe Dramatic Club"
FOOTER_SITE = "https://hrdctheater.org"


GROUP_LOCATION = "Harvard"
SITE_URL = "http://localhost:8000"

LOGO_PATH = os.path.join(BASE_DIR, "hrdc/static/logo.png")

CASTING_IS_COMMON = True


CELERY_BEAT_SCHEDULE = {
    'update-casting-releases': {
        'task': 'casting.tasks.update_releases',
        'schedule': 10.0,
        'relative': True,
    },
    'send-missed-emails': {
        'task': 'emailtracker.tasks.send_missing',
        'schedule': 60.0 * 10.0,
        'relative': False,
    },
}


QUEUED_EMAIL_TEMP = None
QUEUED_EMAIL_DEBUG = True

CHAT_LOADING_LIMIT = 20

SHORTLINK_PREFIX = "127.0.0.1:8000" + "/shortlinks/"
