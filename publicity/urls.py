
from django.conf.urls import url, include

from .views import *

app_name = "publicity"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^show/(?P<pk>\d+)/info/$', InfoView.as_view(), name="info"),
    url(r'^show/(?P<pk>\d+)/people/$', PeopleView.as_view(), name="people"),
]
