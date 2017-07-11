
from django.conf.urls import url

from .views import *

app_name = "casting"
urlpatterns = [
    url(r'^$', index, name="index"),
    url(r'^admin/$', admin, name="admin"),
]
