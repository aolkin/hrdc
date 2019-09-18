from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group, Permission
from django.contrib import messages

from django.http import HttpResponse
from django.shortcuts import redirect

import csv

from django import forms
from django.conf import settings

from .models import *

admin.site.site_title = settings.ADMIN_SITE_TITLE
admin.site.site_header = settings.ADMIN_SITE_TITLE

class UserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

def generate_tokens(modeladmin, request, queryset):
    for obj in queryset:
        obj.new_token(expiring=True)
        
def clear_tokens(modeladmin, request, queryset):
    for obj in queryset:
        obj.clear_token()

def export_users(modeladmin, request, qs):
    response = HttpResponse(content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="hrdcapp_users_{}.csv"'.format(
        timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H%M%S"))
    writer = csv.writer(response)
    writer.writerow((
        "Name", "Email", "Phone", "Affiliation", "Year", "PGPs",
    ))
    for i in qs:
        writer.writerow((
            i.get_full_name(False),
            i.email,
            i.phone,
            i.affiliation,
            i.year,
            i.pgps
        ))
    return response
export_users.short_description = "Download spreadsheet of selected users"

def set_to_default_affiliation(modeladmin, request, qs):
    qs.update(affiliation=settings.DEFAULT_AFFILIATION)
    messages.success(request, 'Set users\' affiliation to "{}".'.format(
        settings.DEFAULT_AFFILIATION))
    return redirect("admin:dramaorg_user_changelist")
set_to_default_affiliation.short_description = 'Set affiliation to "{}"'.format(
    settings.DEFAULT_AFFILIATION)

class ActiveFilter(admin.SimpleListFilter):
    title = "active status"
    parameter_name = "pw_active"

    def lookups(self, request, model_admin):
        return (
            ("disabled", "Disabled"),
            ("enabled", "Enabled but password-less"),
            ("active", "Has set password"),
            ("social", "Connected with OAuth2"),
        )

    def queryset(self, request, queryset):
        if self.value() == "disabled":
            return queryset.filter(is_active=False)
        if self.value() == "enabled":
            return queryset.filter(is_active=True, password="")
        if self.value() == "active":
            return queryset.filter(is_active=True).exclude(password="")
        if self.value() == "social":
            return queryset.filter(is_active=True, social_auth__isnull=False)
        
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': (('first_name', 'last_name'),
                           ('pgps', 'gender_pref'),
                           ('affiliation', 'year'),
                           ('suspended_until',))}),
        ('Contact Info', {'fields': ('email', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'admin_access',
                                    'is_superuser', 'groups'),
                         'classes': ('collapse',)}),
        ('Information', {'fields': ('last_login', 'date_joined', 'password')}),
    )
    staff_fieldsets = (
        (None, {'fields': (('first_name', 'last_name'),
                           ('pgps', 'gender_pref'),
                           ('affiliation', 'year'), 'email', 'phone',
                           'suspended_until', 'groups', 'is_active',
                           'password')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email',)
        }),
    )
    add_form = UserCreationForm
    add_form_template = "dramaadmin/invite_user.html"
    list_display = ('__str__', 'email', 'phone', 'affiliationyear',
                    'get_pdsm', 'get_season_pdsm', 'has_password', 'get_social')
    list_filter = (ActiveFilter,'is_superuser', 'affiliation', 'year',
                   'suspended_until', 'last_login', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name',)
    readonly_fields = ('last_login', 'date_joined')
    staff_readonly = ('email', 'first_name', 'last_name',
                      'pgps', 'gender_pref', 'phone', 'groups',
                      'affiliation', 'year', 'is_active', 'suspended_until')
    actions = [export_users, set_to_default_affiliation] + (
        [generate_tokens, clear_tokens] if settings.DEBUG else [])
    ordering = ('date_joined',)
    save_as_continue = True

    def get_initialized(self, obj):
        return obj.is_initialized
    get_initialized.boolean = True
    get_initialized.short_description = "Profile"

    def get_board(self, obj):
        return obj.is_board
    get_board.boolean = True
    get_board.short_description = "Board"

    def get_pdsm(self, obj):
        return obj.is_pdsm
    get_pdsm.boolean = True
    get_pdsm.short_description = "PDSM"

    def get_season_pdsm(self, obj):
        return obj.is_season_pdsm
    get_season_pdsm.boolean = True
    get_season_pdsm.short_description = "Current"

    def get_active(self, obj):
        return obj.is_active
    get_active.boolean = True
    get_active.short_description = "Enabled"

    def get_social(self, obj):
        return obj.social_auth.exists()
    get_social.boolean = True
    get_social.short_description = "OAuth"
    
    def has_password(self, obj):
        if obj.is_active is False:
            return False
        elif obj.password is None or obj.password == "":
            return None
        elif obj.source == "social":
            return obj.is_active
        else:
            return obj.is_active and obj.has_usable_password()
    has_password.boolean = True
    has_password.short_description = "Active"
    
    def get_readonly_fields(self, request, obj):
        if obj:
            if request.user.has_perm("dramaorg.modify_user"):
                return self.readonly_fields
            else:
                return self.staff_readonly
        else:
            return []

    def get_fieldsets(self, request, obj):
        if obj:
            if request.user.has_perm("dramaorg.modify_user"):
                return self.fieldsets
            else:
                return self.staff_fieldsets
        else:
            return self.add_fieldsets
            
@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('title', 'seasonstr', 'space',
                    'residency_starts', 'residency_ends', 'liaison_display')
    list_filter = ('season', 'year', 'space')
    autocomplete_fields = ('staff', 'liaisons')
    fields = ('title', ('season', 'year'), 'space',
              ('residency_starts', 'residency_ends'),
              ('staff', 'liaisons'), 'slug',
              ('created', 'modified'))
    readonly_fields = "created", "modified"
    exclude = ('invisible',)
    search_fields = ('title',)
    prepopulated_fields = {"slug": ("title",)}
    save_as_continue = False

    def liaison_display(self, obj):
        return ", ".join([str(i.get_full_name()) for i in obj.liaisons.all()])
    liaison_display.short_description = "Liaisons"

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ("__str__", "latitude", "longitude")
    list_editable = ('latitude', 'longitude')
    
@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'building', 'nickname')
    list_filter = ('building',)
    list_editable = ('nickname',)
    search_fields = ('name', 'building__name', 'nickname')

admin.site.register(Permission)
