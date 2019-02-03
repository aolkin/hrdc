
from django.views.generic.base import *
from django.views.generic.edit import *
from django.http import JsonResponse
from django.shortcuts import redirect

from django.urls import reverse_lazy, reverse
from django.db.models import Q

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages

from django.conf.urls import url

from django import forms
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
import datetime

from emailtracker.tools import render_for_user

from ..models import *
from . import get_current_slots, building_model
from ..utils import UserIsSeasonPdsmMixin, suppress_autotime

class SignInStartForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'email@example.com',
            'autocomplete': 'off',
        }))

    def clean(self):
        cleaned_data = super().clean()
        shows = self.data.getlist("shows",[])
        if not shows:
            raise forms.ValidationError(
                "Please select a show to audition for!")
        cleaned_data["shows"] = shows
        return cleaned_data
    
    def __init__(self, instance, **kwargs):
        self.building = instance
        super().__init__(**kwargs)

PERMISSION_DENIED_MESSAGE = """You must be logged in as a staff member to access
 the casting sign-in page directly. If you are not a staff member, please try
 the publicly accessible location-based sign-in method."""
        
class ActorSignInBase(UserIsSeasonPdsmMixin, TemplateResponseMixin):
    popout = False

    def get_building(self):
        return self.request.session.get("building") or self.get_object().pk
    
    def get_location(self):
        return self.request.session.get("located_building")
    
    def test_func(self):
        if self.get_location():
            if (self.get_location() == self.get_building() and
                (self.request.session["located_building_ts"] > (
                    timezone.now() - timedelta(hours=1)))):
                return True
        return super().test_func()
    
    def get_permission_denied_message(self):
        return PERMISSION_DENIED_MESSAGE

    def actor_missing(self):
        messages.error(
            self.request, "An error has occurred. Please try again.")
        return reverse("casting:sign_in_start",
                       args=(self.request.session["building"],))
    
    def get_success_url(self):
        if "actor" not in self.request.session:
            return self.actor_missing()
        if self.get_actor().is_initialized:
            for i in self.request.session.get("audition_ids", []):
                audition = Audition.objects.get(id=i)
                if not audition.actorseasonmeta.conflicts:
                    return reverse("casting:sign_in_seasonmeta")
                if audition.tech_interest == None:
                    return reverse("casting:sign_in_tech", args=(audition.id,))
            return reverse("casting:sign_in_done")
        else:
            return reverse("casting:sign_in_profile")
    
    def get_actor(self, *args, **kwargs):
        return get_user_model().objects.get(pk=self.request.session["actor"])
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if not self.get_location():
            context["BT_header_url"] = None
        context["shows"] = CastingMeta.objects.filter(
            id__in=map(lambda x: x.split(":")[0],
                       self.request.session.get("show_ids",[])))
        context["actor"] = SimpleLazyObject(self.get_actor)
        return context

class ActorSignInStart(ActorSignInBase, BaseUpdateView):
    form_class = SignInStartForm
    model = building_model
    template_name = "casting/sign_in/start.html"
    show_all = False
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        self.request.session["popout"] = self.popout
        if self.show_all:
            q = Q(day=timezone.localdate())
            q |= Q(day=timezone.localdate() - datetime.timedelta(days=1),
                   end__gt=datetime.time(hour=21))
            slots = Slot.objects.auditions().filter(
                q, space__building=self.object)
        else:
            slots = get_current_slots().filter(space__building=self.object)
        context["shows"] = slots.order_by("show_id", "start").values_list(
            "show__show__title", "show_id", "space_id")
        if self.get_location():
            context["located_user_signin"] = True
        return context
    
    def form_valid(self, form):
        if self.request.session.get("located_building"):
            self.actor = self.request.user
        else:
            self.actor, created = get_user_model().objects.get_or_create(
                email=form.cleaned_data["email"],
                defaults={"source": "casting"})
        self.request.session["actor"] = self.actor.pk
        self.request.session["building"] = self.object.pk
        self.request.session["show_ids"] = form.cleaned_data["shows"]
        auditions = []

        if self.actor.is_suspended:
            messages.error(
                self.request,
                "You are currently suspended from Common Casting and cannot " +
                "be cast in productions via Common Casting.")
                                
        for showspace in form.cleaned_data["shows"]:
            i, space = showspace.split(":")
            space = int(space)
            obj, created = Audition.objects.get_or_create(
                actor_id=self.actor.pk, show_id=i,
                defaults={ "space_id": space })
            auditions.append(obj.id)
            if not created:
                if obj.status == Audition.STATUSES[2][0]:
                    messages.error(
                        self.request,
                        "You have already auditioned for {}!".format(
                            CastingMeta.objects.get(id=i)))
                else:
                    if (obj.space_id != space or
                        timezone.localdate(obj.signed_in) !=
                        timezone.localdate()):
                        obj.space_id = space
                        obj.status = Audition.STATUSES[0][0]
                        with suppress_autotime(obj, "signed_in"):
                            obj.signed_in = timezone.now()
                        obj.save()
                    else:
                        send_auditions(Audition, obj)
                        if obj.status == Audition.STATUSES[1][0]:
                            messages.success(
                                self.request,
                                "You have been called to audition for {}!"
                                .format(CastingMeta.objects.get(id=i)))
                        else:
                            if obj.sign_in_complete:
                                messages.warning(
                                    self.request,
                                    "You have already signed in for " +
                                    "{}!".format(
                                        CastingMeta.objects.get(id=i)))
        self.request.session["audition_ids"] = auditions
        return FormView.form_valid(self, form)

    def get_actor(self):
        return self.actor

