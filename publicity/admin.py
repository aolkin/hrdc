from django.contrib import admin

from django.utils.html import format_html

from .models import *

class PerformanceDateAdmin(admin.TabularInline):
    model = PerformanceDate
    extra = 0

class ShowPersonAdmin(admin.StackedInline):
    model = ShowPerson
    extra = 0
    fields = (
        ("name", "year"),
        ("position", "type", "order"),
        ("email", "phone"),
    )

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
            "fields": ('blurb', 'runtime', 'contact_email',)
            # 'content_warning'),
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

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "title", "message", "note",
                       "start_date", "end_date", "submitted", "modified")
    fields = (
        ("user",),
        ("title",),
        ("message",),
        ("note",),
        ("start_date", "end_date"),
        ("submitted", "modified"),
        ("published",),
    )

    list_display = ("__str__", "user", "start_date", "end_date", "modified",
                    "published")
    list_editable = "published",
    list_filter = ("published", "start_date", "end_date", "submitted")

    def has_add_permission(self, arg):
        return False
