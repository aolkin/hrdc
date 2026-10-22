from django.conf import settings
from django.urls import re_path

from .views import *

app_name = "emailtracker"
urlpatterns = [
    re_path(r'^$', EmailerView.as_view(), name="admin"),
]
if settings.DEBUG:
    urlpatterns.append(re_path(r'^preview/$', preview))
