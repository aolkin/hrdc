
from django.conf.urls import url, include

from .views import *

app_name = "venueapp"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="public_index"),
    url(r'^new/$', NewApplication.as_view(), name="new"),
    url(r'^app/(?P<pk>\d+)/', include([
        url(r'^details/$', UpdateApplication.as_view(), name="details"),
        url(r'^staff/$', StaffView.as_view(), name="staff"),
        url(r'^staff/add/$', AddStaffView.as_view(), name="add_staff"),
        url(r'^residencies/$', ResidencyView.as_view(), name="residencies"),
    ])),
]
