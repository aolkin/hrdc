
from django.conf.urls import url, include
from django.urls import reverse_lazy, path
from django.contrib.auth import views as auth_views

from .views import *

def auth_view(name):
    v = getattr(auth_views, name + "View")
    class NewView(v):
        template_name = v.template_name.replace("registration","dramaauth")
        success_url = reverse_lazy("dramaorg:home")
    return NewView.as_view()

auth_urls = [
    url(r'^login/$', LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_view("Logout"), name='logout'),
    url(r'^password/$', auth_view("PasswordChange"), name='password_change')
]

app_name = "dramaorg"
urlpatterns = [
    url(r'^$', HomePage.as_view(), name="home"),

    url(r'^staff/$', StaffIndexView.as_view(), name="index"),
    url(r'^staff/show/(?P<pk>\d+)/$', UpdateShow.as_view(), name="update"),
    url(r'^staff/show/(?P<pk>\d+)/staff/$', UpdateShowStaff.as_view(),
        name="update_staff"),

    url(r'^season/$', ManagementView.as_view(), name="admin"),
    url(r'^season/(?P<year>\d+)/(?P<season>\d+)/', include([
        url(r'^$', SeasonView.as_view(), name="season"),
    ])),

    url(r'^people/search/$', SearchPeople.as_view(), name="search_people"),
    url(r'^people/add/$', AddPerson.as_view(), name="add_person"),

    url(r'^', include(auth_urls)),
    url(r'^profile/$', ProfileView.as_view(), name="profile"),
    url(r'^account/$', AccountView.as_view(), name="account"),
    url(r'^register/$', RegisterView.as_view(), name="register"),
    url(r'^u/([A-Za-z0-9+-]{86})/$', capture_token, name="token_reset"),
    url(r'^password/token/$', TokenView.as_view(), name="password_token"),
    url(r'^reset/$', ResetView.as_view(), name="start_reset"),
]
