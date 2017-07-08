"""hrdc URL Configuration"""

from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.urls import reverse


urlpatterns = [
    url(r'^', include("dramaorg.urls")),
    url(r'^admin/', admin.site.urls),
]
