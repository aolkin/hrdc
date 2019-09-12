from django.contrib import admin

from .models import *

class PerformanceDateAdmin(admin.StackedInline):
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
    list_display = ('show', 'season', 'contact_email')
    search_fields = ('show__title',)
    list_filter = ('show__season', 'show__year',)
    autocomplete_fields = ('show',)
    fieldsets = (
        ("", {
            "fields": ('show', 'contact_email')
        }),
        ("Publicity Header", {
            "fields": ('credits',)
        }),
        ("Show Information", {
            "fields": ('blurb', 'runtime',) # 'content_warning'),
        })
    )
    
    inlines = [
        PerformanceDateAdmin,
        ShowPersonAdmin,
    ]
    
    def contact_email_link(self, obj):
        return format_html('<a href="mailto:{0}">{0}</a>', obj.contact_email)
    contact_email_link.short_description = "Show Email"
    
    def season(self, obj):
        return obj.show.seasonstr()

    def get_readonly_fields(self, modeladmin, obj):
        return ("show",) if obj and obj.show else []
