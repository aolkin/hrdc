
from django.urls import include, path, re_path, reverse_lazy
from django.contrib.auth import views as auth_views

from .views import *

def auth_view(name):
    v = getattr(auth_views, name + "View")
    class NewView(v):
        template_name = v.template_name.replace("registration","dramaauth")
        success_url = reverse_lazy("dramaorg:home")
    return NewView.as_view()

auth_urls = [
    re_path(r'^login/$', LoginView.as_view(), name='login'),
    re_path(r'^logout/$', auth_view("Logout"), name='logout'),
    re_path(r'^password/$', auth_view("PasswordChange"), name='password_change')
]

app_name = "dramaorg"
urlpatterns = [
    re_path(r'^$', HomePage.as_view(), name="home"),

    re_path(r'^staff/$', StaffIndexView.as_view(), name="index"),
    re_path(r'^staff/show/(?P<pk>\d+)/$', UpdateShow.as_view(), name="update"),
    re_path(r'^staff/show/(?P<pk>\d+)/staff/$', UpdateShowStaff.as_view(),
        name="update_staff"),

    re_path(r'^season/$', ManagementView.as_view(), name="admin"),
    re_path(r'^season/(?P<year>\d+)/(?P<season>\d+)/', include([
        re_path(r'^$', SeasonView.as_view(), name="season"),
    ])),

    re_path(r'^people/search/$', SearchPeople.as_view(), name="search_people"),
    re_path(r'^people/add/$', AddPerson.as_view(), name="add_person"),

    re_path(r'^', include(auth_urls)),
    re_path(r'^profile/$', ProfileView.as_view(), name="profile"),
    re_path(r'^account/$', AccountView.as_view(), name="account"),
    re_path(r'^register/$', RegisterView.as_view(), name="register"),
    re_path(r'^u/([A-Za-z0-9+-]{86})/$', capture_token, name="token_reset"),
    re_path(r'^password/token/$', TokenView.as_view(), name="password_token"),
    re_path(r'^reset/$', ResetView.as_view(), name="start_reset"),
]
