from django.contrib import admin
from django import forms

from .models import *

class ResidencyInline(admin.TabularInline):
    model = AvailableResidency
    extra = 0

class DefaultBudgetInline(admin.TabularInline):
    model = DefaultBudgetLine
    extra = 0

@admin.register(VenueApp)
class VenueAdmin(admin.ModelAdmin):
    fieldsets = (
        ("", {
            "fields": (
                ("year", "season",),
                ("venue", "due"),
                ("live",),
                ("contact_email",),
                ("managers", "readers"),
            ),
        }),
        ("General Questions", {
            "fields": ("questions",),
            "classes": ("collapse",),
        }),
        ("Instructions and Notes", {
            "fields": ("residency_instr", "budget_instr",),
            "classes": ("collapse",),
        }),
    )
    list_display = ("__str__", "live", "seasonstr",
                    "due", "contact_email")
    list_filter = "live", "year", "season", "due"
    filter_horizontal = "questions",
    autocomplete_fields = "managers", "readers",
    inlines = ResidencyInline, DefaultBudgetInline

@admin.register(OldStyleApp)
class OldStyleAppAdmin(admin.ModelAdmin):
    fieldsets = (
        ("", {
            "fields": (
                ("year", "season",),
                ("venue", "due"),
                ("live",),
                ("url", "download"),
            ),
        }),
    )
    list_display = ("__str__", "live", "seasonstr", "due",)
    list_filter = "live", "year", "season", "due"

class StaffInline(admin.TabularInline):
    model = StaffMember
    extra = 1
    fields = ("person", "role", "other_role", "signed_on",)

class SlotPrefInline(admin.TabularInline):
    model = SlotPreference
    extra = 1

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("show", "venuestr", "season", "submitted")
    list_filter = ("venues__venue", "show__year", "show__season", "submitted")
    readonly_fields = "submitted",
    inlines = StaffInline, SlotPrefInline

@admin.register(SeasonStaffMeta)
class SeasonStaffAdmin(admin.ModelAdmin):
    pass

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass

class QuestionInline(admin.TabularInline):
    model = RoleQuestion
    extra = 1

@admin.register(StaffRole)
class RoleAdmin(admin.ModelAdmin):
    fields = (
        ("category", "name"),
        ("statement_length", "accepts_attachment"),
        ("archived",),
    )
    list_display = ("__str__", "category", "statement_length",
                    "accepts_attachment", "archived")
    list_filter = "category", "archived"
    inlines = QuestionInline,