PROFILE_FIELDS = ["first_name", "last_name", "phone", "affiliation"]
PROFILE_WIDGETS = dict(zip(PROFILE_FIELDS, [
    forms.TextInput(attrs={ "autocomplete": "off" }) for i in range(len(
        PROFILE_FIELDS))]))
PROFILE_WIDGETS["year"] = forms.NumberInput()

class ActorProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = PROFILE_FIELDS + ["year", "pgps", "gender_pref"]
        widgets = PROFILE_WIDGETS
    
class ActorSignInProfile(ActorSignInBase, BaseUpdateView):
    template_name = "casting/sign_in/profile.html"
    form_class = ActorProfileForm
    
    get_object = ActorSignInBase.get_actor

class ActorSeasonMetaForm(forms.ModelForm):
    class Meta:
        model = ActorSeasonMeta
        fields = ("conflicts",)
    
class ActorSignInSeasonMeta(ActorSignInBase, BaseUpdateView):
    template_name = "casting/sign_in/seasonmeta.html"
    form_class = ActorSeasonMetaForm
    
    def get_object(self):
        return Audition.objects.get(
            id=self.request.session.get("audition_ids")[0]).actorseasonmeta
    
class ActorTechForm(forms.ModelForm):
    class Meta:
        model = Audition
        fields = ("tech_interest",)
    
class ActorSignInTech(ActorSignInBase, BaseUpdateView):
    template_name = "casting/sign_in/tech.html"
    form_class = ActorTechForm
    model = Audition

class ActorSignInDone(ActorSignInBase, TemplateView):
    template_name = "casting/sign_in/done.html"
    
    def get(self, *args, **kwargs):
        auditions = Audition.objects.filter(
            id__in=self.request.session.get("audition_ids", []))
        for i in auditions:
            i.sign_in_complete=True
            i.save()
        if "actor" not in self.request.session:
            return redirect(self.actor_missing())
        render_for_user(self.get_actor(), "casting/email/signin-complete.html",
                        "signin-complete",
                        "-".join(self.request.session.get("show_ids", [])),
                        { "auditions": auditions },
                        subject="Common Casting Sign-in Confirmation",
                        tags=["casting", "signin_complete"])
        messages.success(self.request, "You should receive a sign-in " +
                         "confirmation via email shortly.")
        response = super().get(*args, **kwargs)
        try:
            del self.request.session["show_ids"]
            del self.request.session["actor"]
            del self.request.session["audition_ids"]
        except KeyError:
            pass
        return response

class PositionForm(forms.Form):
    latitude = forms.fields.FloatField()
    longitude = forms.fields.FloatField()
    accuracy = forms.fields.FloatField()
    
class ActorSignInPublic(LoginRequiredMixin, FormView):
    template_name = "casting/sign_in/public.html"
    form_class = PositionForm
    
    def form_valid(self, form):
        slots = get_current_slots().filter(
            space__building__latitude__isnull=False,
            space__building__longitude__isnull=False).values_list(
                "space__building", "space__building__latitude",
                "space__building__longitude").distinct()
        for pk, lat, lon in slots:
            latd = form.cleaned_data["latitude"] - lat
            lond = form.cleaned_data["longitude"] - lon
            distance = (latd ** 2 + lond ** 2) ** (0.5)
            if distance < config.get_float("distance_epsilon"):
                self.request.session["located_building"] = pk
                self.request.session["located_building_ts"] = timezone.now()
                return HttpResponseRedirect(reverse("casting:sign_in_start",
                                                    args=(pk,)))
        for pk, lat, lon, name in building_model.objects.filter(
                latitude__isnull=False, longitude__isnull=False).values_list(
                    "pk", "latitude", "longitude", "name"):
            latd = form.cleaned_data["latitude"] - lat
            lond = form.cleaned_data["longitude"] - lon
            distance = (latd ** 2 + lond ** 2) ** (0.5)
            if distance < config.get_float("distance_epsilon", 0):
                messages.success(self.request, "Welcome to {}!".format(name))
        messages.error(
            self.request,
            "You are not at a location currently hosting Common Casting. " +
            "Please try again when you are in the building's lobby.")
        return HttpResponseRedirect(reverse("casting:public_index"))

urlpatterns = [
    url(r'^(?P<pk>\d+)/$', ActorSignInStart.as_view(),
        name="sign_in_start"),
    url(r'^(?P<pk>\d+)/all/$', ActorSignInStart.as_view(show_all=True),
        name="sign_in_start_all"),
    url(r'^(?P<pk>\d+)/popout/$', ActorSignInStart.as_view(popout=True),
        name="sign_in_start_popout"),
    url(r'^profile/$', ActorSignInProfile.as_view(),
        name="sign_in_profile"),
    url(r'^season/$', ActorSignInSeasonMeta.as_view(),
        name="sign_in_seasonmeta"),
    url(r'^season/(?P<pk>\d+)/$', ActorSignInTech.as_view(),
        name="sign_in_tech"),
    url(r'^done/$', ActorSignInDone.as_view(),
        name="sign_in_done"),
    url(r'^location/$', ActorSignInPublic.as_view(), name="sign_in_public")
]
