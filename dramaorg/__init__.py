from django.conf import settings
from django.db.utils import OperationalError
from django.contrib import admin

from importlib import import_module

default_app_config = "dramaorg.apps.DramaorgConfig"

def get_admin_group():
    auth = import_module("django.contrib.auth.models")
    try:
        return auth.Group.objects.get_or_create(
            name=settings.ADMIN_GROUP_NAME)[0]
    except OperationalError:
        return None

admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.site_header = settings.ADMIN_SITE_TITLE
