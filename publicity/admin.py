from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.http import HttpResponse

import csv

from config import config

from rangefilter.filter import DateRangeFilter

from .models import *

class PerformanceDateAdmin(admin.TabularInline):
    model = PerformanceDate
    extra = 0

class ShowPersonAdmin(admin.StackedInline):
    model = ShowPerson
    extra = 0
    fields = (
        ("person"),
        ("position", "type", "order"),
    )
    autocomplete_fields = "person",

def export_wordpress(modeladmin, request, qs):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="hrdcapp_publicity_{}.csv"'.format(
        timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H%M%S"))
    writer = csv.writer(response)
    writer.writerow((
        "ID", "Title", "Content", "URL",
    ))
    for i in qs:
        writer.writerow((
            i.id,
            i.show.title,
            i.embed_code(False),
            i.show.slug,
        ))
        if not i.website_page:
            i.website_page = "{}{}/".format(
                config.publicity_website_page_prefix, i.show.slug)
            i.save()
    return response
export_wordpress.short_description = "Download selected shows for WordPress"

@admin.register(PublicityInfo)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('show', 'season', 'contact_email_link', "link")
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year', 'performancedate__performance')
    autocomplete_fields = ('show',)
    actions = export_wordpress,
    fieldsets = (
        ("", {
            "fields": ('show', "website_page", "embed_code")
        }),
        ("Publicity Header", {
            "fields": ('cover', 'credits',)
        }),
        ("Show Information", {
            "fields": ('blurb', 'runtime', 'contact_email', 'ticket_link',
                       'band_term',)
        })
    )

    inlines = [
        PerformanceDateAdmin,
        ShowPersonAdmin,
    ]

    def contact_email_link(self, obj):
        return format_html('<a href="mailto:{0}">{0}</a>', obj.contact_email)
    contact_email_link.short_description = "Show Email"

    def link(self, obj):
        return format_html('<a href="{0}" target="_blank">{0}</a>',
                           obj.website_page)
    link.short_description = "Website Link"

    def season(self, obj):
        return obj.show.seasonstr()

    def get_readonly_fields(self, modeladmin, obj):
        return (["show"] if obj and obj.show else []) + ["embed_code"]

@admin.register(PerformanceDate)
class PerformanceDateAdmin(admin.ModelAdmin):
    list_display = "show", "performance", "note"
    list_display_links = "performance",
    search_fields = ("show__show__title", "note")
    list_filter = (("performance", DateRangeFilter),
                   "show__show__season", "show__show__year")

    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = "name", "performance", "venue", "note",
    list_display_links = "name",
    search_fields = ("name", "note")
    list_filter = (("performance", DateRangeFilter), "venue")

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "title", "rendered_message", "note", "graphic",
                       "start_date", "end_date", "submitted", "modified")
    fields = (
        ("user",),
        ("title",),
        ("rendered_message",),
        ("graphic",),
        ("note",),
        ("start_date", "end_date"),
        ("submitted", "modified"),
        ("published",),
    )

    list_display = ("__str__", "user", "start_date", "end_date", "graphic_link",
                    "active", "published")
    list_editable = "published",
    list_filter = ("published", ("start_date", DateRangeFilter),
                   ("end_date", DateRangeFilter), "submitted")

    def has_add_permission(self, arg):
        return False

    def graphic_link(self, obj):
        return format_html('<a href="{0}" target="_blank">view</a>',
                           obj.graphic.url) if obj.graphic else None
    graphic_link.short_description = "Graphic"

def enable_show_action(showadmin, request, queryset):
    count = queryset.count()
    results = PublicityInfo.objects.bulk_create([
        PublicityInfo(show=i) for i in queryset
        if not hasattr(i, "publicity_info")
    ])
    if results:
        messages.success(
            request, 'Activated Publicity Manager for {} shows.'.format(
                len(results)
            ))
    if len(results) < count:
        messages.warning(
            request,
            "{} shows had already been added to the Publicity Manager".format(
                count - len(results)
            ))
enable_show_action.short_description = "Add selected shows to Publicity Manager"
enable_show_action.permission = "publicity.add_publicityinfo"
