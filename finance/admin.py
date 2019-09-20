from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html

import csv, re, zipfile

from .models import *

class IncomeInline(admin.TabularInline):
    model = Income
    extra = 0
    fields = ("name", "requested", "received", "status")
    readonly_fields = "name", "requested",
    show_change_link = True
    can_delete = False
    def has_add_permission(self, request, obj):
        return False

class BudgetExpenseInline(admin.StackedInline):
    model = BudgetExpense
    extra = 0
    fields = (
        ("category", "name", "estimate",),
        ("reported", "actual", "notes",)
    )
    readonly_fields = "actual",

class EditableExpenseInline(admin.StackedInline):
    model = Expense
    extra = 0
    autocomplete_fields = ("subcategory", "submitting_user")
    fieldsets = (
        (None, {
            "fields": (
                ("status", "purchased_using", "amount",),
                ("subcategory", "item", "submitting_user",),
                ("purchaser_name", "date_purchased", "receipt"),
            )
        }),
        ("Reimbursement Options", {
            "fields": (
                ("purchaser_email", "reimburse_via_mail",),
                ("mailing_address",),
            ),
            "classes": ("collapse",),
        })
    )

class LimitedExpenseInline(admin.TabularInline):
    model = Expense
    can_delete = False
    show_change_link = True
    def has_add_permission(self, request, obj):
        return False
    
class PCardExpenseInline(LimitedExpenseInline):
    fields = ("subcategory", "item", "amount", "status", "purchaser_name",
              "date_purchased")
    readonly_fields = ("subcategory", "item", "purchaser_name",
                       "date_purchased",)
    verbose_name_plural = "P-Card Expenses"
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(purchased_using=0)
    
class ReimburseableExpenseInline(LimitedExpenseInline):
    fields = ("subcategory", "item", "amount", "status", "purchaser_name",
              "date_purchased")
    readonly_fields = ("subcategory", "item", "purchaser_name",
                       "date_purchased",)
    verbose_name_plural = "Reimburseable Expenses"
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(purchased_using=1)

SAVE_WARNING = """
<p style="background-color: darkred; color: white; border-radius: 0.4em; padding: 0.8em;">
DANGER: Saving this page will overwrite any concurrent edits made outside
of this page.
</p>
<div id="save-warning" style="position: fixed; width: 100%; height: 100%; top: 0; left: 0; display: none; background-color: darkred; color: white; font-weight: bold; text-align: center; font-size: 1.5em; z-index: 99999; padding-top: 40%;">
DANGER: Saving this page will overwrite any concurrent edits made outside
of this page. Please refresh before continuing (your changes will be lost).
</div>
<script>
setTimeout(() => {
   django.jQuery("#save-warning").fadeIn(1000);
}, 1000 * 60 * 5);
</script>
""".strip().replace("\n", " ")

@admin.register(FinanceInfo)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('show', 'season', "income_count",
                    "requested_income", "view_budget")
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year',)
    autocomplete_fields = ('show',)
    fieldsets = (
        ("", {
            "fields": ("show",),
            "description": SAVE_WARNING,
        }),
    )

    inlines = (IncomeInline, PCardExpenseInline, ReimburseableExpenseInline)

    view_budget_text = "View budget"
    
    def get_readonly_fields(self, modeladmin, obj):
        return ("show", "view_budget") if obj and obj.show else ("view_budget",)
    
    def season(self, obj):
        return obj.show.seasonstr()

    def income_count(self, obj):
        return obj.income_set.count()
    income_count.short_description = "# of Grants"

    def view_budget(self, obj):
        return format_html('<a href="{}">{}</a>'.format(
            obj.get_absolute_url(), self.view_budget_text))
    
def export_income(modeladmin, request, qs):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="hrdcapp_income_{}.csv"'.format(
        timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H%M%S"))
    writer = csv.writer(response)
    writer.writerow((
        "Show", "Grant", "Requested", "Received", "Status",
    ))
    for i in qs:
        writer.writerow((
            str(i.show),
            i.name,
            i.requested,
            i.received,
            i.get_status_display()
        ))
    return response
export_income.short_description = "Export selected to csv"

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ("show", "name", "requested", "received",
                    "status")
    list_filter = ("status", "show__show__season", "show__show__year")
    search_fields = ("show__show__title", "name")
    autocomplete_fields = "show",
    list_display_links = None
    list_editable = "received", "status"
    actions = export_income,

    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []

