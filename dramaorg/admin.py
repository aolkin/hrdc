from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group

from django import forms

from .models import *

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
        
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': (('first_name', 'last_name'), 'pgps',
                           ('affiliation', 'year'))}),
        ('Contact Info', {'fields': ('email', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'groups')}),
        ('Information', {'fields': ('last_login', 'date_joined', 'password')}),
    )
    staff_fieldsets = (
        (None, {'fields': (('first_name', 'last_name'), 'pgps',
                           ('affiliation', 'year'), 'email', 'phone',
                           'groups', 'is_active', 'password')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email',)
        }),
    )
    add_form = UserCreationForm
    add_form_template = "dramaadmin/invite_user.html"
    list_display = ('get_full_name', 'email', 'phone', 'affiliationyear',
                    'is_pdsm', 'is_board', 'is_active')
    list_filter = ('is_active','is_superuser', 'affiliation', 'year')
    search_fields = ('email', 'first_name', 'last_name',)
    readonly_fields = ('last_login', 'date_joined')
    staff_readonly = ('email', 'first_name', 'last_name', 'pgps',
                      'phone', 'groups', 'affiliation', 'year', 'is_active')
    actions = [generate_tokens, clear_tokens] if settings.DEBUG else []
    ordering = ('email',)
    save_as_continue = True
    
    def get_readonly_fields(self, request, obj):
        if obj:
            if request.user.is_superuser:
                return self.readonly_fields
            else:
                return self.staff_readonly
        else:
            return []

    def get_fieldsets(self, request, obj):
        if obj:
            if request.user.is_superuser:
                return self.fieldsets
            else:
                return self.staff_fieldsets
        else:
            return self.add_fieldsets
            
@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('title', 'seasonstr', 'space', 'people') #, 'invisible')
    list_filter = ('season', 'year', 'space') #, 'invisible')
    #list_editable = ('invisible',)
    autocomplete_fields = ('staff',)
    fields = ('title', ('season', 'year'), 'space', 'staff', 'slug')
    exclude = ('invisible',)
    search_fields = ('title',)
    prepopulated_fields = {"slug": ("title",)}
    save_as_continue = False

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False
    
@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'include_building_name')
    list_filter = ('building',)
    list_editable = ('name', 'building', 'include_building_name')
    list_display_links = None
    search_fields = ('name', 'building__name')

admin.register(GroupProxy, GroupAdmin)
admin.site.unregister(Group)
