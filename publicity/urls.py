
from django.conf.urls import url, include

from .views import *

app_name = "publicity"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^show/(?P<pk>\d+)/', include([
        url(r'^$', DisplayView.as_view(), name="display"),
        url(r'^script.js$', ScriptView.as_view(), name="script"),
        url(r'^info/$', InfoView.as_view(), name="info"),
        url(r'^people/$', PeopleView.as_view(), name="people"),
        url(r'^people/search$', SearchPerson.as_view(), name="search_people"),
        url(r'^people/add$', AddUser.as_view(), name="add_person"),
    ])),
    url(r'^newsletter/$', NewsletterView.as_view(), name="public_index"),
    url(r'^newsletter/(?P<pk>\d+)/$', NewsletterEditView.as_view(),
        name="edit_announcement"),
]
