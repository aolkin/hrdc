from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete, post_delete

from dramaorg.models import Space, Season, Show

class Settlement(Season):
    locked = models.BooleanField(default=False, help_text="Prevent staff members of shows in this settlement from adding, modifying, or updating their budget, income, and expenses.")

    club_budget = models.DecimalField(
        decimal_places=2, max_digits=7, default=1000,
        help_text="A.R.T. grant towards organization expenses.")

    class Meta:
        ordering = "-year", "-season"

    def get_absolute_url(self):
        return reverse_lazy("finance:settlement", args=(self.pk,))

    def showstr(self):
        return ", ".join([str(i) for i in self.financeinfo_set.all()])
    showstr.short_description = "Shows"

    def __str__(self):
        return self.seasonstr()

    @property
    def total_revenue(self):
        return self.financeinfo_set.all().aggregate(
            models.Sum("box_office"))["box_office__sum"] or 0

    @property
    def total_royalties(self):
        return self.financeinfo_set.filter(ignore_royalties=False).aggregate(
            models.Sum("royalties"))["royalties__sum"] or 0

    @property
    def total_less(self):
        return self.total_revenue - self.total_royalties

    @property
    def total_less_capped(self):
        return max(self.total_revenue - self.total_royalties, 0)

    @property
    def revenue_royalties_shows(self):
        return self.financeinfo_set.exclude(
            box_office=0, royalties=0).order_by("show__space__order")

    @property
    def art_shows(self):
        return self.financeinfo_set.filter(
            income__status=92).order_by("show__space__order")

    @property
    def grant_shows(self):
        return self.financeinfo_set.exclude(
            income__status=92).order_by("show__space__order")

    @property
    def total_art_funded_balance(self):
        return sum([i.due_to_art for i in self.art_shows])

    @property
    def total_outside_funded_balance(self):
        return sum([i.p_card_total for i in self.grant_shows])

    @property
    def total_expenses_due(self):
        return (self.total_art_funded_balance +
                self.total_outside_funded_balance) * -1

    @property
    def total_due_hrdc(self):
        return (self.total_expenses_due + self.total_less_capped +
                self.club_budget)

class FinanceInfo(models.Model):
    show = models.OneToOneField(settings.SHOW_MODEL, on_delete=models.CASCADE,
                                related_name="finance_info")

    imported_budget = models.BooleanField(default=False)

    settlement = models.ForeignKey(Settlement, on_delete=models.SET_NULL,
                                   null=True, blank=True)
    royalties = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    box_office = models.DecimalField(decimal_places=2, max_digits=7, default=0,
                                     verbose_name="Box Office Revenue")
    ignore_royalties = models.BooleanField(
        default=False, verbose_name="Ignore Royalties Cost",
        help_text="If checked, don't count royalties against the revenue.")

    class Meta:
        verbose_name = "Finance-Enabled Show"

    @property
    def revenue_less_royalties(self):
        res = self.box_office
        if not self.ignore_royalties:
            res -= self.royalties
        return res

    @property
    def art_funded(self):
        return self.income_set.filter(status=92).exists()

    @property
    def locked(self):
        return self.settlement and self.settlement.locked

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
    def actual_expense_val(self):
        return self.budgetexpense_set.all().aggregate(
            models.Sum("actual"))["actual__sum"] or 0

    @property
    def actual_expenses(self):
        return "${:.2f}".format(self.actual_expense_val)

    @property
    def actual_bal(self):
        return self.received_income_val - self.actual_expense_val

    @property
    def actual_balance(self):
        return "${:.2f}".format(self.actual_bal)

    @property
    def confirmed_non_art_income(self):
        return self.income_set.filter(status=91).aggregate(
            models.Sum("received"))["received__sum"] or 0

    @property
    def art_income(self):
        return self.income_set.filter(status=92).aggregate(
            models.Sum("received"))["received__sum"] or 0

    @property
    def p_card_total(self):
        return self.expense_set.filter(purchased_using=0).exclude(
            status=0).aggregate(models.Sum("amount"))["amount__sum"] or 0

    @property
    def reimbursement_total(self):
        return self.expense_set.filter(purchased_using=1).exclude(
            status=0).aggregate(models.Sum("amount"))["amount__sum"] or 0

    @property
    def funding_less_reimbursements(self):
        return self.confirmed_non_art_income - self.reimbursement_total

    @property
    def art_remainder(self):
        return self.art_income - self.p_card_total

    @property
    def due_to_art(self):
        if self.art_remainder < 0:
            return self.art_remainder * -1
        if self.funding_less_reimbursements > 0:
            return min(self.funding_less_reimbursements,
                       self.p_card_total)
        return max(self.funding_less_reimbursements, -self.art_remainder)

    @property
    def unconfirmed_income(self):
        return self.income_set.filter(status__lt=90).exclude(status=11)

    @property
    def unconfirmed_expenses(self):
        return self.expense_set.filter(status=0)

    def __str__(self):
        return self.show.name

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
    actual = models.DecimalField(decimal_places=2, max_digits=7, default=0)

    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return "{} - {}".format(self.get_category_display(), self.name)

    class Meta:
        verbose_name = "Budgeted Expense Subcategory"
        verbose_name_plural = "Budgeted Expense Subcategories"
        ordering = "category", "pk"

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

    REIMBURSEMENT_OPTIONS = (
        (2, "Venmo"),
        (0, "Check - Pick up"),
        (1, "Check - Receive by Mail"),
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

    administrative_note = models.CharField(max_length=255, blank=True)

    # For Reimbursement Only
    purchaser_email = models.EmailField(blank=True)
    reimburse_via = models.PositiveSmallIntegerField(
        default=2, choices=REIMBURSEMENT_OPTIONS)
    mailing_address = models.TextField(blank=True)
    venmo_handle = models.CharField(max_length=20, blank=True)
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
            if self.reimburse_via == 1 and not self.mailing_address:
                raise ValidationError(
                    "Must provide mailing address to reimburse via mail.")
            if self.reimburse_via == 2 and not self.venmo_handle:
                raise ValidationError(
                    "Must provide Venmo handle to reimburse via Venmo.")
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
