from django.shortcuts import render
from django.views.generic import TemplateView, View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django import forms
from django.forms import widgets
from django.contrib import messages    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.http import Http404

from utils import InitializedLoginMixin, UserStaffMixin, ShowStaffMixin

from datetime import timedelta, date, datetime
from collections import defaultdict
from itertools import groupby

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

        shows = [(i.show, i.role, i) for i in StaffMember.objects.filter(
            person__user=self.request.user)
                 if i.signed_on and not i.show.full_submitted]

        urls = [
            ("Preview and Submit", "venueapp:submit"),
            ("Show Details", "venueapp:details"),
            ("Staff", "venueapp:staff"),
            ("Residency", "venueapp:residencies"),
            ("Budget(s)", "venueapp:budget"),
        ]

        for show, role, person in shows:
            title = str(show)
            i = 2
            while title in menu:
                title = "{} ({})".format(show, i)
                i += 1
            submenu = menu[title] = []
            active = (hasattr(self, "object") and
                         self.object.pk == show.pk)
            if role.admin:
                for name, url in urls:
                    submenu.append({
                        "name": name,
                        "url": reverse_lazy(url, args=(show.pk,)),
                        "active": active and current_url == url.split(":")[-1]
                    })
                if any([app.questions.exists() for app in show.venues.all()]):
                    submenu.append({
                        "name": "Questions",
                        "url": reverse_lazy("venueapp:questions",
                                            args=(show.pk,)),
                        "active": active and current_url == "questions"
                    })
            if (role.statement_length or role.accepts_attachment or
                role.rolequestion_set.count()):
                submenu.append({
                    "name": "{} Supplement".format(role),
                    "url": reverse_lazy("venueapp:individual",
                                        args=(show.pk, person.pk)),
                    "active": (active and current_url == "individual" and
                               self.kwargs.get("role", None) == str(person.pk))
                })
        return context

class FormMixin:
    def get_form(self, instance=None):
        form_args = {}
        if self.request.method in ('POST', 'PUT'):
            form_args.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return self.form_class(
            **form_args,
            instance=instance or (
                hasattr(self, "object") and self.object or None)
        )

    def get_context_data(self, **kwargs):
        if 'form' not in kwargs:
            kwargs['form'] = self.get_form()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            form.save()
            messages.success(request, self.get_success_message(form))
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_message(self, form):
        return "Success!"

class UnsubmittedAppMixin(SingleObjectMixin):
    model = Application

    def get_object(self):
        obj = super().get_object()
        if obj.full_submitted:
            raise PermissionDenied("Cannot modify submitted applications.")
        return obj

class IndexView(MenuMixin, InitializedLoginMixin, TemplateView):
    verbose_name = "Venue Applications"
    help_text = "apply for space"

    template_name = "venueapp/index.html"

    def get_context_data(self, **kwargs):
        kwargs["roles"] = StaffMember.objects.filter(
            person__user=self.request.user)
        return super().get_context_data(**kwargs)

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

class ApplicationFormMixin:
    template_name = "venueapp/details.html"

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

class NewApplication(ApplicationFormMixin, MenuMixin, InitializedLoginMixin,
                     TemplateView):
    def post(self, request, *args, **kwargs):
        show_form, app_form, venue_form = self.get_forms()
        if (show_form.is_valid() and app_form.is_valid() and
            venue_form.is_valid()):
            v = venue_form.cleaned_data["venues"][0]
            show = show_form.save(commit=False)
            show.season = v.season
            show.year = v.year
            show.save()
            app = app_form.save(commit=False)
            app.show = show
            app.save()
            app.venues.set(venue_form.cleaned_data["venues"])
            StaffMember.objects.create_from_user(
                app, request.user, signed_on=True,
                role=StaffRole.objects.active().order_by("pk").first()
            )
            messages.success(request, "New application created. Use the sidebar navigate through the rest of the application.")
            return redirect("venueapp:details", app.pk)
        else:
            return self.render_to_response(self.get_context_data(
                show_form=show_form, app_form=app_form, venue_form=venue_form))

class UpdateApplication(ApplicationFormMixin, MenuMixin, UserStaffMixin,
                        UnsubmittedAppMixin, DetailView):

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

class RoleChoiceIterator(forms.models.ModelChoiceIterator):
    def __iter__(self):
        for group, objs in groupby(self.queryset,
                                   lambda r: r.get_category_display()):
            yield (group, [self.choice(obj) for obj in objs])

class RoleChoiceField(forms.ModelChoiceField):
    iterator = RoleChoiceIterator

class StaffMemberForm(forms.ModelForm):
    role = RoleChoiceField(queryset=StaffRole.objects.active())
    class Meta:
        model = StaffMember
        fields = "role", "other_role"

StaffFormSet = forms.inlineformset_factory(
    Application, StaffMember, form=StaffMemberForm,
    fields=("role", "other_role"), extra=0,
)

