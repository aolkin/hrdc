"""hrdc URL Configuration"""

from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic.base import RedirectView
from django.urls import reverse

from config import config

class HomeRedirect(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        return reverse(config.get("home","index"))

urlpatterns = [
    url(r'^$', HomeRedirect.as_view()),
    url(r'^u/', include("dramaorg.urls")),
    url(r'^admin/', admin.site.urls),
]
