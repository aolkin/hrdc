
from django.conf.urls import url, include

from .views import *

app_name = "finance"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^show/(?P<pk>\d+)/income/$', IncomeView.as_view(), name="income"),
]
