
from django.conf.urls import url, include

from .views import *

app_name = "archive"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^show/(?P<pk>\d+)/$', ShowView.as_view(), name="show"),
    url(r'^show/(?P<pk>\d+)/upload/$', UploadView.as_view(), name="upload"),
    url(r'^view/', include([
        url(r'^$', PublicView.as_view(), name="public_index"),
        url(r'^(?P<pk>\d+)/$', PublicDetailView.as_view(), name="detail"),
    ]))
]
