from django.contrib import admin
from django import forms
from django.utils.html import mark_safe, format_html
from django.contrib import messages

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
    search_fields = "venue__name", "venue__nickname", "season", "year"
    inlines = ResidencyInline, DefaultBudgetInline
    save_as = True

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
    save_as = True

class StaffInline(admin.TabularInline):
    model = StaffMember
    extra = 0
    fields = ("person", "role", "other_role", "role_name", "signed_on",)
    autocomplete_fields = ("person",)
    readonly_fields = ("signed_on", "role_name")

class SlotPrefInline(admin.TabularInline):
    model = SlotPreference
    extra = 0
    fields = ("ordering", "venue", "start_date", "end_date", "weeks")
    readonly_fields = ("venue", "start_date", "end_date", "weeks")

def unsubmit_apps(modeladmin, request, qs):
    qs = qs.exclude(submitted=None)
    qs.update(submitted=None)
    messages.success(request, "Un-submitted {} applications.".format(qs.count()))
unsubmit_apps.short_description = "Un-submit selected applications"

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("show", "venuestr", "season", "submitted")
    list_filter = ("venues__venue", "show__year", "show__season", "submitted")
    inlines = StaffInline, SlotPrefInline
    fieldsets = (
        ("", {
            "fields": (
                ("show",),
                ("creator_credit",),
                ("prod_type"),
                ("affiliation",),
                ("venues",),
                ("cast_breakdown",),
                ("band_size"),
                ("script",),
                ("contact_executive_staff",),
                ("length_description",),
                ("submitted", "created"),
            ),
        }),
    )
    readonly_fields = ("created", "prod_type", "creator_credit", "affiliation",
                       "contact_executive_staff", "submitted", "show",)
    autocomplete_fields = ("venues",)
    actions = [unsubmit_apps]

    def prod_type(self, obj):
        return obj.show and obj.show.get_prod_type_display()
    prod_type.short_description = Show._meta.get_field("prod_type").verbose_name
    def creator_credit(self, obj):
        return obj.show and obj.show.creator_credit
    creator_credit.short_description = Show._meta.get_field(
        "creator_credit").verbose_name
    def affiliation(self, obj):
        return obj.show and obj.show.affiliation
    affiliation.short_description = Show._meta.get_field(
        "affiliation").verbose_name

    def contact_executive_staff(self, obj):
        return mark_safe(", ".join([format_html(
            '<a href="mailto:{0}">{1}</a>', i.email,
            "{} <{}>".format(i.get_full_name(False), i.email))
                                    for i in obj.show.staff.all()]))


@admin.register(SeasonStaffMeta)
class SeasonStaffAdmin(admin.ModelAdmin):
    search_fields = ("user__first_name", "user__last_name", "user__email")

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
