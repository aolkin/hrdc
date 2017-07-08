from django.conf import settings
from django.contrib import admin

default_app_config = "dramaorg.apps.DramaorgConfig"

admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.site_header = settings.ADMIN_SITE_TITLE
