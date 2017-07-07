
from django.conf.urls import url
from django.contrib.auth import views as auth_views

from .views import *

urlpatterns = [
    url(r'^$', auth_views.LoginView.as_view(), name="index"),
    url(r'^create/', CreateView.as_view(), name="initialize_user"),
    url(r'^create/([A-Za-z0-9+-]{86})/', TokenView.as_view(create=True),
        name="token_create"),
    url(r'^reset/', ResetView.as_view(), name="start_reset"),
    url(r'^reset/([A-Za-z0-9+-]{86})/', TokenView.as_view(),
        name="token_reset")
]
