from django.views.generic import TemplateView, View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django import forms
from django.forms import widgets
from django.contrib import messages    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.utils import timezone

from emailtracker.tools import render_for_user, render_to_queue

from utils import InitializedLoginMixin, UserStaffMixin, ShowStaffMixin

from datetime import timedelta, date, datetime
from collections import defaultdict, OrderedDict
from itertools import groupby

from .models import *
from .tasks import render_and_send_app

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

        staff = StaffMember.objects.filter(
            person__user=self.request.user, signed_on=True
        )
        shows = [Application.objects.get(id=i) for i in staff.values_list(
            "show", flat=True).order_by("-show").distinct()]

        urls = [
            ("Preview and Submit", "venueapp:submit"),
            ("Show Details", "venueapp:details"),
            ("Staff", "venueapp:staff"),
            ("Residency", "venueapp:residencies"),
            ("Budget(s)", "venueapp:budget"),
        ]

        for show in shows:
            title = str(show)
            i = 2
            while title in menu:
                title = "{} ({})".format(show, i)
                i += 1
            submenu = menu[title] = []
            active = (hasattr(self, "object") and
                         self.object.pk == show.pk)
            showstaff = staff.filter(show=show)
            if show.submitted:
                submenu.append({
                    "name": "<<submitted>>",
                })
                submenu.append({
                    "name": "View Application",
                    "url": reverse_lazy("venueapp:submit", args=(show.pk,)),
                    "active": active and current_url == "submit"
                })
                continue

            if showstaff.filter(role__category=10).exists():
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
            for person in showstaff:
                submenu.append({
                    "name": "{} Supplement".format(person.role_name),
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
            msg = self.get_success_message(form)
            if msg:
                messages.success(request, msg)
            return redirect(request.path)
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_message(self, form):
        return "Success!"

class UnsubmittedAppMixin(SingleObjectMixin):
    model = Application

    def get_object(self):
        obj = super().get_object()
        if obj.submitted:
            raise PermissionDenied("Cannot modify submitted applications.")
        return obj

class IndexView(MenuMixin, TemplateView):
    verbose_name = "Venue Applications"
    help_text = "apply for space"

    template_name = "venueapp/index.html"

    def get_context_data(self, **kwargs):
        kwargs["live"] = VenueApp.objects.available()
        kwargs["old"] = OldStyleApp.objects.available()
        if not self.request.user.is_anonymous:
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
        widgets = {
            "script": forms.ClearableFileInput(attrs={'accept':'application/pdf'})
        }

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
            messages.success(request, "Your new application has been created! Use the sidebar navigate through the rest of the application.")
            messages.info(request, "To allow others to edit this application, add them as Executive staff members.")
            return redirect("venueapp:staff", app.pk)
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

class DeleteApplication(UserStaffMixin, UnsubmittedAppMixin, View):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if request.POST.get("delete-confirmation") == "DELETE":
            show = self.object.show
            self.object.delete()
            try:
                show.delete()
            except Exception:
                messages.warning(request, "Failed to entirely delete your show from the system.")
            messages.success(request, "Application deleted.")
            return redirect("venueapp:public_index")
        else:
            messages.warning(request, 'Did not delete application. Please type "DELETE" to delete your application.')
            return redirect("venueapp:details", self.object.pk)

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
            render_for_user(
                user, "venueapp/email/invite.html", "venueapp", staff.pk,
                { "role": staff, "app": self.object, "who": request.user },
                subject="Added to {} Venue Application".format(self.object),
                tags=["venueapp", "staff_invite"])
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
                    messages.error(request, "Cannot assign same preference ({}) to multiple residencies.".format(pref))
                preferences[pref] = res
            else:
                for week, pref in prefs.items():
                    if pref in preferences:
                        if type(preferences[pref]) == VenueDateRange:
                            if preferences[pref].venue == res.venue:
                                preferences[pref].extend(
                                    dates[week],
                                    dates[week] + timedelta(days=6))
                            else:
                                messages.error(request, "Cannot assign same preference ({}) to multiple venues.".format(pref))
                        else:
                            messages.error(request, "Cannot assign same preference ({}) to multiple residencies.".format(pref))
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
                    length = ((slot.end - slot.start).days + 6) // 7
                    messages.info(request, "Preference {} is {} week{} ({:%b %d} - {:%b %d}) in {venue}.".format(pref, length, "s" if length != 1 else "", slot.start, slot.end, venue=slot.venue.venue))
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
    widgets={
        "answer": forms.Textarea(attrs={"rows": 6, "cols": 40}),
    }
)

class QuestionsView(MenuMixin, UserStaffMixin, FormMixin, UnsubmittedAppMixin,
                    DetailView):
    template_name = "venueapp/questions.html"
    form_class = AnswerFormSet

    def get_success_message(self, form):
        return "Answer{} updated.".format(
            "s" if self.object.venues.all().count() != 1 else "")

class MembershipMixin(InitializedLoginMixin):
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
            "resume": forms.ClearableFileInput(attrs={'accept':'application/pdf'})
        }

