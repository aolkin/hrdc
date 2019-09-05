from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import SingleObjectMixin
from django.urls import reverse_lazy

from django import forms
from django.contrib import messages
    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from utils import user_is_initialized

from .models import *

class InitializedLoginMixin:
    @method_decorator(login_required)
    @method_decorator(user_is_initialized)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class MenuMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        menu[""] = [{
            "name": "Publicity",
            "url": reverse_lazy("publicity:index"),
            "active": current_url == "index"
        }]
        
        for show in [i for i in
                     self.request.user.show_set.all().order_by("-pk")
                     if hasattr(i, "publicity_info")]:
            submenu = menu[str(show)] = []
            is_active = (hasattr(self, "object") and
                         self.object.pk == show.publicity_info.pk)
            submenu.append({
                "name": "Show Info",
                "url": reverse_lazy("publicity:info",
                                    args=(show.publicity_info.pk,)),
                "active": is_active and current_url == "info"
            })
            submenu.append({
                "name": "Cast and Staff",
                "url": reverse_lazy("publicity:people",
                                    args=(show.publicity_info.pk,)),
                "active": is_active and current_url == "people"
            })
        return context

class ShowStaffMixin(InitializedLoginMixin, SingleObjectMixin):
    model = PublicityInfo
    
    test_silent = False
    
    def test_func(self):
        if super().test_func():
            if self.get_object().show.user_is_staff(self.request.user):
                return True
            else:
                if not self.test_silent:
                    messages.error(self.request, "You are not a member of the "
                                   "executive staff of that show. Log in as a "
                                   "different user?")
        return False

class IndexView(MenuMixin, InitializedLoginMixin, TemplateView):
    verbose_name = "Show Publicity"
    help_text = "Update your web listing"
    
    template_name = "publicity/index.html"

DateFormSet = forms.modelformset_factory(PerformanceDate,
                                         fields=("show", "performance"))
    
class InfoForm(forms.ModelForm):
    class Meta:
        model = PublicityInfo
        fields = ('credits', 'contact_email',
                  'blurb', 'runtime', 'content_warning')
        widgets = {
            'credits': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'blurb': forms.Textarea(attrs={'rows': 5, 'cols': 40}),
            'content_warning': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }
    
class InfoView(MenuMixin, ShowStaffMixin, UpdateView):
    template_name = "publicity/info.html"
    success_url = reverse_lazy("publicity:index")
    form_class = InfoForm

    def post(self, *args, **kwargs):
        res = super().post(*args, **kwargs)
        self.formset = DateFormSet(self.request.POST)
        if self.formset.is_valid():
            self.formset.save()
        else:
            messages.error(self.request, "Failed to save performance dates. "+
                           "Please try again.")
        return self.get(*args, **kwargs)
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["date_formset"] = (
            self.formset if hasattr(self, "formset") else DateFormSet(
                queryset=self.get_object().performancedate_set.all(),
                initial=[{
                    "show": self.get_object()
                }]
            )
        )
        return context

class PeopleView(MenuMixin, ShowStaffMixin, UpdateView):
    template_name = "publicity/people.html"

    fields = ('people',)
