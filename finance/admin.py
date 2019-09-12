from django.contrib import admin
from django.http import HttpResponse

import csv, re

from .models import *

class IncomeInline(admin.TabularInline):
    model = Income
    extra = 0
    fields = (
        ("name", "status"),
        ("requested", "received"),
    )

class BudgetExpenseInline(admin.StackedInline):
    model = BudgetExpense
    extra = 0
    fields = (
        ("category", "name", "estimate",),
        ("reported", "actual", "notes",)
    )
    readonly_fields = "actual",

class ExpenseInline(admin.StackedInline):
    model = Expense
    extra = 0
    autocomplete_fields = ("subcategory", "submitting_user")
    fieldsets = (
        (None, {
            "fields": (
                ("status", "purchased_using", "submitting_user",),
                ("subcategory", "item",),
                ("purchaser_name", "date_purchased",),
                ("amount", "receipt"),
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

@admin.register(FinanceInfo)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('show', 'season', "income_count",
                    "requested_income", "confirmed_income")
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year',)
    autocomplete_fields = ('show',)
    fieldsets = (
        ("", {
            "fields": ('show',)
        }),
    )

    inlines = (IncomeInline, BudgetExpenseInline, ExpenseInline)

    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []
    
    def season(self, obj):
        return obj.show.seasonstr()

    def income_count(self, obj):
        return obj.income_set.count()
    income_count.short_description = "# of Grants"

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
    list_display_links = None
    list_editable = "requested", "received", "status"

    readonly_fields = "show",
    actions = export_income,

@admin.register(BudgetExpense)
class BudgetExpenseAdmin(admin.ModelAdmin):
    list_display = ("show", "category", "name",
                    "estimate", "reported", "actual")
    list_filter = ("category",
                   "show__show__season", "show__show__year")
    list_editable = ("estimate", "reported",)
    search_fields = ("show__show__title", "category", "name")
    list_display_links = None

    readonly_fields = "show",

    def get_search_results(self, request, queryset, search_term):
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
        "Purchaser Email", "Reimburse via Mail", "Mailing Address"
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
            i.receipt,
            i.purchaser_email,
            i.reimburse_via_mail,
            i.mailing_address
        ))
    return response
export_expense.short_description = "Export selected to csv"

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("show", "category", "sub_category", "item",
                    "get_amount", "status",
                    "purchased_using", "purchaser_name", "date_purchased")
    list_filter = ("status", "purchased_using", "subcategory__category",
                   "show__show__season", "show__show__year")
    search_fields = ("show__show__title", "subcategory__name", "item")
    list_display_links = "item",
    list_editable = "status",
    autocomplete_fields = "show", "submitting_user", "subcategory"
    actions = export_expense,

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
        ("Reimbursement Options", {
            "fields": (
                ("purchaser_email", "reimburse_via_mail",),
                ("mailing_address",),
            ),
            "classes": ("collapse",),
        })
    )

    def get_amount(self, obj):
        return obj.amount_display
    get_amount.short_description = "Amount"
    get_amount.admin_order_field = "amount"
    
    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []
