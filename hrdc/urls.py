"""hrdc URL Configuration"""

from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^', include("dramaorg.urls")),
    url(r'^casting/', include("casting.urls")),
    url(r'^admin/', admin.site.urls),
]
