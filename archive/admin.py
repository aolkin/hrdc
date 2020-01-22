from django.contrib import admin
from django.contrib import messages

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
                    "program_submitted", "poster_submitted", "photos_submitted",
                    "view")
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

    def view(self, obj):
        return format_html('<a href="{}">{}</a>'.format(
            obj.get_absolute_url(), "view page"))

@admin.register(ProductionPhoto)
class ProductionPhotoAdmin(admin.ModelAdmin):
    list_display = "show", "credit", "filename", "allow_in_publicity", "view"
    list_filter = ("allow_in_publicity",
                   "show__show__year", "show__show__season",)
    list_display_links = None

    def view(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>'.format(
            obj.img.url, "view"))


def enable_show_action(showadmin, request, queryset):
    count = queryset.count()
    results = ArchivalInfo.objects.bulk_create([
        ArchivalInfo(show=i) for i in queryset
        if not hasattr(i, "archival_info")
    ])
    if results:
        messages.success(
            request, 'Activated Archival Tool for {} shows.'.format(
                len(results)
            ))
    if len(results) < count:
        messages.warning(
            request,
            "{} shows had already been added to the Archival Tool".format(
                count - len(results)
            ))
enable_show_action.short_description = "Add selected shows to Archival Tool"
enable_show_action.permission = "archive.add_archivalinfo"
