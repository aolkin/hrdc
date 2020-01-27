
from django.conf.urls import url, include
from django.urls import path

from .views import *

app_name = "finance"
urlpatterns = [
    url(r'^$', IndexView.as_view(), name="index"),
    url(r'^show/(?P<pk>\d+)/', include([
        path('income/', IncomeView.as_view(), name="income"),
        path('budget/', BudgetView.as_view(), name="budget"),
        path('expenses/', ExpenseView.as_view(), name="expenses"),
        path('import/', ImportView.as_view(), name="import"),
    ])),
    url(r'^tax-certificate/$', view_tax_certificate, name="tax_certificate"),
    path('settle/<int:pk>/', SettlementView.as_view(), name="settlement"),
]
