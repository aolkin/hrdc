
from django.urls import include, re_path

from .views import *

app_name = "venueapp"
urlpatterns = [
    re_path(r'^$', IndexView.as_view(), name="public_index"),
    re_path(r'^seasonmeta/(?P<pk>\d+)/$', SeasonStaffView.as_view(),
        name="seasonmeta"),
    re_path(r'^apply/new/$', NewApplication.as_view(), name="new"),
    re_path(r'^apply/(?P<pk>\d+)/', include([
        re_path(r'^details/$', UpdateApplication.as_view(), name="details"),
        re_path(r'^staff/$', StaffView.as_view(), name="staff"),
        re_path(r'^staff/add/$', AddStaffView.as_view(), name="add_staff"),
        re_path(r'^residencies/$', ResidencyView.as_view(), name="residencies"),
        re_path(r'^budget/$', BudgetView.as_view(), name="budget"),
        re_path(r'^budget/add/$', AddBudgetView.as_view(), name="add_budget"),
        re_path(r'^questions/$', QuestionsView.as_view(), name="questions"),
        re_path(r'^role/(?P<role>\d+)/', include([
            re_path(r'^$', IndividualView.as_view(), name="individual"),
            re_path(r'^join/$', SignOnView.as_view(), name="join"),
            re_path(r'^leave/$', SignOffView.as_view(), name="leave"),
        ])),
        re_path(r'^delete/$', DeleteApplication.as_view(), name="deleteapp"),
        re_path(r'^submit/$', PreviewSubmitView.as_view(), name="submit"),
    ])),
    re_path(r'^read/$', AdminIndexView.as_view(), name="venuelist"),
    re_path(r'^read/(?P<pk>\d+)/', include([
        re_path(r'^$', AdminListView.as_view(), name="applist"),
        re_path(r'^app/(?P<app>\d+)/', AdminReadView.as_view(), name="read"),
    ])),
]
