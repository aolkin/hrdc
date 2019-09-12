from django.contrib import admin
from django.http import HttpResponse

import csv

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

    inlines = (IncomeInline, BudgetExpenseInline)

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
