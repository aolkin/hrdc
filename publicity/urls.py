
from django.conf.urls import url, include

from .views import *

app_name = "publicity"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^show/(?P<pk>\d+)/$', DisplayView.as_view(), name="display"),
    url(r'^show/(?P<pk>\d+)/script.js$', ScriptView.as_view(), name="script"),
    url(r'^show/(?P<pk>\d+)/info/$', InfoView.as_view(), name="info"),
    url(r'^show/(?P<pk>\d+)/people/$', PeopleView.as_view(), name="people"),
]
