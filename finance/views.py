from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
    
from utils import InitializedLoginMixin

from emailtracker.tools import render_to_queue
from config import config

import datetime, os

from django.conf import settings

from .models import *

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

        shows = [i.finance_info for i in
                 self.request.user.show_set.all().order_by("-pk")
                 if hasattr(i, "finance_info")]
        if (self.request.user.has_perm("finance.view_financeinfo") and
            hasattr(self, "object")):
            shows += [self.object]

        urls = [
            ("Grants and Income", "finance:income"),
            ("Budget", "finance:budget"),
            ("Expenses", "finance:expenses"),
        ]
        if (self.request.user.is_staff and
            self.request.user.has_perm("finance.change_financeinfo")):
            urls += [ ("[Admin Access]", "admin:finance_financeinfo_change") ]
        
        for show in shows:
            submenu = menu[str(show)] = []
            is_active = (hasattr(self, "object") and
                         self.object.pk == show.pk)
            for name, url in urls:
                submenu.append({
                    "name": name,
                    "url": reverse_lazy(url, args=(show.pk,)),
                    "active": is_active and current_url == url.split(":")[-1]
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
    verbose_name = "Finance Manager"
    help_text = "manage budget and accounting"
    
    template_name = "finance/index.html"


BaseIncomeFormSet = forms.inlineformset_factory(
    FinanceInfo, Income,
    fields=("name", "requested", "received", "status"), extra=1
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

class ExpenseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subcategory"].queryset = self.show_instance.budgetexpense_set.all()
        self.fields["date_purchased"].widget.is_required = False
        self.receipt_filename = os.path.basename(
            self.instance.receipt.name) if self.instance.receipt else None

    def clean(self):
        res = super().clean()
        if res["purchased_using"] == 1:
            if res["reimburse_via_mail"] and not res["mailing_address"]:
                raise ValidationError(
                    "Reimbursement via mail requires a mailing address.")
        return res

THIS_YEAR = datetime.date.today().year

BaseExpenseFormSet = forms.inlineformset_factory(
    FinanceInfo, Expense,
    form=ExpenseForm,
    fields=("item", "subcategory", "amount", "purchased_using",
            "date_purchased", "purchaser_name", "purchaser_email", "receipt",
            "reimburse_via_mail", "mailing_address", "submitting_user"),
    extra=1,
    widgets = {
        "mailing_address": forms.Textarea(attrs={"rows": 4, "cols": 40}),
        "receipt": forms.FileInput(),
        "submitting_user": forms.HiddenInput(),
        "date_purchased": forms.SelectDateWidget(
            years=range(THIS_YEAR - 1, THIS_YEAR + 2)),
    }
)

class ExpenseFormSet(BaseExpenseFormSet):
    def __init__(self, *args, submitting_user=None, **kwargs):
        self.form.show_instance = kwargs["instance"]
        super().__init__(*args, **kwargs)
        self.queryset = self.queryset.filter(status__lt=50)

class ExpenseView(MenuMixin, ShowStaffMixin, TemplateView):
    template_name = "finance/expenses.html"
    model = FinanceInfo

    def post(self, *args, **kwargs):
        self.formset = ExpenseFormSet(
            self.request.POST, self.request.FILES,
            instance=self.get_object(),
            initial=[{"submitting_user": self.request.user}]
        )
        if self.formset.is_valid():
            self.formset.save()
        else:
            messages.error(self.request, "Failed to save expense information. "+
                           "Please try again.")
            return self.get(*args, **kwargs)
        req = self.request.POST.get("request-reimbursement")
        if req:
            expense = Expense.objects.get(pk=req)
            expense.status = 61
            try:
                expense.full_clean()

                if config.get("fin_contact_email"):
                    res = render_to_queue(
                        "finance/email/reimbursement-requested.html",
                        "reimbursement-requested",
                        "{}: {}".format(expense.pk, expense.last_updated),
                        { "expense": expense },
                        to=config["fin_contact_email"],
                        subject="Reimbursement Requested for {}".format(
                            expense.show),
                        tags=["finance", "reimbursements",
                              "reimbursement_request"]
                    )
                    if not res:
                        messages.warning(
                            self.request, "Error sending reimbursement request."
                        )

                expense.save()
                messages.success(self.request,
                                 "Requested reimbursement for {}.".format(
                                     expense))
            except ValidationError as err:
                for msg in err.messages:
                    messages.error(self.request, msg)
                return self.get(*args, **kwargs)
        messages.success(self.request,
                         "Updated expense information for {}.".format(
                             self.get_object()))
        return redirect(reverse_lazy("finance:expenses",
                                     args=(self.get_object().id,)))

    def get_context_data(self, *args, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(*args, **kwargs)
        context["reimbursements"] = self.object.expense_set.filter(
            status__gte=60)
        context["p_card"] = self.object.expense_set.filter(
            status__gte=50, status__lt=60)
        context["formset"] = (
            self.formset if hasattr(self, "formset") else ExpenseFormSet(
                instance=self.get_object(),
                initial=[{"submitting_user": self.request.user}]
            )
        )
        return context

def view_tax_certificate(request):
    if request.user.is_season_pdsm or request.user.is_board:
        return redirect(config.finance_tax_certificate)
    raise PermissionDenied()
