from django.contrib import admin

from .models import *

@admin.register(FinanceInfo)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('show', 'season',)
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year',)
    autocomplete_fields = ('show',)
    fieldsets = (
        ("", {
            "fields": ('show',)
        }),
    )
    
    def season(self, obj):
        return obj.show.seasonstr()