class AddStaffMemberForm(forms.Form):
    role = RoleChoiceField(queryset=StaffRole.objects.active())
    email = forms.EmailField()

class StaffView(MenuMixin, UserStaffMixin, FormMixin, UnsubmittedAppMixin,
                DetailView):
    template_name = "venueapp/staff.html"
    form_class = StaffFormSet

    def get_context_data(self, **kwargs):
        kwargs["add_form"] = AddStaffMemberForm()
        return super().get_context_data(**kwargs)

    def get_success_message(self, form):
        return "Staff list updated."

class AddStaffView(UserStaffMixin, UnsubmittedAppMixin, View):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AddStaffMemberForm(self.request.POST)
        if form.is_valid():
            user, uc = get_user_model().objects.get_or_create(
                email=form.cleaned_data["email"])
            staff = StaffMember.objects.create_from_user(
                self.object, user, role=form.cleaned_data["role"])
            # TODO Send email to staff member with instructions
            messages.success(request, "Staff member invited. They must now log in themselves to upload their resume and sign on to the show.")
        else:
            messages.error(request, "Failed to add staff member.")
        return redirect("venueapp:staff", self.object.pk)

class VenueDateRange:
    def __init__(self, venue, start, end):
        self.venue = venue
        self.start = start
        self.end = end

    def extend(self, start, end):
        if start < self.start:
            self.start = start
        if end > self.end:
            self.end = end

    def __str__(self):
        return "{} - {}".format(self.start, self.end)

class LengthForm(forms.ModelForm):
    class Meta:
        fields = "length_description",
        model = Application
        widgets = {
            "length_description": forms.Textarea(attrs={"rows": 3, "cols": 40}),
        }

