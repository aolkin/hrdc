
from django.conf.urls import url, include

from .views import *

app_name = "publicity"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
]
