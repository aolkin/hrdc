
from django.urls import include, re_path

from .views import *

app_name = "archive"
urlpatterns = [
    re_path(r'^$', IndexView.as_view(), name="index"),
    re_path(r'^show/(?P<pk>\d+)/$', ShowView.as_view(), name="show"),
    re_path(r'^show/(?P<pk>\d+)/upload/$', UploadView.as_view(), name="upload"),
    re_path(r'^view/', include([
        re_path(r'^$', PublicView.as_view(), name="public_index"),
        re_path(r'^(?P<pk>\d+)/$', PublicDetailView.as_view(), name="detail"),
    ]))
]