@admin.register(BudgetExpense)
class BudgetExpenseAdmin(admin.ModelAdmin):
    list_display = ("show", "category", "name",
                    "estimate", "reported", "actual")
    list_filter = ("category",
                   "show__show__season", "show__show__year")
    autocomplete_fields = "show",
    #list_editable = ("estimate", "reported",)
    search_fields = ("show__show__title", "category", "name")
    list_display_links = "name",

    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []

    def get_search_results(self, request, queryset, search_term):
        filter_show = request.META.get("HTTP_X_EXPENSE_SUBCATEGORY_SHOW", "")
        if filter_show:
            queryset = queryset.filter(show=filter_show)
        else:
            referer = request.META.get("HTTP_REFERER", "")
            financeinfo_match = re.search(r'/financeinfo/(\d+)/', referer)
            if financeinfo_match:
                queryset = queryset.filter(show=financeinfo_match.group(1))
        return super().get_search_results(request, queryset, search_term)

def export_expense(modeladmin, request, qs):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="hrdcapp_expenses_{}.csv"'.format(
        timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H%M%S"))
    writer = csv.writer(response)
    writer.writerow((
        "Show", "Category", "Subcategory", "Item", "Amount", "Purchaser Name",
        "Status", "Purchased Via", "Date Purchased", "Receipt",
        "Purchaser Email", "Reimburse via Mail", "Mailing Address", "Check #",
    ))
    for i in qs:
        writer.writerow((
            str(i.show),
            i.category(),
            i.sub_category(),
            i.item,
            i.amount_display,
            i.purchaser_name,
            i.get_status_display(),
            i.get_purchased_using_display(),
            i.date_purchased,
            i.receipt.url if i.receipt and i.receipt.url.startswith(
                "http") else i.receipt,
            i.purchaser_email,
            i.reimburse_via_mail,
            i.mailing_address,
            i.check_number,
        ))
    return response
export_expense.short_description = "Export selected expenses to csv"

def export_receipt_zip(modeladmin, request, qs):
    response = HttpResponse(content_type="application/zip")
    response['Content-Disposition'] = 'attachment; filename="hrdcapp_receipts_{}.zip"'.format(
        timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H%M%S"))
    zipfd = zipfile.ZipFile(response, "w")
    for expense in qs:
        if expense.receipt:
            zipfd.writestr("hrdcapp_receipts/" +
                           expense.receipt.name.rpartition("receipts")[2],
                           expense.receipt.read())
    zipfd.close()
    return response
export_receipt_zip.short_description = "Download zip of selected receipts"

def mark_confirmed(modeladmin, request, qs):
    if qs.exclude(purchased_using=0).exists():
        messages.warning(request,
                         "Not marking reimburseable purchases as confirmed.")
    qs.filter(purchased_using=0).update(status=52)
    messages.success(request, "Marked P-Card purchases as confirmed.")
mark_confirmed.short_description = "Confirm selected P-Card purchases"

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("show", "category", "sub_category", "item",
                    "get_amount", "status",
                    "purchased_using", "purchaser_name", "date_purchased",
                    "check_number", "view_receipt",)
    list_filter = ("status", "purchased_using", "subcategory__category",
                   "show__show__season", "show__show__year",
                   "last_updated",)
    search_fields = ("show__show__title", "subcategory__name", "item",
                     "check_number")
    list_display_links = "item",
    list_editable = "status", "check_number"
    autocomplete_fields = "show", "submitting_user", "subcategory"
    actions = mark_confirmed, export_expense, export_receipt_zip
              
    fieldsets = (
        (None, {
            "fields": (
                ("show",),
                ("status", "purchased_using", "submitting_user",),
            )
        }),
        ("Expense Details", {
            "fields": (
                ("subcategory", "item",),
                ("amount", "receipt",),
                ("purchaser_name", "date_purchased",),
            )
        }),
        ("Reimbursement Data", {
            "fields": (
                ("purchaser_email", "check_number",),
                ("reimburse_via_mail", "mailing_address",),
            ),
        })
    )

    class Media:
        js = ('finance/expense_admin.js',)

    def view_receipt(self, obj):
        return format_html(
            '<a href="{}" target="_blank">view receipt</a>'.format(
                obj.receipt.url)) if obj.receipt else "-"

    def get_amount(self, obj):
        return obj.amount_display
    get_amount.short_description = "Amount"
    get_amount.admin_order_field = "amount"
