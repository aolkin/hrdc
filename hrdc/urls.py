"""hrdc URL Configuration"""

from django.conf.urls import url, include
from django.contrib import admin

from config.views import autocomplete_json

urlpatterns = [
    url(r'^', include("dramaorg.urls")),
    url(r'^autocomplete/$', autocomplete_json),
    url(r'^casting/', include("casting.urls")),
    url(r'^admin/', admin.site.urls),
    url(r'^email/', include('emailtracker.views')),
]
