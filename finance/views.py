from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django import forms
from django.contrib import messages
    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from utils import user_is_initialized

from django.conf import settings

from .models import *

class InitializedLoginMixin:
    @method_decorator(login_required)
    @method_decorator(user_is_initialized)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class MenuMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        menu[""] = [{
            "name": "Financials",
            "url": reverse_lazy("finance:index"),
            "active": current_url == "index"
        }]

        if self.request.user.is_anonymous:
            return context
        
        for show in [i for i in
                     self.request.user.show_set.all().order_by("-pk")
                     if hasattr(i, "finance_info")]:
            submenu = menu[str(show)] = []
            is_active = (hasattr(self, "object") and
                         self.object.pk == show.finance_info.pk)
            submenu.append({
                "name": "Grants and Income",
                "url": reverse_lazy("finance:income",
                                    args=(show.finance_info.pk,)),
                "active": is_active and current_url == "income"
            })
            submenu.append({
                "name": "Budget",
                "url": reverse_lazy("finance:budget",
                                    args=(show.finance_info.pk,)),
                "active": is_active and current_url == "budget"
            })
        return context

class ShowStaffMixin(InitializedLoginMixin, SingleObjectMixin):
    model = FinanceInfo
    
    test_silent = False
    
    def test_func(self):
        if super().test_func():
            if self.get_object().show.user_is_staff(self.request.user):
                return True
            else:
                if not self.test_silent:
                    messages.error(self.request, "You are not a member of the "
                                   "executive staff of that show. Log in as a "
                                   "different user?")
        return False

class IndexView(MenuMixin, InitializedLoginMixin, TemplateView):
    verbose_name = "Show Finances"
    help_text = "Manage budget and finances"
    
    template_name = "finance/index.html"


BaseIncomeFormSet = forms.inlineformset_factory(
    FinanceInfo, Income,
    fields=("name", "amount_requested", "amount_received", "status"), extra=1
)

class IncomeFormSet(BaseIncomeFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset.filter(status__lt=90)

class IncomeView(MenuMixin, ShowStaffMixin, TemplateView):
    template_name = "finance/income.html"
    model = FinanceInfo

    def post(self, *args, **kwargs):
        self.formset = IncomeFormSet(self.request.POST,
                                     instance=self.get_object())
        if self.formset.is_valid():
            self.formset.save()
        else:
            messages.error(self.request, "Failed to save income information. "+
                           "Please try again.")
            return self.get(*args, **kwargs)
        messages.success(self.request,
                         "Updated income information for {}.".format(
                             self.get_object()))
        return redirect(reverse_lazy("finance:income",
                                     args=(self.get_object().id,)))

    def get_context_data(self, *args, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(*args, **kwargs)
        context["confirmed"] = self.object.income_set.filter(status__gte=90)
        context["formset"] = (
            self.formset if hasattr(self, "formset") else IncomeFormSet(
                instance=self.get_object()
            )
        )
        return context

class BudgetView(MenuMixin, ShowStaffMixin, DetailView):
    template_name = "finance/budget.html"
    model = FinanceInfo

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        return context
