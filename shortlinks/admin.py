from django.contrib import admin

from .models import Link

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ("url", "destination", "link_markup")
    list_filter = ("created", "updated")

    readonly_fields = ("created", "updated", "link")
