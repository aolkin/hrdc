from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, post_delete

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
        return "${:.2f}".format(self.requested_income_val)

    @property
    def received_income_val(self):
        return self.income_set.filter(status__gt=50).aggregate(
            models.Sum("received"))["received__sum"] or 0

    @property
    def received_income(self):
        return "${:.2f}".format(self.received_income_val)

    @property
    def confirmed_income_val(self):
        return self.income_set.filter(status__gte=90).aggregate(
            models.Sum("received"))["received__sum"] or 0

    @property
    def confirmed_income(self):
        return "${:.2f}".format(self.confirmed_income_val)

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
    
    @property
    def expected_bal(self):
        expenses = self.budgetexpense_set.all().aggregate(
            models.Sum("estimate"))["estimate__sum"] or 0
        return self.requested_income_val - expenses

    @property
    def expected_balance(self):
        return "${:.2f}".format(self.expected_bal)

    @property
    def reported_bal(self):
        expenses = self.budgetexpense_set.all().aggregate(
            models.Sum("reported"))["reported__sum"] or 0
        return self.received_income_val - expenses

    @property
    def reported_balance(self):
        return "${:.2f}".format(self.reported_bal)

    @property
    def actual_expense_val(self):
        return self.budgetexpense_set.all().aggregate(
            models.Sum("actual"))["actual__sum"] or 0
    
    @property
    def actual_expenses(self):
        return "${:.2f}".format(self.actual_expense_val)
    
    @property
    def actual_bal(self):
        return self.confirmed_income_val - self.actual_expense_val

    @property
    def actual_balance(self):
        return "${:.2f}".format(self.actual_bal)

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
    
    show = models.ForeignKey(FinanceInfo, on_delete=models.PROTECT,
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
        return "{} - {}".format(self.get_category_display(), self.name)

    class Meta:
        verbose_name = "Budgeted Expense Subcategory"
        verbose_name_plural = "Budgeted Expense Subcategories"
        ordering = "category",

class Expense(models.Model):
    EXPENSE_STATUSES = (
        (0, "Pending"),
        (
            "P-Card", (
                (52, "Confirmed"),
            )
        ),
        (
            "Reimbursement", (
                (61, "Requested"),
                (62, "Processed"),
            )
        ),
    )

    FUNDS_SOURCES = (
        (0, "P-Card"),
        (1, "Personal Funds")
    )

    def upload_destination(instance, filename):
        return "finance/receipts/{}/{}".format(instance.show.show.slug,
                                               filename)
    
    show = models.ForeignKey(FinanceInfo, on_delete=models.PROTECT,
                             db_index=True)

    status = models.PositiveSmallIntegerField(choices=EXPENSE_STATUSES,
                                              default=0)
    purchased_using = models.PositiveSmallIntegerField(choices=FUNDS_SOURCES,
                                                       default=0)

    last_updated = models.DateTimeField(auto_now=True)

    date_purchased = models.DateField()
    amount = models.DecimalField(decimal_places=2, max_digits=7)
    receipt = models.FileField(upload_to=upload_destination, blank=True)

    item = models.CharField(max_length=255)
    subcategory = models.ForeignKey(BudgetExpense, on_delete=models.PROTECT)
    purchaser_name = models.CharField(max_length=255)

    submitting_user = models.ForeignKey(get_user_model(), null=True,
                                        on_delete=models.SET_NULL)
    
    # For Reimbursement Only
    purchaser_email = models.EmailField(blank=True)
    reimburse_via_mail = models.BooleanField(
        default=False,
        help_text="Does the reimbursement check need to be mailed?"
    )
    mailing_address = models.TextField(blank=True)
    check_number = models.PositiveIntegerField(blank=True, null=True,
                                               verbose_name="Check #")

    class Meta:
        ordering = "date_purchased",
    
    def category(self):
        return self.subcategory.get_category_display()
    category.admin_order_field = "subcategory__category"

    def sub_category(self):
        return self.subcategory.name
    sub_category.admin_order_field = "subcategory__name"
    sub_category.short_description = "Subcategory"

    @property
    def amount_display(self):
        return "${:.2f}".format(self.amount)
    
    def __str__(self):
        return ("{} - ${:.2f}".format(self.item, self.amount)
                if self.amount else self.item)


    def clean(self):
        if self.show_id and self.subcategory_id and (
                self.subcategory.show_id != self.show_id):
            raise ValidationError(
                "Selected expense category does not belong to selected show.")
        if self.status > 60:
            if not self.purchaser_email:
                raise ValidationError(
                    "Must provide purchaser email for reimbursement.")
            if self.reimburse_via_mail and not self.mailing_address:
                raise ValidationError(
                    "Must provide mailing address to reimburse via mail.")
            if self.purchased_using != 1:
                raise ValidationError(
                    "Reimbursement statuses can only be selected for purchases "
                    "made with personal funds.")
            if not self.receipt:
                raise ValidationError(
                    "Must provide receipt for reimbursement.")
        if self.purchased_using != 0 and (
                self.status > 50 and self.status < 60):
            raise ValidationError(
                "P-card statuses can only be selected for purchases "
                "made via a p-card.")

@receiver(post_save)
def update_actual(sender, instance, created, raw, **kwargs):
    if sender == Expense:
        budget_item = instance.subcategory
        budget_item.actual = round(budget_item.expense_set.all().aggregate(
            models.Sum("amount"))["amount__sum"] or 0, 2)
        budget_item.save()

@receiver(post_delete)
def update_actual_on_delete(sender, instance, **kwargs):
    if sender == Expense:
        budget_item = instance.subcategory
        budget_item.actual = round(budget_item.expense_set.all().aggregate(
            models.Sum("amount"))["amount__sum"] or 0, 2)
        budget_item.save()
