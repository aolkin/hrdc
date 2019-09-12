from django.contrib import admin

from .models import *

class IncomeAdmin(admin.TabularInline):
    model = Income
    extra = 1
    fields = (
        ("name", "status"),
        ("amount_requested", "amount_received"),
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

    inlines = (IncomeAdmin,)
    
    def season(self, obj):
        return obj.show.seasonstr()

    def income_count(self, obj):
        return obj.income_set.count()
    income_count.short_description = "# of Grants"
