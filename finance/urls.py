
from django.conf.urls import url, include

from .views import *

app_name = "finance"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^show/(?P<pk>\d+)/income/$', IncomeView.as_view(), name="income"),
    url(r'^show/(?P<pk>\d+)/budget/$', BudgetView.as_view(), name="budget"),
    url(r'^show/(?P<pk>\d+)/expenses/$', ExpenseView.as_view(),
        name="expenses"),
    url(r'^tax-certificate/$', view_tax_certificate, name="tax_certificate"),
]
