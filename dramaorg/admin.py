from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'groups')}),
        ('Information', {'fields': ('last_login', 'date_joined',
                                    'login_token', 'token_expiry')}),
    )
    staff_fieldsets = (
        (None, {'fields': ('email', 'first_name', 'last_name', 'phone',
                           'groups', 'is_active')}),
    )
    staff_readonly = ('email', 'first_name', 'last_name', 'phone', 'groups')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email',)
        }),
    )
    add_form = UserCreationForm
    add_form_template = "dramaorg/invite_user.html"
    list_display = ('get_full_name', 'email', 'phone', 'is_pdsm', 'is_board',
                    'is_active')
    list_filter = ('is_active','is_superuser')
    search_fields = ('email', 'first_name', 'last_name',)
    readonly_fields = ('last_login', 'date_joined', 'login_token')
    actions = [generate_tokens, clear_tokens]
    staff_actions = []
    ordering = ('email',)
    save_as_continue = True

    def change_view(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            try:
                self.fieldsets = self.staff_fieldsets
                self.readonly_fields = self.staff_readonly
                self.actions = self.staff_actions
                response = super().change_view(request, *args, **kwargs)
            finally:
                self.actions = UserAdmin.actions
                self.fieldsets = UserAdmin.fieldsets
                self.readonly_fields = UserAdmin.readonly_fields
            return response
        else:
            return super().change_view(request, *args, **kwargs)
    
@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ('title', 'season', 'year', 'people', 'invisible')
    list_filter = ('season', 'year', 'staff', 'invisible')
    list_editable = ('invisible',)
    filter_horizontal = ('staff',)
    exclude = ('invisible',)
    search_fields = ('title',)
    prepopulated_fields = {"slug": ("title",)}
    save_as_continue = False

admin.site.unregister(Group)
