from django.shortcuts import render
from django.views.generic import View, TemplateView
from django.views.generic.edit import UpdateView, CreateView, BaseCreateView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django import forms
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.utils.html import mark_safe
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt

import calendar, datetime

from utils import InitializedLoginMixin
from config import config
from django.conf import settings

from .models import *
from venueapp.models import VenueApp
from casting.models import Signing, Slot

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

    def get(self, *args, **kwargs):
        if not self.request.user.is_anonymous:
            for i in self.request.user.show_set.filter(
                    space__isnull=False,
                    publicity_info__isnull=True):
                PublicityInfo(show=i).save()
        return super().get(*args, **kwargs)

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
        fields = ('credits', 'cover', 'contact_email', 'ticket_link',
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
                if i.signable:
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

class BaseEmbedView(TemplateView):
    def get_template_names(self):
        return ["publicity/embed.{}".format(
            self.request.resolver_match.kwargs["format"])]

    def get(self, *args, format, **kwargs):
        res = super().get(*args, **kwargs)
        res["Content-Type"] = "application/{}".format(
            "javascript" if format == "js" else "json")
        res["Cache-Control"] = "no-cache"
        return res

class ShowScriptView(BaseEmbedView, DetailView):
    model = PublicityInfo

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["innerHtml"] = render_to_string(
            "publicity/content.html", {
                "object": context["object"],
                "h": self.request.GET.get("h", "h3"),
                "enabled": {
                    "cover": self.request.GET.get("cover", "") != "0",
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
                "is_show_staff": context["object"].show.staff.filter(
                    id=self.request.user.id).exists()
            }).replace("\n","")
        return context

class SeasonScriptView(BaseEmbedView):
    def get_context_data(self, **kwargs):
        year = self.request.GET.get("year") or config.year
        season = self.request.GET.get("season") or config.season
        if type(season) == str and len(season) > 1:
            for val, name in Season.SEASONS:
                if name.lower() == season.lower():
                    season = val
                    break
            if type(season) == str:
                season = config.season
        season_name = Season.SEASONS[int(season)][1]
        shows = PublicityInfo.objects.filter(
            show__season=season, show__year=year).exclude(
                show__space=None).exclude(show__residency_starts=None)
        venues = defaultdict(list)
        for i in shows:
            venues[i.show.space].append(i)
        sorted_shows = [(i, sorted(
            val, key=lambda x: x.show.residency_starts))
                        for i, val in venues.items()]
        kwargs["innerHtml"] = render_to_string(
            "publicity/render_season.html", {
                "year": year,
                "season": season_name,
                "venues": sorted(sorted_shows, key=lambda x: x[0].order)
            }).replace("\n", "")
        return super().get_context_data(**kwargs)

class NewsletterMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        menu["HRDC Newsletter"] = [{
            "name": "Submit an Announcement",
            "url": reverse_lazy("publicity:public_app"),
            "active": current_url == "public_app"
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

generic_calendar = calendar.Calendar()

class VenueAppWrapper(AbstractEvent):
    def __init__(self, venueapp):
        self.app = venueapp
        self.name = "{} Apps Due".format(self.app.venue)
        self.performance = self.app.due
        self.note = "[Venue Applications for the {} for the {} Season]".format(
            self.app.venue, self.app.seasonstr())
        self.venue = None
        self.webpage = (settings.SITE_URL + reverse("venueapp:public_index") +
                        "?utm_medium=referral&utm_source=Calendar"
                        "&utm_campaign=venueapp")

class AuditionWrapper(AbstractEvent):
    def __init__(self, qs):
        first = qs.order_by("start").first()
        self.name = "Common Casting Auditions"
        self.performance = timezone.make_aware(
            datetime.datetime.combine(first.day, first.start))
        venues = list(qs.values_list("space__building__name",
                                     flat=True).distinct())
        if len(venues) > 1:
            sep = ("," if len(venues) > 2 else "") + " and "
            venues = venues[:-2] + [sep.join(venues[-2:])]
        self.note = "Auditions will be held in {}.".format(", ".join(venues))
        self.venue = None
        self.webpage = (settings.SITE_URL + reverse("casting:public_index") +
                        "?utm_medium=referral&utm_source=Calendar"
                        "&utm_campaign=casting")

def get_events(**kwargs):
    app_kwargs = { k.replace("performance", "due") : v
                   for (k, v) in kwargs.items() }
    app_kwargs["live"] = True
    events = (list([VenueAppWrapper(i) for i in
                    VenueApp.objects.filter(**app_kwargs)]) +
              list(PerformanceDate.objects.filter(**kwargs)) +
              list(Event.objects.filter(**kwargs)))
    slot_kwargs = { k.replace("performance", "day").replace("__date", "") : v
                    for (k, v) in kwargs.items() }
    slot_kwargs["type"] = 0
    if Slot.objects.filter(**slot_kwargs).exists():
        for day in Slot.objects.filter(**slot_kwargs).values_list(
                "day", flat=True).distinct():
            events.append(AuditionWrapper(Slot.objects.filter(day=day)))
    return sorted(events, key=lambda obj: obj.performance)

@method_decorator(xframe_options_exempt, name="dispatch")
class CalendarView(TemplateView):
    verbose_name = "Calendar"
    help_text = "view upcoming performances"

    def get_template_names(self):
        if self.request.GET.get("embed", False):
            return "publicity/embed_calendar.html"
        else:
            return "publicity/calendar.html"

    def get_context_data(self, **kwargs):
        now = timezone.localtime(timezone.now())
        if self.request.GET.get("embed"):
            kwargs["BT_extra_body_class"] = "embedded"
        kwargs["embed"] = self.request.GET.get("embed", False)
        kwargs["year"] = year = self.kwargs.get("year", now.year)
        kwargs["month"] = month = self.kwargs.get("month", now.month)
        date = datetime.date(year, month, 1)
        kwargs["prev"] = date - datetime.timedelta(days=1)
        kwargs["next"] = date + datetime.timedelta(days=31)
        kwargs["month_name"] = calendar.month_name[month]
        kwargs["calendar"] = calendar
        kwargs["cal"] = map(lambda dates: [
            (date, get_events(performance__date=date))
            for date in dates
        ], generic_calendar.monthdatescalendar(year, month))

        kwargs["upcoming"] = get_events(
            performance__gte=now, performance__lte=now + datetime.timedelta(
                days=config.get_int("upcoming_performances_future_days", 14)))
        return super().get_context_data(**kwargs)


class UpcomingScriptView(BaseEmbedView):
    def get_context_data(self, **kwargs):
        now = timezone.localtime(timezone.now())
        kwargs["innerHtml"] = render_to_string(
            "publicity/embed_upcoming.html", {
                "upcoming": get_events(
                    performance__gte=now,
                    performance__lte=now +
                    datetime.timedelta(days=config.get_int(
                        "upcoming_performances_future_days", 14))
                ),
                "site_url": settings.SITE_URL,
            }).replace("\n", "")
        return super().get_context_data(**kwargs)

class AdminIndexView(PermissionRequiredMixin, TemplateView):
    verbose_name = "Show Information"
    help_text = "(from publicity manager)"

    permission_required = ("publicity.view_publicityinfo",)
    template_name = "publicity/admin_index.html"

    def get_context_data(self, **kwargs):
        years = defaultdict(lambda: [False] * 4)
        for season, year in PublicityInfo.objects.all().values_list(
            "show__season", "show__year").distinct():
            years[year][season] = Season.SEASONS[season]
        kwargs["years"] = sorted(years.items())
        kwargs["headers"] = Season.SEASONS
        return super().get_context_data(**kwargs)

class AdminMixin(PermissionRequiredMixin):
    permission_required = ("publicity.view_showperson", "dramaorg.view_user")

    def get_season(self):
        if "season" in self.kwargs and "year" in self.kwargs:
            return self.kwargs["season"], self.kwargs["year"]
        return self.object.show.season, self.object.show.year

    def get_season_display(self):
        season, year = self.get_season()
        return "{} {}".format(Season.SEASONS[season][1], year)

    def get_context_data(self, **kwargs):
        current_url = self.request.resolver_match.url_name
        menu = kwargs["sidebar_menu"] = {}
        menu[""] = [{
            "name": "Show Information",
            "url": reverse_lazy("publicity:admin"),
            "active": current_url == "admin"
        }]

        kwargs["season"] = self.get_season_display()
        submenu = menu[kwargs["season"]] = []

        season, year = self.get_season()
        for show in PublicityInfo.objects.filter(
                show__season=season, show__year=year):
            is_active = (hasattr(self, "object") and
                         self.object.pk == show.pk)
            submenu.append({
                "name": str(show),
                "url": reverse_lazy("publicity:admin:show", args=(show.pk,)),
                "active": is_active and current_url == "show"
            })
        return super().get_context_data(**kwargs)

class AdminSeasonView(AdminMixin, TemplateView):
    template_name = "publicity/admin_season.html"

class AdminShowView(AdminMixin, DetailView):
    template_name = "publicity/admin_show.html"
    model = PublicityInfo
