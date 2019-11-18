from django.conf import settings
from django.conf.urls import url

from .views import *

app_name = "emailtracker"
urlpatterns = [
    url(r'^$', EmailerView.as_view(), name="admin"),
]
if settings.DEBUG:
    urlpatterns.append(url(r'^preview/$', preview))
