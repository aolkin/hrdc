from django.contrib import admin

from django.utils.html import format_html

import dramaorg.models as org
from .models import *

class ExtraFileInline(admin.TabularInline):
    model = ExtraFile
    extra = 0

class ProductionPhotoInline(admin.TabularInline):
    model = ProductionPhoto
    extra = 0

@admin.register(ArchivalInfo)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('show', 'season',)
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year',)
    fieldsets = (
        ("", {
            "fields": ('show',),
        }),
        ("Materials", {
            "fields": ("poster", "program"),
        }),
    )

    inlines = (ExtraFileInline, ProductionPhotoInline)
    
    def season(self, obj):
        return obj.show.seasonstr()
    
    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []

