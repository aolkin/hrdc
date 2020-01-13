from django.contrib import admin

from .models import Link

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ("__str__", "destination", "link_markup", "owner")
    list_filter = ("created", "updated")
    autocomplete_fields = "owner",
    readonly_fields = ("created", "updated", "link")
    search_fields = ("link", "owner__first_name", "owner__last_name")
