from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.list import ListView
from django.views.generic.edit import FormView
from django.views.generic.base import TemplateView
from django.conf.urls import url, include
from django.contrib.auth import get_user_model
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.contrib import messages

from django import forms

from ..models import *
from ..tasks import signing_email

from . import show_model

class FixHeaderUrlMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_authenticated:
            if self.request.user.is_pdsm:
                context["BT_header_url"] = 'casting:index'
        else:
            context["BT_header_url"] = 'casting:public_index'
        return context

class PublicView(FixHeaderUrlMixin, DetailView):
    model = CastingMeta

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["user_is_staff"] = self.object.show.user_is_staff(
            self.request.user)
        context["sidebar_menu"] = {}
        if self.request.user.is_authenticated and self.request.user.is_pdsm:
            submenu = context["sidebar_menu"]["Common Casting"] = []
            submenu.append({
                "name": "Home",
                "url": reverse("casting:index"),
            })
        return context
    
class CallbackView(PublicView):
    template_name = "casting/public/callbacks.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["characters"] = self.object.character_set.filter(
            added_for_signing=False)
        menu = context["sidebar_menu"]
        submenu = menu[self.object.show.seasonstr() + " Callbacks"] = []
        if self.request.user.is_authenticated and self.request.user.is_board:
            filter_args = {}
        else:
            filter_args = {
                "callbacks_submitted": True,
                "release_meta__stage__gt": 0,
            }
        shows = CastingMeta.objects.filter(
            show__year=self.object.show.year,
            show__season=self.object.show.season, **filter_args)
        if shows.exists():
            for i in shows:
                submenu.append({
                    "name": i,
                    "url": reverse("casting:view_callbacks", args=(i.pk,)),
                    "active": self.object.pk == i.pk
                })
        else:
            submenu.append({
                "name": self.object,
                "active": True,
                "url": ""
            })
        return context

class CastView(PublicView):
    template_name = "casting/public/cast.html"
    popout = False
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["base_template"] = ("bt/default.html" if self.popout else
                                    "casting/public/base.html")
        context["popout"] = self.popout
        context["allow_view_first_cast"] = (
            self.object.first_cast_released and
            self.request.user.is_authenticated and self.request.user.is_pdsm)
        context["show_all_actors"] = ((self.object.first_cast_submitted and
                                       context["user_is_staff"]) or
                                      self.object.cast_list_released)
        context["characters"] = self.object.character_set.filter(
            hidden_for_signing=False)
        menu = context["sidebar_menu"]
        submenu = menu[self.object.show.seasonstr() + " Cast Lists"] = []
        if self.request.user.is_authenticated and self.request.user.is_board:
            filter_args = {}
        elif (self.request.user.is_authenticated and
              self.request.user.is_pdsm):
            filter_args = {
                "first_cast_submitted": True,
                "release_meta__stage__gt": 1,
            }
        else:
            filter_args = {
                "cast_submitted": True,
                "release_meta__stage__gt": 2,
            }
        shows = CastingMeta.objects.filter(
            show__year=self.object.show.year,
            show__season=self.object.show.season, **filter_args)
        if shows.exists():
            for i in shows:
                submenu.append({
                    "name": i,
                    "url": reverse("casting:view_cast", args=(i.pk,)),
                    "active": self.object.pk == i.pk
                })
        else:
            submenu.append({
                "name": self.object,
                "active": True,
                "url": ""
            })
        if self.popout:
            del context["sidebar_menu"]
        return context

SIGNING_ACTOR_KEY = "SIGNING_ACTOR_TOKEN_PK_SESSION_KEY"
    
