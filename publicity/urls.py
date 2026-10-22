
from django.urls import include, path, re_path

from .views import *

app_name = "publicity"
urlpatterns = [
    re_path(r'^$', IndexView.as_view(), name="index"),
    re_path(r'^show/(?P<pk>\d+)/', include([
        re_path(r'^$', DisplayView.as_view(), name="display"),
        re_path(r'^script.(?P<format>js|json)$', ShowScriptView.as_view(), name="script"),
        re_path(r'^info/$', InfoView.as_view(), name="info"),
        re_path(r'^people/$', PeopleView.as_view(), name="people"),
        re_path(r'^people/import/staff$', ImportStaff.as_view(),
            name="import_staff"),
        re_path(r'^people/import/cast$', ImportCast.as_view(),
            name="import_cast"),
    ])),
    re_path(r'^newsletter/$', NewsletterView.as_view(), name="public_app"),
    re_path(r'^newsletter/(?P<pk>\d+)/$', NewsletterEditView.as_view(),
        name="edit_announcement"),
    path('calendar/', CalendarView.as_view(), name="public_index"),
    path('calendar/<int:year>/<int:month>/', CalendarView.as_view(),
         name="calendar"),
    re_path('^upcoming.(?P<format>js|json)$', UpcomingScriptView.as_view(), name="upcoming"),
    re_path('^season.(?P<format>js|json)$', SeasonScriptView.as_view(), name="season"),
    re_path('^seasons.(?P<format>js|json)$', SeasonsScriptView.as_view(), name="seasons"),
    re_path(r'^admin/$', AdminIndexView.as_view(), name="admin"),
    re_path(r'^admin/', include(([
        path("season/<int:year>/<int:season>/", AdminSeasonView.as_view(),
             name="season"),
        re_path(r'^show/(?P<pk>\d+)/', include([
            re_path(r'^$', AdminShowView.as_view(), name="show"),
        ])),
    ], "admin"))),
    re_path('^api/', include([
        path('slug/<slug:slug>', ShowDataView.as_view(), name="show_data"),
        path('query', ShowQueryView.as_view(), name="show_query")
    ]))
]
