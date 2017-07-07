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
        
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'groups')}),
        ('Information', {'fields': ('last_login', 'date_joined',
                                    'login_token')}),
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
    ordering = ('email',)

    def change_view(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            try:
                self.fieldsets = self.staff_fieldsets
                self.readonly_fields = self.staff_readonly
                response = super().change_view(request, *args, **kwargs)
            finally:
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
    search_fields = ('title',)
    prepopulated_fields = {"slug": ("title",)}

admin.site.unregister(Group)
