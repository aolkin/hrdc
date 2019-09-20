from django.contrib import admin

from django.utils.html import format_html

import dramaorg.models as org
from .models import *

"""class PerformanceDateAdmin(admin.TabularInline):
    model = PerformanceDate
    extra = 0
"""
@admin.register(ArchivalInfo)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('show', 'season',)
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year',)
    fieldsets = (
        ("", {
            "fields": ('show',)
        }),
    )
    
    def season(self, obj):
        return obj.show.seasonstr()
    
    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []

