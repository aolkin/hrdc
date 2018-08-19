
from django.views.generic.base import *
from django.views.generic.edit import *
from django.http import JsonResponse

from django.urls import reverse_lazy, reverse
from django.db.models import Q

from django.contrib.auth import get_user_model
from django.contrib import messages

from django.conf.urls import url

from django import forms
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
import datetime

from ..models import *
from . import get_current_slots, building_model
from ..utils import UserIsPdsmMixin, suppress_autotime

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

class ActorSignInBase(UserIsPdsmMixin, TemplateResponseMixin):
    popout = False

    def get_success_url(self):
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
        return context
    
    def form_valid(self, form):
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
                        obj.signed_in.date() != timezone.localdate()):
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
        for i in Audition.objects.filter(
            id__in=self.request.session.get("audition_ids", [])):
            i.sign_in_complete=True
            i.save()
        # Email sign-in confirmation here
        response = super().get(*args, **kwargs)
        try:
            del self.request.session["show_ids"]
            del self.request.session["actor"]
            del self.request.session["audition_ids"]
        except KeyError:
            pass
        return response

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
        name="sign_in_done")]
