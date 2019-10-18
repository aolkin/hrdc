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
    list_display = ('show', 'season',
                    "program_submitted", "poster_submitted", "photos_submitted")
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year')
    fieldsets = (
        ("", {
            "fields": ('show',),
        }),
        ("Materials", {
            "fields": ("poster", "program"),
        }),
    )
    autocomplete_fields = "show",
    inlines = (ExtraFileInline, ProductionPhotoInline)
    
    def season(self, obj):
        return obj.show.seasonstr()
    
    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []

    def program_submitted(self, obj):
        return bool(obj.program)
    program_submitted.short_description = "Program"
    program_submitted.admin_order_field = "program"
    program_submitted.boolean = True

    def poster_submitted(self, obj):
        return bool(obj.poster)
    poster_submitted.short_description = "Poster"
    poster_submitted.admin_order_field = "poster"
    poster_submitted.boolean = True

    def photos_submitted(self, obj):
        return obj.productionphoto_set.count()
    photos_submitted.short_description = "Photos"
