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
                ("venue",),
                ("live",),
                ("contact_email",),
                ("managers", "readers"),
            ),
        }),
        ("Due Dates", {
            "fields": (("prelim_due", "full_due",),),
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
    filter_horizontal = "questions",
    autocomplete_fields = "managers", "readers",
    inlines = ResidencyInline, DefaultBudgetInline

class StaffInline(admin.TabularInline):
    model = StaffMember
    extra = 1

class SlotPrefInline(admin.TabularInline):
    model = SlotPreference
    extra = 1

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("show", "venuestr", "season",
                    "pre_submitted", "full_submitted")
    list_filter = ("venues__venue", "show__year", "show__season",
                   "pre_submitted", "full_submitted")
    readonly_fields = "pre_submitted", "full_submitted"
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
