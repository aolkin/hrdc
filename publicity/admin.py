from django.contrib import admin

from django.utils.html import format_html

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

@admin.register(PublicityInfo)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('show', 'season', 'contact_email_link', "link")
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year', 'performancedate__performance')
    autocomplete_fields = ('show',)
    fieldsets = (
        ("", {
            "fields": ('show', "website_page",)
        }),
        ("Publicity Header", {
            "fields": ('credits',)
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
        return ("show",) if obj and obj.show else []

@admin.register(PerformanceDate)
class PerformanceDateAdmin(admin.ModelAdmin):
    list_display = "show", "performance", "note"
    list_display_links = "performance",
    search_fields = ("show__show__title", "note")
    list_filter = (("performance", DateRangeFilter),
                   "show__show__season", "show__show__year")
    fields = ("show",), ("performance", "note")

    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []
    
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "title", "message", "note", "graphic",
                       "start_date", "end_date", "submitted", "modified")
    fields = (
        ("user",),
        ("title",),
        ("message",),
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
