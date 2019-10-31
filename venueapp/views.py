from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormView, CreateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django import forms
from django.forms import widgets
from django.contrib import messages    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from utils import InitializedLoginMixin, UserStaffMixin, ShowStaffMixin

from .models import *

class ApplicationStaffMixin(ShowStaffMixin):
    model = Application

class MenuMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        menu[""] = [{
            "name": "Applications",
            "url": reverse_lazy("venueapp:public_index"),
            "active": current_url == "public_index"
        }]

        if self.request.user.is_anonymous:
            return context

        shows = [i.application for i in
                 self.request.user.show_set.all().order_by("-pk")
                 if hasattr(i, "application") and
                 not i.application.full_submitted]

        urls = [
            ("Show Details", "venueapp:details"),
            ("Staff", "venueapp:staff"),
            ("Residencies", "venueapp:residencies"),
            ("Budget", "venueapp:budget"),
            ("Questions", "venueapp:questions"),
            ("Submit", "venueapp:submit"),
        ]

        for show in shows:
            title = str(show)
            i = 2
            while title in menu:
                title = "{} ({})".format(show, i)
                i += 1
            submenu = menu[title] = []
            is_active = (hasattr(self, "object") and
                         self.object.pk == show.pk)
            for name, url in urls:
                submenu.append({
                    "name": name,
                    "url": reverse_lazy(url, args=(show.pk,)),
                    "active": is_active and current_url == url.split(":")[-1]
                })
        return context

class IndexView(MenuMixin, InitializedLoginMixin, TemplateView):
    verbose_name = "Venue Applications"
    help_text = "apply for space"
    
    template_name = "venueapp/index.html"

class ShowForm(forms.ModelForm):
    class Meta:
        model = Show
        fields = "prod_type", "title", "creator_credit", "affiliation",

class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = "cast_breakdown", "band_size", "script"

class VenueSelectionForm(forms.Form):
    venues = forms.ModelMultipleChoiceField(
        required=True,
        queryset=VenueApp.objects.live(),
        widget=widgets.CheckboxSelectMultiple)

class ApplicationFormMixin(MenuMixin, InitializedLoginMixin):
    template_name = "venueapp/application.html"

    def get_forms(self):
        form_args = {}
        if self.request.method in ('POST', 'PUT'):
            form_args.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return (
            ShowForm(
                prefix="show", **form_args,
                instance=hasattr(self, "object") and self.object.show or None),
            ApplicationForm(
                prefix="app", **form_args,
                instance=hasattr(self, "object") and self.object or None),
            VenueSelectionForm(
                prefix="venue", **form_args,
                initial={
                    "venues": hasattr(self, "object") and
                    self.object.venues.all() or []
                }),
        )

    def get_context_data(self, **kwargs):
        if 'show_form' not in kwargs:
            kwargs['show_form'], kwargs["app_form"], kwargs["venue_form"] = self.get_forms()
        return super().get_context_data(**kwargs)

class NewApplication(ApplicationFormMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        show_form, app_form, venue_form = self.get_forms()
        if (show_form.is_valid() and app_form.is_valid() and
            venue_form.is_valid()):
            v = venue_form.cleaned_data["venues"][0]
            show = show_form.save(commit=False)
            show.season = v.season
            show.year = v.year
            show.save()
            show.staff.add(self.request.user)
            app = app_form.save(commit=False)
            app.show = show
            app.save()
            app.venues.set(venue_form.cleaned_data["venues"])
            messages.success(request, "New application created. Use the sidebar navigate through the rest of the application.")
            return redirect("venueapp:details", app.pk)
        else:
            return self.render_to_response(self.get_context_data(
                show_form=show_form, app_form=app_form, venue_form=venue_form))

class UpdateApplication(ApplicationFormMixin, DetailView):
    model = Application

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        show_form, app_form, venue_form = self.get_forms()
        if (show_form.is_valid() and app_form.is_valid() and
            venue_form.is_valid()):
            show = show_form.save()
            app = app_form.save()
            app.venues.set(venue_form.cleaned_data["venues"])
            messages.success(request, "Application updated.")
            return redirect("venueapp:details", app.pk)
        else:
            return self.render_to_response(self.get_context_data(
                show_form=show_form, app_form=app_form, venue_form=venue_form))