class SigningView(FixHeaderUrlMixin, ListView):
    template_name = "casting/public/sign.html"
    model = Signing

    def get_actor(self):
        if SIGNING_ACTOR_KEY in self.request.session:
            return get_user_model().objects.get(
                pk=self.request.session[SIGNING_ACTOR_KEY])
        elif self.request.user.is_authenticated:
            return self.request.user
        else:
            return None
        
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        all_shows = show_model.objects.current_season().filter(
            casting_meta__isnull=False)
        unpublished = all_shows.filter(
            casting_meta__release_meta__stage__lt=4)
        seconds = all_shows.filter(casting_meta__release_meta__stage__lt=5)
        context["unpublished"] = []
        context["seconds"] = []
        context["wrong_user"] = (self.request.user.is_authenticated and
                                 SIGNING_ACTOR_KEY in self.request.session)
        for key, qs in (("unpublished", unpublished),
                        ("seconds", seconds)):
            for i in qs.distinct().values_list(
                    "casting_meta__release_meta").order_by(
                        "casting_meta__release_meta__signing_opens"):
                context[key].append(
                    CastingReleaseMeta.objects.get(pk=i[0]))
        context["actor"] = self.get_actor()
        return context
            
    def get_queryset(self):
        shows = show_model.objects.current_season().filter(
            casting_meta__isnull=False).filter(
                casting_meta__release_meta__stage__gte=4,
                casting_meta__cast_submitted=True)
        qs = super().get_queryset().filter(
            actor=self.get_actor(), character__show__show__in=shows).order_by(
                "character__show", "order")
        return qs

    def post(self, *args, **kwargs):
        signings = [(int(x.split("-")[-1]), int(y)) for x, y in
                    self.request.POST.items() if
                    x.startswith("signing-response-") and y]
        for pk, r in signings:
            obj = Signing.objects.get(pk=pk)
            if obj.response == None:
                obj.response = r
                obj.save()
        return HttpResponseRedirect(reverse("casting:signing"))

def actor_token_auth(request, token):
    try:
        user = get_user_model().objects.get(login_token=token)
        request.session[SIGNING_ACTOR_KEY] = user.pk
    except Exception:
        messages.error(request, "Please request a new signing link.")
    finally:
        return HttpResponseRedirect(reverse("casting:signing"))

def actor_token_logout(request):
    try:
        del request.session[SIGNING_ACTOR_KEY]
    finally:
        return HttpResponseRedirect(reverse("casting:signing"))

class IndexView(FixHeaderUrlMixin, TemplateView):
    template_name = "casting/public/index.html"

    def get_shows(self):
        return map(lambda x: x.casting_meta,
                   show_model.objects.current_season().filter(
                       casting_meta__isnull=False))
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["shows"] = (("Callback", "casting:view_callbacks", [], "info"),
                            ("Cast", "casting:view_cast", [], "primary"))
        for show in self.get_shows():
            if show.callbacks_released and show.release_meta.stage < 3:
                context["shows"][0][2].append(show)
            if show.cast_list_released:
                context["shows"][1][2].append(show)
        return context

class PKIndexView(SingleObjectMixin, IndexView):
    model = CastingReleaseMeta

    def dispatch(self, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(*args, **kwargs)
    
    def get_shows(self):
        return self.get_object().castingmeta_set.all()

class RequestLinkForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        actor = get_user_model().objects.filter(
            email=self.cleaned_data["email"])
        if actor:
            self.actor = actor[0]
        else:
            raise ValidationError(
                "Could not find anyone with this email address.")
        return self.cleaned_data["email"]
    
    def send_link(self):
        signing_email.delay(self.actor.pk)
    
class RequestLinkView(FixHeaderUrlMixin, FormView):
    template_name = "casting/public/request-link.html"
    form_class = RequestLinkForm
    success_url = reverse_lazy('casting:request_link')
    
    def form_valid(self, form):
        form.send_link()
        messages.success(self.request, "Link sent!")
        return super().form_valid(form)
    
urlpatterns = [
    url(r'^show/(?P<pk>\d+)/', include([
        url(r'^callbacks/$', CallbackView.as_view(),
            name="view_callbacks"),
        url(r'^cast/$', CastView.as_view(),
            name="view_cast"),
        url(r'^cast/popout/$', CastView.as_view(popout=True),
            name="view_cast_popout"),
    ])),
    url(r'^$', IndexView.as_view(), name="public_index"),
    url(r'^(?P<pk>\d+)/$', PKIndexView.as_view(), name="public_index_pk"),
    url(r'^sign/$', SigningView.as_view(), name="signing"),
    url(r'^getlink/$', RequestLinkView.as_view(), name="request_link"),
    url(r'^t/([A-Za-z0-9+-]{86})/$', actor_token_auth, name="actor_token"),
    url(r'^sign/logout/$', actor_token_logout, name="actor_token_logout"),
]
