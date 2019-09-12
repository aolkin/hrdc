from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from django.urls import reverse_lazy

from dramaorg.models import Space, Season, Show

class FinanceInfo(models.Model):
    show = models.OneToOneField(settings.SHOW_MODEL, on_delete=models.CASCADE,
                                related_name="finance_info")

    class Meta:
        verbose_name = "Finance-Enabled Show"

    @property
    def requested_income_val(self):
        return self.income_set.exclude(status=11).aggregate(
            models.Sum("requested"))["requested__sum"] or 0

    @property
    def requested_income(self):
        sum = self.requested_income_val
        return "${:.2f}".format(sum) if sum else sum

    @property
    def received_income_val(self):
        return self.income_set.filter(status__gt=50).aggregate(
            models.Sum("received"))["received__sum"] or 0

    @property
    def received_income(self):
        sum = self.received_income_val
        return "${:.2f}".format(sum) if sum else sum

    @property
    def confirmed_income_val(self):
        return self.income_set.filter(status__gte=90).aggregate(
            models.Sum("received"))["received__sum"] or 0

    @property
    def confirmed_income(self):
        sum = self.confirmed_income_val
        return "${:.2f}".format(sum) if sum else sum

    @property
    def administrative_budget(self):
        return self.budgetexpense_set.filter(
            category=BudgetExpense.BUDGET_CATEGORIES[0][0])

    @property
    def production_budget(self):
        return self.budgetexpense_set.filter(
            category=BudgetExpense.BUDGET_CATEGORIES[1][0])

    @property
    def other_budget(self):
        return self.budgetexpense_set.filter(
            category=BudgetExpense.BUDGET_CATEGORIES[2][0])
    
    def __str__(self):
        return str(self.show)

    def get_absolute_url(self):
        return reverse_lazy("finance:budget", args=(self.pk,))

class Income(models.Model):
    INCOME_STATUSES = (
        (0, "Planned"),
        (1, "Applied"),
        (51, "Received"),
        (
            "Administrative Statuses", (
                (91, "Confirmed (Funds Received)"),
                (92, "A.R.T. Grant"),
            )
        ),
        (11, "Rejected"),
    )
    
    show = models.ForeignKey(FinanceInfo, on_delete=models.CASCADE,
                             db_index=True)
    name = models.CharField(max_length=40)

    requested = models.DecimalField(decimal_places=2, max_digits=7)
    received = models.DecimalField(decimal_places=2, max_digits=7,
                                          null=True, blank=True)

    status = models.PositiveSmallIntegerField(choices=INCOME_STATUSES,
                                              default=0)

    def clean(self):
        if self.status > 50:
            if self.received is None:
                raise ValidationError("Must provide amount received.")
        else:
            if self.received is not None:
                raise ValidationError(
                    "Cannot provide amount received before grant is received.")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Grant/Income"
        verbose_name_plural = "Grants and Income"
        ordering = "-status",

class BudgetExpense(models.Model):
    BUDGET_CATEGORIES = (
        (10, "Administrative"),
        (20, "Production"),
        (50, "Other"),
    )
    
    show = models.ForeignKey(FinanceInfo, on_delete=models.CASCADE,
                             db_index=True)

    category = models.PositiveSmallIntegerField(choices=BUDGET_CATEGORIES,
                                                default=10)
    name = models.CharField(max_length=80)
    
    estimate = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    reported = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    actual = models.DecimalField(decimal_places=2, max_digits=7, default=0)

    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Budget Expense Item"
