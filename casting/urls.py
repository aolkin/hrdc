
from django.conf.urls import url, include

from .views import *
from .views.sign_in import urlpatterns as signin_patterns
from .views.pdsm import urlpatterns as pdsm_patterns

app_name = "casting"
urlpatterns = [
    url(r'^edit/show/(?P<pk>\d+)/$', ShowEditor.as_view(), name="edit_show"),
    
    url(r'^sign-in/', include(signin_patterns)),
    url(r'^staff/', include(pdsm_patterns)),
    
    url(r'^admin/$', admin, name="admin"),
]
