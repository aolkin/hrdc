
from django.conf.urls import url

from .views import *

app_name = "casting"
urlpatterns = [
    url(r'^$', index, name="index"),
    url(r'^edit/show/(?P<pk>\d+)/$', ShowEditor.as_view(), name="edit_show"),
    url(r'^auditions/signin/(?P<pk>\d+)/$', ActorSignInStart.as_view(),
        name="sign_in_start"),
    url(r'^auditions/signin/(?P<pk>\d+)/all/$',
        ActorSignInStart.as_view(show_all=True),
        name="sign_in_start_all"),
    url(r'^auditions/signin/(?P<pk>\d+)/popout/$',
        ActorSignInStart.as_view(popout=True),
        name="sign_in_start_popout"),
    url(r'^auditions/signin/profile/$', ActorSignInProfile.as_view(),
        name="sign_in_profile"),
    url(r'^auditions/signin/done/$', ActorSignInDone.as_view(),
        name="sign_in_done"),
    url(r'^admin/$', admin, name="admin"),
]
