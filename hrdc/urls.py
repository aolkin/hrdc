"""hrdc URL Configuration"""

from django.urls import path
from django.conf.urls import url, include
from django.contrib import admin

from config.views import autocomplete_json
from shortlinks.views import link

urlpatterns = [
    url(r'^', include("dramaorg.urls")),
    url(r'^autocomplete/$', autocomplete_json),
    url(r'^casting/', include("casting.urls")),
    url(r'^publicity/', include("publicity.urls")),
    url(r'^finance/', include("finance.urls")),
    url(r'^archive/', include("archive.urls")),
    url(r'^admin/', admin.site.urls),
    url(r'^email/', include('emailtracker.views')),
    path(r'shortlinks/<slug:slug>', link, name="shortlink"),
    path('social/', include('social_django.urls', namespace='social')),
]