RoleAnswerFormSet = forms.inlineformset_factory(
    StaffMember, RoleAnswer, fields=("answer",), extra=0, can_delete=False,
    widgets={
        "answer": forms.Textarea(attrs={"rows": 4, "cols": 40}),
    }
)

class SupplementForm(forms.ModelForm):
    class Meta:
        fields = "statement", "attachment"
        model = StaffMember
        widgets = {
            "answer": forms.Textarea(attrs={"rows": 6, "cols": 60}),
            "attachment": forms.ClearableFileInput(attrs={'accept':'application/pdf'})
        }

class IndividualView(MenuMixin, FormMixin, MembershipMixin, UnsubmittedAppMixin,
                     DetailView):
    template_name = "venueapp/individual.html"
    form_class = RoleAnswerFormSet

    def get_context_data(self, **kwargs):
        if "supplement" not in kwargs:
            kwargs["supplement"] = SupplementForm(
                instance=self.get_membership(), prefix="supplement")
        kwargs["season_form"] = SeasonStaffForm(
            instance=self.get_membership().person)
        return super().get_context_data(**kwargs)

    def get_form(self):
        return super().get_form(self.get_membership())

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        errors = False
        supplement = SupplementForm(
            data=self.request.POST, files=self.request.FILES,
            instance=self.get_membership(), prefix="supplement"
        )
        if (self.get_membership().role.statement_length or
            self.get_membership().role.accepts_attachment):
            if supplement.is_valid():
                supplement.save()
                messages.success(self.request, "Supplement saved.")
            else:
                errors = True
        form = self.get_form()
        if self.get_membership().roleanswer_set.all().exists():
            if form.is_valid():
                form.save()
                messages.success(request, "Answer{} updated.".format(
                    "s" if self.get_membership().roleanswer_set.all().count()
                    != 1 else ""))
            else:
                errors = True
        if errors:
            return self.render_to_response(self.get_context_data(
                form=form, supplement=supplement))
        else:
            return redirect(request.path)

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

class SignOffView(MembershipMixin, UnsubmittedAppMixin, View):
    def get(self, request, *args, **kwargs):
        staff = self.get_membership()
        staff.signed_on = False
        staff.save()
        messages.success(request, "Left application for {}.".format(
                self.get_object()))
        return redirect("venueapp:public_index")

def make_cover_page(app):
        cover = OrderedDict()
        cover["Production"] = app.show.title
        cover["Production Type"] = app.show.get_prod_type_display()
        cover["Author/Composer"] = app.show.creator_credit
        cover["Sponsorship/Affiliation"] = app.show.affiliation
        cover["Executive Staff"] = ", ".join(
            [str(i) for i in app.staffmember_set.filter(
                role__category=10)])
        cover["Cast Gender Breakdown"] = app.cast_breakdown
        cover["Band/Orchestra Size"] = app.band_size
        cover["Application Submitted"] = app.submitted
        return cover

class PreviewSubmitView(MenuMixin, UserStaffMixin, DetailView):
    template_name = "venueapp/preview.html"
    model = Application

    def get_context_data(self, **kwargs):
        kwargs["cover"] = make_cover_page(self.object)
        return super().get_context_data(**kwargs)

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.submitted = timezone.now()
        self.object.save()
        transaction.on_commit(
            lambda id=self.object.pk: render_and_send_app.delay(id))
        messages.success(self.request, "Application for {} submitted to {}! Check your email for confirmation.".format(self.object, self.object.venuesand()))
        return redirect("venueapp:public_index")
