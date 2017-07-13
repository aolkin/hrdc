
from django.conf.urls import url, include

from .views import *
from .sign_in_views import urlpatterns as signin_patterns
from .pdsm_views import urlpatterns as pdsm_patterns
from .pdsm_views import IndexView

app_name = "casting"
urlpatterns = [
    url(r'^edit/show/(?P<pk>\d+)/$', ShowEditor.as_view(), name="edit_show"),
    
    url(r'^sign-in/', include(signin_patterns)),
    url(r'^staff/', include(pdsm_patterns)),
    
    url(r'^admin/$', admin, name="admin"),
]
