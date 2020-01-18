
from django.conf.urls import url, include
from django.urls import path

from .views import *

app_name = "publicity"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^show/(?P<pk>\d+)/', include([
        url(r'^$', DisplayView.as_view(), name="display"),
        url(r'^script.js$', ShowScriptView.as_view(), name="script"),
        url(r'^info/$', InfoView.as_view(), name="info"),
        url(r'^people/$', PeopleView.as_view(), name="people"),
        url(r'^people/import/staff$', ImportStaff.as_view(),
            name="import_staff"),
        url(r'^people/import/cast$', ImportCast.as_view(),
            name="import_cast"),
    ])),
    url(r'^newsletter/$', NewsletterView.as_view(), name="public_app"),
    url(r'^newsletter/(?P<pk>\d+)/$', NewsletterEditView.as_view(),
        name="edit_announcement"),
    path('calendar/', CalendarView.as_view(), name="public_index"),
    path('calendar/<int:year>/<int:month>/', CalendarView.as_view(),
         name="calendar"),
    path('season/', SeasonScriptView.as_view(), name="season"),
]
