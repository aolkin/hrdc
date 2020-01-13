"""hrdc URL Configuration"""

from django.urls import path
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from config.views import autocomplete_json
from shortlinks.views import link, LinksView

urlpatterns = [
    url(r'^', include("dramaorg.urls")),
    url(r'^autocomplete/$', autocomplete_json),
    url(r'^venues/', include("venueapp.urls")),
    url(r'^casting/', include("casting.urls")),
    url(r'^publicity/', include("publicity.urls")),
    url(r'^finance/', include("finance.urls")),
    url(r'^archive/', include("archive.urls")),
    url(r'^admin/', admin.site.urls),
    url(r'^email/', include('emailtracker.urls')),
    path(r'shortlinks/<slug:slug>', link, name="shortlink"),
    path('links/', include('shortlinks.urls')),
    path('social/', include('social_django.urls', namespace='social')),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static("/" + settings.MEDIA_URL.split("/",3)[-1],
                          document_root=settings.MEDIA_ROOT)
