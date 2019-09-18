from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django import forms
from django.contrib import messages
    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from utils import user_is_initialized

from django.conf import settings

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

        if self.request.user.is_anonymous:
            return context
        
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
            submenu.append({
                "name": "Preview",
                "url": reverse_lazy("publicity:display",
                                    args=(show.publicity_info.pk,)),
                "active": is_active and current_url == "display"
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
    verbose_name = "Publicity Manager"
    help_text = "update your webpage and directory"
    
    template_name = "publicity/index.html"

DateFormSet = forms.inlineformset_factory(
    PublicityInfo, PerformanceDate, fields=("performance", "note"), extra=1,
    widgets={
        "performance": forms.DateTimeInput(
            format=settings.DATETIME_INPUT_FORMAT
        ),
    })
    
class InfoForm(forms.ModelForm):
    class Meta:
        model = PublicityInfo
        fields = ('credits', 'contact_email',
                  'blurb', 'runtime',) # 'content_warning')
        widgets = {
            'credits': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'blurb': forms.Textarea(attrs={'rows': 5, 'cols': 40}),
            'content_warning': forms.Textarea(attrs={'rows': 2, 'cols': 40}),
        }
    
class InfoView(MenuMixin, ShowStaffMixin, UpdateView):
    template_name = "publicity/info.html"
    form_class = InfoForm

    def get_success_url(self):
        return reverse_lazy("publicity:info", args=(self.object.id,))
    
    def post(self, *args, **kwargs):
        res = super().post(*args, **kwargs)
        self.formset = DateFormSet(self.request.POST,
                                   instance=self.get_object())
        if self.formset.is_valid():
            self.formset.save()
        else:
            messages.error(self.request, "Failed to save performance dates. "+
                           "Please try again.")
            return self.get(*args, **kwargs)
        messages.success(self.request,
                         "Updated publicity information for {}.".format(
                             self.get_object()))
        return res
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["date_formset"] = (
            self.formset if hasattr(self, "formset") else DateFormSet(
                instance=self.get_object()
            )
        )
        return context

PersonFormSet = forms.inlineformset_factory(
    PublicityInfo, ShowPerson,
    fields=("position", "name", "year",
            "email", "phone", "type","order"), extra=1)

class PeopleView(MenuMixin, ShowStaffMixin, TemplateView):
    template_name = "publicity/people.html"
    model = PublicityInfo

    def post(self, *args, **kwargs):
        self.formset = PersonFormSet(self.request.POST,
                                     instance=self.get_object())
        if self.formset.is_valid():
            self.formset.save()
        else:
            messages.error(self.request, "Failed to save cast and staff. "+
                           "Please try again.")
            return self.get(*args, **kwargs)
        messages.success(self.request,
                         "Updated cast and staff directory for {}.".format(
                             self.get_object()))
        return redirect(reverse_lazy("publicity:people",
                                     args=(self.get_object().id,)))

    def get_context_data(self, *args, **kwargs):
        self.object = self.get_object()
        context = super().get_context_data(*args, **kwargs)
        context["formset"] = (
            self.formset if hasattr(self, "formset") else PersonFormSet(
                instance=self.get_object()
            )
        )
        return context

class DisplayView(MenuMixin, DetailView):
    template_name = "publicity/display.html"
    model = PublicityInfo

class ScriptView(DetailView):
    template_name = "publicity/embed.js"
    model = PublicityInfo

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["innerHtml"] = render_to_string(
            "publicity/content.html", {
                "object": context["object"],
                "h": self.request.GET.get("h", "h3"),
                "enabled": {
                    "cast": self.request.GET.get("cast", "") != "0",
                    "credits": self.request.GET.get("credits", "") != "0",
                    "staff": self.request.GET.get("staff", "") != "0",
                    "about": self.request.GET.get("about", "") != "0",
                    "dates": self.request.GET.get("dates", "") != "0",
                },
                "cast": ShowPerson.collate(context["object"].cast()),
                "staff": ShowPerson.collate(context["object"].staff()),
            }).replace("\n","")
        return context
    
    def get(self, *args, **kwargs):
        res = super().get(*args, **kwargs)
        res["Content-Type"] = "application/javascript"
        res["Cache-Control"] = "no-cache"
        return res
