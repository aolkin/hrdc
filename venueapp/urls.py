
from django.conf.urls import url, include

from .views import *

app_name = "venueapp"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="public_index"),
    url(r'^seasonmeta/(?P<pk>\d+)/$', SeasonStaffView.as_view(),
        name="seasonmeta"),
    url(r'^apply/new/$', NewApplication.as_view(), name="new"),
    url(r'^apply/(?P<pk>\d+)/', include([
        url(r'^details/$', UpdateApplication.as_view(), name="details"),
        url(r'^staff/$', StaffView.as_view(), name="staff"),
        url(r'^staff/add/$', AddStaffView.as_view(), name="add_staff"),
        url(r'^residencies/$', ResidencyView.as_view(), name="residencies"),
        url(r'^budget/$', BudgetView.as_view(), name="budget"),
        url(r'^budget/add/$', AddBudgetView.as_view(), name="add_budget"),
        url(r'^questions/$', QuestionsView.as_view(), name="questions"),
        url(r'^role/(?P<role>\d+)/', include([
            url(r'^$', IndividualView.as_view(), name="individual"),
            url(r'^join/$', SignOnView.as_view(), name="join"),
            url(r'^leave/$', SignOffView.as_view(), name="leave"),
        ])),
        url(r'^delete/$', DeleteApplication.as_view(), name="deleteapp"),
        url(r'^submit/$', PreviewSubmitView.as_view(), name="submit"),
    ])),
    url(r'^read/$', AdminIndexView.as_view(), name="admin"),
    url(r'^read/(?P<pk>\d+)/', include([
        url(r'^$', AdminListView.as_view(), name="applist"),
        url(r'^app/(?P<app>\d+)/', AdminReadView.as_view(), name="read"),
    ])),
]
