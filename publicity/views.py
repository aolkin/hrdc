from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.views.generic.edit import UpdateView, CreateView, BaseCreateView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django import forms
from django.contrib import messages
from django.db.models import Q

from utils import InitializedLoginMixin

from django.conf import settings

from .models import *

from casting.models import Signing

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

        urls = (
            ("Show Info", "publicity:info"),
            ("Personnel List", "publicity:people"),
            ("Preview", "publicity:display")
        )
        
        for show in [i.publicity_info for i in
                     self.request.user.show_set.all().order_by("-pk")
                     if hasattr(i, "publicity_info")]:
            submenu = menu[str(show)] = []
            is_active = (hasattr(self, "object") and
                         self.object.pk == show.pk)
            for name, url in urls:
                submenu.append({
                    "name": name,
                    "url": reverse_lazy(url, args=(show.pk,)),
                    "active": is_active and current_url == url.split(":")[-1]
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
        fields = ('credits', 'contact_email', 'ticket_link',
                  'blurb', 'runtime', 'band_term') # 'content_warning')
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
                           "Please fix any errors below and try again.")
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
    fields=("position", "person", "type","order"), extra=1,
    widgets={
        "person": forms.HiddenInput(),
    })

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
                           "Please fix any errors below and try again.")
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

class SearchPerson(ShowStaffMixin, DetailView):
    def get(self, *args, **kwargs):
        if "term" in self.request.GET:
            terms = self.request.GET["term"].split(" ")
        else:
            terms = ("",)
        
        users = get_user_model().objects.all()
        for term in terms:
            q = Q(first_name__icontains=term)
            q |= Q(last_name__icontains=term)
            q |= Q(email__icontains=term)
            q |= Q(phone__icontains=term)
            users = users.filter(q)
        if users.count() > 20:
            return JsonResponse([
                { "text": "Too many results, please narrow your search..." }
            ], safe=False)
        people = [{
            "text": str(i) + " " + i.apostrophe_year,
            "id": i.id
        } for i in users]
        return JsonResponse(people, safe=False)

class AddUser(BaseCreateView):
    model = get_user_model()
    fields = "email", "first_name", "last_name", "year"
    
    def form_valid(self, form):
        person = form.save()
        return JsonResponse({
            "text": str(person) + " " + person.apostrophe_year,
            "id": person.id
        })

    def form_invalid(self, form):
        return JsonResponse({
            "errors": form.errors
        })

class ImportStaff(ShowStaffMixin, DetailView):
    def get(self, *args, **kwargs):
        self.object = self.get_object()
        try:
            count = 0
            for i in self.object.show.application.staffmember_set.all():
                p, created = ShowPerson.objects.get_or_create(
                    show=self.object, person=i.person.user,
                    type=1, position=i.role_name)
                if created:
                    count += 1
            messages.success(
                self.request,
                "Successfully imported {} staff members.".format(count))
        except AttributeError:
            messages.error(
                self.request,
                "No venue application attached to this show.")
        return redirect("publicity:people", self.object.id)

class ImportCast(ShowStaffMixin, DetailView):
    def get(self, *args, **kwargs):
        self.object = self.get_object()
        try:
            cm = self.object.show.casting_meta
            count = 0
            for i in Signing.objects.filter(response=True, character__show=cm):
                p, created = ShowPerson.objects.get_or_create(
                    show=self.object, person=i.actor,
                    type=2, position=i.character.name)
                if created:
                    count += 1
            messages.success(
                self.request,
                "Successfully imported {} cast members.".format(count))
        except AttributeError:
            messages.error(
                self.request,
                "This show is not set up for Common Casting.")
        return redirect("publicity:people", self.object.id)

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
                    "credits": self.request.GET.get("credits", "") != "0",
                    "cast": self.request.GET.get("cast", "") != "0",
                    "staff": self.request.GET.get("staff", "") != "0",
                    "band": self.request.GET.get("band", "") != "0",
                    "about": self.request.GET.get("about", "") != "0",
                    "dates": self.request.GET.get("dates", "") != "0",
                },
                "cast": ShowPerson.collate(context["object"].cast()),
                "staff": ShowPerson.collate(context["object"].staff()),
                "band": ShowPerson.collate(context["object"].band()),
            }).replace("\n","")
        return context
    
    def get(self, *args, **kwargs):
        res = super().get(*args, **kwargs)
        res["Content-Type"] = "application/javascript"
        res["Cache-Control"] = "no-cache"
        return res

class NewsletterMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        menu["HRDC Newsletter"] = [{
            "name": "Submit an Announcement",
            "url": reverse_lazy("publicity:public_index"),
            "active": current_url == "public_index"
        }]

        qs = self.request.user.announcement_set.filter(published=False)
        if qs.exists():
            submenu = menu["Current Submissions"] = []
            for announcement in qs.order_by("start_date", "end_date",
                                            "submitted"):
                is_active = (hasattr(self, "object") and self.object and
                             self.object.pk == announcement.pk)
                submenu.append({
                    "name": str(announcement),
                    "url": reverse_lazy("publicity:edit_announcement",
                                        args=(announcement.pk,)),
                    "active": is_active and current_url == "edit_announcement"
                })

        qs = self.request.user.announcement_set.filter(published=True)
        if qs.exists():
            submenu = menu["Published Announcements"] = []
            for announcement in qs:
                submenu.append({
                    "name": str(announcement),
                })
        return context

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ("title", "message", "graphic",
                  "note", "start_date", "end_date", "user")
        widgets = {
            'message': forms.Textarea(attrs={'rows': 8, 'cols': 40}),
            'note': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'user': forms.HiddenInput(),
        }

class NewsletterView(InitializedLoginMixin, NewsletterMixin, CreateView):
    verbose_name = "Submit Announcements"
    help_text = "submit to the newsletter"

    template_name = "publicity/announcement.html"
    form_class = NewsletterForm

    def post(self, *args, **kwargs):
        assert self.request.POST.get("user") == str(self.request.user.pk)
        return super().post(*args, **kwargs)
    
    def form_valid(self, *args, **kwargs):
        messages.success(self.request, "Successfully submitted announcement! "
                         "You may continue to edit it until it is published.")
        return super().form_valid(*args, **kwargs)
        
    def get_initial(self):
        return { "user": self.request.user }

class NewsletterEditView(InitializedLoginMixin, NewsletterMixin, UpdateView):
    template_name = "publicity/announcement.html"
    model = Announcement
    form_class = NewsletterForm

    def form_valid(self, *args, **kwargs):
        messages.success(self.request, "Saved changes.")
        return super().form_valid(*args, **kwargs)

    ## TODO: Check that user submitted the announcement
    ## TODO: Check that announcement has not been published
