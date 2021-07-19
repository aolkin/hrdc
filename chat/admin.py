from django.contrib import admin

from .models import *

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    readonly_fields = "timestamp", "room", "user", "nickname", "message"

    list_display = "timestamp", "room", "user", "nickname", "message"
    list_filter = "room",

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
