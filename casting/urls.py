
from django.conf.urls import url, include

from .views import *
from .sign_in_views import *

app_name = "casting"
urlpatterns = [
    url(r'^$', index, name="index"),
    url(r'^edit/show/(?P<pk>\d+)/$', ShowEditor.as_view(), name="edit_show"),
    
    url(r'^auditions/signin/', include([
        url(r'^(?P<pk>\d+)/$', ActorSignInStart.as_view(),
            name="sign_in_start"),
        url(r'^(?P<pk>\d+)/all/$',
            ActorSignInStart.as_view(show_all=True),
            name="sign_in_start_all"),
        url(r'^(?P<pk>\d+)/popout/$',
            ActorSignInStart.as_view(popout=True),
            name="sign_in_start_popout"),
        url(r'^profile/$', ActorSignInProfile.as_view(),
            name="sign_in_profile"),
        url(r'^done/$', ActorSignInDone.as_view(),
            name="sign_in_done")])),
    
    url(r'^admin/$', admin, name="admin"),
]
