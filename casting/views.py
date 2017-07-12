from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic.base import *
from django.views.generic.edit import *

from django.urls import reverse_lazy, reverse
from django.db.models import Q

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib import messages


from django import forms
from django.apps import apps
from django.conf import settings
from django.utils import timezone
import datetime

from config import config

from .models import *

def test_pdsm(user):
    return user.is_authenticated() and user.is_pdsm

def test_board(user):
    return user.is_authenticated() and user.is_board

class ShowEditor(UpdateView):
    model = CastingMeta
    fields = ("contact_email",)
    success_url = reverse_lazy("casting:index")
    template_name = "casting/show_editor.html"
    
    def test_func(self):
        return (self.request.user.is_authenticated() and
                self.get_object().show.staff.filter(
                    id=self.request.user.id).exists())

    def post(self, *args, **kwargs):
        if self.test_func():
            return super().post(*args, **kwargs)
        else:
            messages.error(self.request, "You do not have access to that show.")
            return HttpResponseRedirect(reverse("login"))
        
    def get(self, *args, **kwargs):
        if not self.request.is_ajax():
            return HttpResponseRedirect(reverse("casting:index"))
        else:
            return super().get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["legal"] = self.test_func()
        return context

show_model = apps.get_model(settings.SHOW_MODEL)
building_model = (apps.get_model(settings.SPACE_MODEL)
                  .building.field.related_model)

def get_current_slots():
    return Slot.objects.auditions().filter(
        day=timezone.localdate(),
        start__lte=timezone.localtime(),
        end__gte=timezone.localtime())

@login_required
def index(request):
    building_ids = (get_current_slots().distinct()
                    .values_list("space__building"))
    buildings = building_model.objects.filter(pk__in=building_ids).values(
        "pk", "name")
    for b in buildings:
        shows = get_current_slots().filter(
            space__building=b["pk"]).distinct().values_list(
                "show__show__title")
        b["slots"] = ", ".join([i[0] for i in shows])
    return render(request, "casting/index.html", locals())
index.verbose_name = "Common Casting"
index.help_text = "audition actors and cast your shows"

@user_passes_test(test_board)
def admin(request):
    return render(request, "bt/default.html")
admin.verbose_name = "Common Casting"
admin.help_text = "administer Common Casting"

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

class ActorSignInBase(UserPassesTestMixin, TemplateResponseMixin):
    popout = False

    def test_func(self):
        return test_pdsm(self.request.user)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["BT_header_url"] = None
        self.request.session["popout"] = self.popout
        context["shows"] = CastingMeta.objects.filter(
            id__in=self.request.session.get("show_ids",[]))
        return context

class ActorSignInStart(ActorSignInBase, BaseUpdateView):
    form_class = SignInStartForm
    model = building_model
    template_name = "casting/sign_in/start.html"
    show_all = False

    def get_success_url(self):
        if self.actor_is_initialized:
            return reverse("casting:sign_in_done")
        else:
            return reverse("casting:sign_in_profile")

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.show_all:
            q = Q(day=timezone.localdate(), start__gte=datetime.time(hour=9))
            q |= Q(day=timezone.localdate() - datetime.timedelta(days=1),
                   end__gt=datetime.time(hour=21))
            slots = Slot.objects.auditions().filter(
                q, space__building=self.object)
        else:
            slots = get_current_slots().filter(space__building=self.object)
        context["shows"] = slots.distinct().values_list("show__show__title",
                                                        "show__id")
        return context
        
    def form_valid(self, form):
        actor, created = get_user_model().objects.get_or_create(
            email=form.cleaned_data["email"],
            defaults={"source": "casting"})
        self.request.session["actor"] = actor.pk
        self.request.session["building"] = self.object.pk
        self.request.session["show_ids"] = form.cleaned_data["shows"]
        self.actor_is_initialized = actor.is_initialized
        return FormView.form_valid(self, form)

PROFILE_FIELDS = ["first_name", "last_name", "phone",]
PROFILE_WIDGETS = dict(zip(PROFILE_FIELDS, [
    forms.TextInput(attrs={ "autocomplete": "off" }) for i in range(len(
        PROFILE_FIELDS))]))
print(PROFILE_WIDGETS)

class ActorProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = PROFILE_FIELDS + ["pgps"]
        widgets = PROFILE_WIDGETS
    
class ActorSignInProfile(ActorSignInBase, BaseUpdateView):
    template_name = "casting/sign_in/profile.html"
    form_class = ActorProfileForm
    success_url = reverse_lazy("casting:sign_in_done")

    def get_object(self, *args, **kwargs):
        return get_user_model().objects.get(pk=self.request.session["actor"])
    
class ActorSignInDone(ActorSignInBase, TemplateView):
    template_name = "casting/sign_in/done.html"
    
    def get(self, *args, **kwargs):
        for i in self.request.session.get("show_ids", []):
            obj, created = Audition.objects.get_or_create(
                actor_id=self.request.session["actor"], show_id=i)
            if not created:
                if obj.status == Audition.STATUSES[2][0]:
                    messages.error(self.request,
                                     "You have already auditioned for {}!"
                                     .format(
                                         CastingMeta.objects.get(id=i)))
                else:
                    messages.warning(self.request,
                                     "You have already signed in for {}!"
                                     .format(
                                         CastingMeta.objects.get(id=i)))
        response = super().get(*args, **kwargs)
        try:
            del self.request.session["show_ids"]
            del self.request.session["actor"]
        except KeyError:
            pass
        return response
