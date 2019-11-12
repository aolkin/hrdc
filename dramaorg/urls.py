
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
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_view("Logout"), name='logout'),
    url(r'^password/$', auth_view("PasswordChange"),
        name='password_change'),
    url(r'^password/done/$', auth_view("PasswordChangeDone"),
        name='password_change_done'),
]

app_name = "dramaorg"
urlpatterns = [
    url(r'^$', HomePage.as_view(), name="home"),
    url(r'^staff/$', StaffIndexView.as_view(), name="index"),
    url(r'^season/$', ManagementView.as_view(), name="admin"),
    url(r'^season/(?P<year>\d+)/(?P<season>\d+)/', include([
        url(r'^$', SeasonView.as_view(), name="season"),
    ])),
    url(r'^', include(auth_urls)),
    url(r'^profile/$', ProfileView.as_view(), name="profile"),
    url(r'^register/$', RegisterView.as_view(), name="register"),
    url(r'^u/([A-Za-z0-9+-]{86})/$', capture_token, name="token_reset"),
    url(r'^password/token/$', TokenView.as_view(), name="password_token"),
    url(r'^reset/$', ResetView.as_view(), name="start_reset"),
]
