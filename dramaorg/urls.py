
from django.conf.urls import url, include
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views

from .views import *

def auth_view(name):
    v = getattr(auth_views, name + "View")
    class NewView(v):
        template_name = v.template_name.replace("registration","dramaauth")
        success_url = reverse_lazy("dramaorg:{}_done".format(name))
    return NewView.as_view()

auth_urls = [
    url(r'login/$', auth_view("Login"), name='login'),
    url(r'logout/$', auth_view("Logout"), name='logout'),
    url(r'password/$', auth_view("PasswordChange"),
        name='password_change'),
    url(r'password/done/$', auth_view("PasswordChangeDone"),
        name='PasswordChange_done'),
]

app_name = "dramaorg"
urlpatterns = [
    url(r'^$', index, name="index"),
    url(r'', include(auth_urls)),
    url(r'create/$', CreateView.as_view(), name="create"),
    url(r'login/([A-Za-z0-9+-]{86})/$', TokenView.as_view(),
        name="token_create"),
    url(r'reset/$', ResetView.as_view(), name="start_reset"),
]
