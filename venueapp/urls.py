
from django.conf.urls import url, include

from .views import *

app_name = "venueapp"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="public_index"),
    url(r'^form/$', ContactView.as_view(), name="form"),
]
