
from django.conf.urls import url, include

from .views import *
from .views.sign_in import urlpatterns as signin_patterns
from .views.pdsm import urlpatterns as pdsm_patterns
from .views.public import urlpatterns as public_patterns

app_name = "casting"
urlpatterns = [
    url(r'^sign-in/', include(signin_patterns)),
    url(r'^staff/', include(pdsm_patterns)),
    url(r'^actor/', include(public_patterns)),
    
    #url(r'^admin/$', admin, name="admin"),
]
