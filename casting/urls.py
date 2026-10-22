
from django.urls import include, re_path

from .views import *
from .views.sign_in import urlpatterns as signin_patterns
from .views.pdsm import urlpatterns as pdsm_patterns
from .views.public import urlpatterns as public_patterns

app_name = "casting"
urlpatterns = [
    re_path(r'^sign-in/', include(signin_patterns)),
    re_path(r'^staff/', include(pdsm_patterns)),
    re_path(r'^actor/', include(public_patterns)),

    re_path(r'^admin/$', admin, name="admin"),
]