class ResidencyView(MenuMixin, UserStaffMixin, FormMixin, UnsubmittedAppMixin,
                    DetailView):
    template_name = "venueapp/residencies.html"
    form_class = LengthForm

    def get_residency(self, venue, current):
        res = venue.availableresidency_set.filter(
            start__lt=current + timedelta(days=7), end__gt=current).first()
        if res:
            if not hasattr(venue, "dow"):
                venue.dow = "{:%a} - {:%a}".format(res.start, res.end)
            res.weeks = 1
            if res.type:
                if res.start < current:
                    res.continuation = True
                    res.weeks = 0
                else:
                    res.weeks = ((res.end - current).days + 6) // 7
                pref = res.slotpreference_set.filter(app=self.object).first()
            else:
                pref = SlotPreference.objects.filter(
                    app=self.object, venue=res.venue,
                    start__lte=current, end__gt=current).first()
            res.pref = pref and pref.ordering
        return res

    def get_context_data(self, **kwargs):
        venues = kwargs["venues"] = self.object.venues.all()[:]
        residencies = AvailableResidency.objects.filter(venue__in=venues)
        calendar = []
        current = residencies.first().start
        end = residencies.last().end
        while current <= end:
            slots = [
                self.get_residency(venue, current) for venue in venues
            ]
            if any(slots):
                calendar.append((current, current + timedelta(days=6), slots))
            else:
                calendar.append((None, None, len(venues) + 1))
            current += timedelta(days=7)
        kwargs["calendar"] = calendar
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        dates = {}
        slots = defaultdict(dict)
        highest = 0
        for k, v in request.POST.items():
            if k.startswith("date"):
                dates[k.lstrip("date")] = datetime.strptime(
                    v, "%Y-%m-%d").date()
            elif k.startswith("slot"):
                slot, i = k.lstrip("slot").split("-")
                if v:
                    slots[slot][i] = int(v)
                    highest = max(highest, int(v))
        preferences = dict()
        for slotid, prefs in slots.items():
            res = AvailableResidency.objects.get(id=slotid)
            if res.type:
                pref = list(prefs.values())[0]
                if pref in preferences:
                    messages.error(request, "Assigned preference {} to multiple residencies.".format(pref))
                preferences[pref] = res
            else:
                for week, pref in prefs.items():
                    if pref in preferences:
                        if type(preferences[pref]) == VenueDateRange:
                            preferences[pref].extend(
                                dates[week], dates[week] + timedelta(days=6))
                        else:
                            messages.error(request, "Assigned preference {} to multiple residencies.".format(pref))
                    else:
                        preferences[pref] = VenueDateRange(
                            res.venue, dates[week],
                            dates[week] + timedelta(days=6))
        with transaction.atomic():
            SlotPreference.objects.filter(app=self.object).delete()
            for pref in range(1, highest + 1):
                if pref in preferences:
                    slot = preferences[pref]
                    preference = SlotPreference(
                        app=self.object, venue=slot.venue, ordering=pref)
                    if type(slot) == VenueDateRange:
                        preference.start = slot.start
                        preference.end = slot.end
                    else:
                        preference.slot = slot
                    preference.save()
                    messages.info(request, "Preference {} is {} weeks ({:%b %d} - {:%b %d}) in {venue}.".format(pref, ((slot.end - slot.start).days + 6) // 7, slot.start, slot.end, venue=slot.venue.venue))
                else:
                    messages.warning(
                        request, "Missing preference {}.".format(pref))
            if not highest:
                messages.warning(
                    request, "No residency preferences saved!")
        form = self.get_form()
        if form.is_valid():
            form.save()
        return self.render_to_response(self.get_context_data(form=form))

        return self.get(request, *args, **kwargs)

BudgetFormSet = forms.inlineformset_factory(
    Application, BudgetLine,
    fields=("name", "amount", "notes"), extra=0,
)

class AddBudgetLineForm(forms.ModelForm):
    class Meta:
        model = BudgetLine
        fields = ("venue", "category", "name", "amount", "notes")
        widgets = {
            "venue": forms.widgets.HiddenInput()
        }

class BudgetView(MenuMixin, UserStaffMixin, FormMixin, UnsubmittedAppMixin,
                 DetailView):
    template_name = "venueapp/budget.html"
    form_class = BudgetFormSet

    def get_context_data(self, **kwargs):
        kwargs["add_form"] = AddBudgetLineForm(prefix="create")
        return super().get_context_data(**kwargs)

    def get_success_message(self, form):
        return "Budget{} updated.".format(
            "s" if self.object.venues.all().count() != 1 else "")

class AddBudgetView(UserStaffMixin, UnsubmittedAppMixin, View):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = AddBudgetLineForm(self.request.POST, prefix="create")
        if form.is_valid():
            budget = BudgetLine.objects.create(
                show=self.object, **form.cleaned_data)
            messages.success(request, "Budget line added to {}.".format(
                budget.venue.venue))
        else:
            messages.error(request, "Failed to add budget line.")
        return redirect("venueapp:budget", self.object.pk)

AnswerFormSet = forms.inlineformset_factory(
    Application, Answer, fields=("answer",), extra=0, can_delete=False,
)

class QuestionsView(MenuMixin, UserStaffMixin, FormMixin, UnsubmittedAppMixin,
                    DetailView):
    template_name = "venueapp/questions.html"
    form_class = AnswerFormSet

    def get_success_message(self, form):
        return "Answer{} updated.".format(
            "s" if self.object.venues.all().count() != 1 else "")

class MembershipMixin:
    def get_membership(self):
        if not hasattr(self, "membership"):
            self.membership = self.get_object().staffmember_set.filter(
                pk=self.kwargs["role"], person__user=self.request.user
            ).first()
            if not self.membership:
                raise Http404("Role not found")
        return self.membership

    def get_context_data(self, **kwargs):
        kwargs['staff'] = self.get_membership()
        return super().get_context_data(**kwargs)

class SeasonStaffForm(forms.ModelForm):
    class Meta:
        fields = "resume", "conflicts"
        model = SeasonStaffMeta
        widgets = {
            "conflicts": forms.Textarea(attrs={"rows": 2, "cols": 40}),
        }

RoleAnswerFormSet = forms.inlineformset_factory(
    StaffMember, RoleAnswer, fields=("answer",), extra=0, can_delete=False,
)
## TODO add attachment/statement
class IndividualView(MenuMixin, FormMixin, MembershipMixin, UnsubmittedAppMixin,
                     DetailView):
    template_name = "venueapp/individual.html"
    form_class = RoleAnswerFormSet

    def get_context_data(self, **kwargs):
        kwargs["season_form"] = SeasonStaffForm(
            instance=self.get_membership().person)
        return super().get_context_data(**kwargs)

    def get_form(self):
        return super().get_form(self.get_membership())

    def get_success_message(self, form):
        return "Answer{} updated.".format(
            "s" if self.object.venues.all().count() != 1 else "")

class SeasonStaffView(SingleObjectMixin, View):
    model = SeasonStaffMeta

    def get(self, request, *args, **kwargs):
        return redirect(self.request.GET.get(
            "redirect", reverse_lazy("venueapp:public_index")))

    def post(self, request, *args, **kwargs):
        if self.request.user != self.get_object().user:
            raise PermissionDenied()
        form = SeasonStaffForm(
            data=self.request.POST, files=self.request.FILES,
            instance=self.get_object()
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Updated resume and conflicts for {}".format(self.get_object().seasonstr()))
        else:
            messages.error(request, "Failed to update resume and conflicts for {}".format(self.get_object().seasonstr()))
        return self.get(request, *args, **kwargs)

class SignOnView(MembershipMixin, UnsubmittedAppMixin, View):
    def get(self, request, *args, **kwargs):
        staff = self.get_membership()
        staff.signed_on = True
        staff.save()
        messages.success(request, "Signed on to {}.".format(
                self.get_object()))
        return redirect("venueapp:individual", self.get_object().pk, staff.pk)
