from django.views.generic.base import TemplateView, View
from django.views.generic.edit import UpdateView
from django.views.generic.detail import *
from django.urls import reverse, reverse_lazy
from django.conf.urls import url, include
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Q
from django.shortcuts import render
from django.contrib import messages

from django.utils import timezone

import csv

from config import config

from chat.models import Message

from ..models import *
from . import get_current_slots, get_active_slot, building_model, show_model
from ..utils import UserIsPdsmMixin, UserIsSeasonPdsmMixin, test_spdsm
from . import public

class StaffViewMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        menu[""] = [{
            "name": "Common Casting",
            "url": reverse("casting:index"),
            "active": current_url == "index"
        }]
        
        if (self.request.user.is_season_pdsm or self.request.user.has_perm(
                "casting.table_auditions")) and get_current_slots().exists():
            submenu = menu["Sign-in Tabling"] = []
            for pk, name in (get_current_slots().distinct()
                            .values_list("space__building__pk",
                                         "space__building__name")):
                is_active = hasattr(self, "object") and self.object.pk == pk
                submenu.append({
                    "name": name,
                    "url": reverse("casting:tabling", args=(pk,)),
                    "active": is_active and current_url == "tabling"
                })
        for show in [i.casting_meta for i in
                     self.request.user.show_set.all().order_by("-pk")
                     if hasattr(i, "casting_meta")]:
            submenu = menu[str(show)] = []
            is_active = hasattr(self, "object") and self.object.pk == show.pk
            submenu.append({
                "name": "Auditions",
                "url": reverse("casting:audition", args=(show.pk,)),
                "active": is_active and current_url == "audition"
            })
            submenu.append({
                "name": "Callbacks",
                "url": reverse("casting:callbacks", args=(show.pk,)),
                "active": is_active and current_url == "callbacks"
            })
            if show.release_meta.stage > 0:
                submenu.append({
                    "name": "Cast List",
                    "url": reverse("casting:cast_list", args=(show.pk,)),
                    "active": is_active and current_url == "cast_list"
                })
            if show.tech_req_contributor_set.exists():
                submenu.append({
                    "name": "Tech Reqs",
                    "url": reverse("casting:tech_reqs", args=(show.pk,)),
                    "active": is_active and current_url == "tech_reqs"
                })
        return context

class IndexView(StaffViewMixin, UserIsPdsmMixin, TemplateView):
    verbose_name = "Common Casting"
    help_text = "audition actors and cast your shows"

    template_name = "casting/index.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_season_pdsm or self.request.user.has_perm(
                "casting.table_auditions"):
            building_ids = (get_current_slots().distinct()
                            .values_list("space__building"))
            context["buildings"] = building_model.objects.filter(
                pk__in=building_ids).values("pk", "name")
            for b in context["buildings"]:
                shows = get_current_slots().filter(
                    space__building=b["pk"]).distinct().values_list(
                        "show__show__title")
                b["slots"] = ", ".join([i[0] for i in shows])
        if self.request.user.is_season_pdsm or self.request.user.has_perm(
                "casting.view_first_cast_lists"):
            context["first_cast_lists"] = []
            shows = show_model.objects.current_season().filter(
                casting_meta__isnull=False)
            for show in shows:
                if (show.casting_meta.first_cast_submitted and
                    show.casting_meta.release_meta.stage == 2):
                    context["first_cast_lists"].append(show.casting_meta)
        return context

class TablingView(StaffViewMixin, UserIsSeasonPdsmMixin, DetailView):
    template_name = "casting/tabling.html"
    model = building_model

    def dispatch(self, *args, **kwargs):
        if "located_building" in self.request.session:
            del self.request.session["located_building"]
        return super().dispatch(*args, **kwargs)
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["auditions"] = Audition.objects.filter(
            signed_in__date=timezone.localdate(),
            sign_in_complete=True,
            space__building=self.object).order_by("signed_in")
        context["chat_building"] = self.object
        context["chat_messages"] = Message.objects.filter(
            room="building-{}-{}".format(
                self.object.pk, timezone.localdate())).order_by(
                    "-timestamp")[:settings.CHAT_LOADING_LIMIT:-1]
        return context

class ShowStaffMixin(StaffViewMixin, UserIsPdsmMixin, SingleObjectMixin):
    model = CastingMeta
    
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

class ShowEditor(ShowStaffMixin, UserIsPdsmMixin, UpdateView):
    fields = ("contact_email",)
    success_url = reverse_lazy("casting:index")
    template_name = "casting/show_editor.html"
    
    def post(self, *args, **kwargs):
        if self.test_func():
            return super().post(*args, **kwargs)
        else:
            messages.error(self.request,
                           "You do not have access to that show.")
            return HttpResponseRedirect(reverse("login"))

    def get(self, *args, **kwargs):
        if not self.request.is_ajax():
            return HttpResponseRedirect(reverse("casting:index"))
        else:
            return super().get(*args, **kwargs)

    def form_invalid(self, form):
        messages.error(self.request,
                       "Please provide a valid email address for {}.".format(
                       self.object))
        return HttpResponseRedirect(reverse("casting:index"))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["legal"] = self.test_func()
        return context
    
class AuditionView(ShowStaffMixin, UserIsPdsmMixin, DetailView):
    template_name = "casting/audition.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        active_slot = get_active_slot(self.object.pk)
        context["chat_building"] = (active_slot.space.building if active_slot
                                    else 0)
        context["chat_messages"] = Message.objects.filter(
            room="building-{}-{}".format(
                context["chat_building"].pk if context["chat_building"] else 0,
                timezone.localdate())).order_by("-timestamp")[
                    :settings.CHAT_LOADING_LIMIT:-1]
        return context

class ExportView(ShowStaffMixin, UserIsPdsmMixin, DetailView):
    def get_objects(self):
        return (self.get_object(),)
    
    def get(self, *args, **kwargs):
        response = HttpResponse(content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="{}_{}s_{}.csv"'.format(
            self.get_object().show.slug,
            self.obj_,
            timezone.localtime(timezone.now()).strftime("%Y-%m-%d_%H%M%S"))
        writer = csv.writer(response)
        objects = self.get_objects()
        writer.writerow([
            "Sign-in Time", "Name", "Email", "Phone", "Affiliation", "Year",
            "PGPs", "Preferred Stage Gender"
        ] + (["Conflicts", "Tech Interest"] if self.obj_ == "audition" else
             ["Cast by Show"]))
        for i in objects:
            writer.writerow([
                i.signed_in if hasattr(i, "signed_in") else "",
                i.actor.get_full_name(False),
                i.actor.email,
                i.actor.phone,
                i.actor.affiliation,
                i.actor.year,
                i.actor.pgps,
                i.actor.gender_pref
            ] + ([
                i.actorseasonmeta.conflicts if hasattr(
                    i, "actorseasonmeta") else "",
                i.tech_interest if hasattr(i, "tech_interest") else ""
            ] if type(i) == Audition else [i.character.show]))
        return response

class AuditionExportView(ExportView):
    obj_ = "audition"
    def get_objects(self):
        return self.get_object().audition_set.all().order_by("signed_in")
        
class TechReqExportView(ExportView):
    obj_ = "techreq"
    def get_objects(self):
        return self.get_object().tech_reqers.all()
    
class AuditionStatusBase(StaffViewMixin, SingleObjectMixin, View):
    model = Audition

    def test_func(self):
        return (super().test_func() and
                self.get_object().show.show.user_is_staff(self.request.user))
    
    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.busy:
            self.object.status = self.new_status
            setattr(self.object, self.new_status + "_time", timezone.now())
            self.object.save()
        if self.request.is_ajax():
            return HttpResponse("success" if not self.object.busy else "failed")
        else:
            return HttpResponseRedirect(self.get_redirect_url())
    
    def get_redirect_url(self):
        return reverse("casting:audition", args=(self.object.show.pk,))
    
class AuditionCallView(AuditionStatusBase):
    new_status = "called"

class AuditionDoneView(AuditionStatusBase):
    new_status = "done"
    
class AuditionCancelView(AuditionStatusBase):
    new_status = "waiting"

def clear_session_vars(session, name):
    for i in ("{}_SUBMIT_ERRORS", "{}_SUBMIT_FLOW"):
        var = i.format(name)
        if var in session:
            del session[var]
                
class ActorListView(ShowStaffMixin, UserIsPdsmMixin, DetailView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["character_blank"] = Character()
        return context

    def inline_public(self, view):
        view.object = self.object
        view.request = self.request
        ctx = view.get_context_data()
        ctx["sidebar_menu"] = self.get_context_data()["sidebar_menu"]
        return render(self.request, view.template_name, ctx)
                
class CallbackView(ActorListView):
    template_name = "casting/callbacks.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["callback_blank"] = Callback()
        context["characters"] = self.object.character_set.filter(
            added_for_signing=False)
        return context
    
    def get(self, *args, **kwargs):
        clear_session_vars(self.request.session, "CALLBACK")
        self.object = self.get_object()
        if self.object.callbacks_submitted:
            return self.inline_public(public.CallbackView())
        else:
            return super().get(*args, **kwargs)

class CastListView(ActorListView):
    template_name = "casting/cast_list.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["signing_blank"] = Signing()
        return context
       
    def get(self, *args, **kwargs):
        clear_session_vars(self.request.session, "CAST")
        self.object = self.get_object()
        if self.object.cast_submitted:
            return self.inline_public(public.CastView())
        else:
            return super().get(*args, **kwargs)
            
class SubmitView(ShowStaffMixin, UserIsPdsmMixin, View): 
    def get(self, *args, **kwargs):
        self.object = self.get_object()
        clear_session_vars(self.request.session, self.var_name)
        if self.clean():
            self.request.session["{}_SUBMIT_FLOW".format(
                self.var_name)] = self.object.pk
        else:
            self.request.session["{}_SUBMIT_ERRORS".format(
                self.var_name)] = self.object.pk
        return HttpResponseRedirect(reverse(self.redirect_url,
                                            args=(self.object.pk,)))
        
    def post(self, *args, **kwargs):
        self.object = self.get_object()
        if ("{}_SUBMIT_FLOW".format(self.var_name) in self.request.session and
            self.request.session["{}_SUBMIT_FLOW".format(
                self.var_name)] == self.object.pk):
            del self.request.session["{}_SUBMIT_FLOW".format(self.var_name)]
            if self.clean(False):
                if "{}_SUBMIT_ERRORS".format(
                        self.var_name) in self.request.session:
                    del self.request.session["{}_SUBMIT_ERRORs".format(
                        self.var_name)]
                self.do_save()
            else:
                self.request.session["{}_SUBMIT_ERRORS".format(
                    self.var_name)] = self.object.pk
            return HttpResponseRedirect(reverse(self.edit_url,
                                                args=(self.object.pk,)))
        else:
            messages.error(self.request,
                           "Failed to submit {}, please try again.".format(
                               getattr(self, "verbose_name", "")))
            return HttpResponseRedirect(reverse(self.edit_url,
                                                args=(self.object.pk,)))

class CallbackSubmitView(SubmitView):
    var_name = "CALLBACK"
    redirect_url = "casting:view_callbacks"
    edit_url = "casting:callbacks"
    verbose_name = "Callback List"
    
    def clean(self, warn=True):
        if self.object.callbacks_submitted:
            messages.error(self.request, "Callbacks already submitted!")
            return False
        clean = True
        for c in self.object.character_set.filter(added_for_signing=False):
            actors = []
            for cb in c.callback_set.all().select_related("actor"):
                if not cb.actor:
                    cb.delete()
                elif cb.actor.pk in actors:
                    cb.delete()
                    messages.warning(
                        self.request,
                        "{} is called for {} multiple times; ".format(
                            cb.actor, c) + "removing duplicate.")
                    clean = False
                else:
                    actors.append(cb.actor.pk)
            if len(actors) < 1:
                if not (c.name or c.callback_description):
                    messages.info(self.request,
                                  "Found empty character; removing.")
                    c.delete()
                else:
                    messages.error(
                        self.request, "No one is called for {}.".format(c))
                    clean = False
        if not self.object.character_set.filter(
                added_for_signing=False).exists():
            messages.error(self.request,
                           "No callbacks have been listed!")
            clean = False
        if self.object.character_set.filter(added_for_signing=False,
                                            name="").exists():
            messages.warning(self.request,
                             "One or more characters are missing names.")
            clean = False
        return clean

    def do_save(self):
        self.object.callbacks_submitted = True
        self.object.save(update_fields=("callbacks_submitted",))
        messages.success(
            self.request,
            "Submitted callback list for {} successfully!".format(
                self.object))

class CastSubmitView(SubmitView):
    var_name = "CAST"
    redirect_url = "casting:view_cast"
    edit_url = "casting:cast_list"
    verbose_name = "Cast List"
    
    def clean(self, warn=True):
        if self.object.cast_submitted:
            messages.error(self.request, "Cast list already submitted!")
            return False
        clean = True
        characters = self.object.character_set.filter(hidden_for_signing=False)
        for c in characters.all():
            actors = []
            for signing in c.signing_set.all().select_related("actor"):
                if not signing.actor:
                    signing.delete()
                elif signing.actor.pk in actors:
                    signing.delete()
                    messages.info(
                        self.request,
                        "{} is cast as {} multiple times; ".format(
                            signing.actor, c) + "removing duplicate.")
                    clean = False
                else:
                    actors.append(signing.actor.pk)
            if len(actors) < 1:
                if (not c.name) and c.allowed_signers == 1:
                    messages.info(self.request,
                                  "Found empty character; removing.")
                    c.delete()
                else:
                    messages.error(
                        self.request,
                        "No actors have been cast as {}.".format(c))
                    clean = False
            elif len(actors) < c.allowed_signers:
                messages.error(
                    self.request,
                    "Not enough actors have been cast as {}. ".format(c) +
                    "Either cast more or decrease the number of allowed " +
                    "signers.")
                clean = False
            elif len(actors) == c.allowed_signers and warn:
                if self.object.first_cast_submitted:
                    messages.warning(
                        self.request,
                        "No alternates have been provided for {}.".format(c))
        if not characters.exists():
            messages.error(self.request,
                           "No characters have been cast!")
            clean = False
        if characters.filter(name="").exists():
            messages.error(self.request,
                             "One or more characters are missing names.")
            clean = False
        return clean

    def do_save(self):
        if self.object.first_cast_submitted:
            self.object.cast_submitted = True
        else:
            self.object.first_cast_submitted = True
        self.object.save(update_fields=("first_cast_submitted",
                                        "cast_submitted"))
        messages.success(
            self.request,
            "Submitted {} for {} successfully!".format(
                "cast list" if self.object.cast_submitted else
                "first-round casting", self.object))
    
class ShowActors(ShowStaffMixin, UserIsPdsmMixin, DetailView):
    def get(self, *args, **kwargs):
        if "term" in self.request.GET:
            terms = self.request.GET["term"].split(" ")
        else:
            terms = ("",)
        
        auditions = self.get_object().audition_set.filter(
            Q(actor__suspended_until__lte=timezone.localdate()) |
            Q(actor__suspended_until__isnull=True),
            sign_in_complete=True)
        for term in terms:
            q = Q(actor__first_name__icontains=term)
            q |= Q(actor__last_name__icontains=term)
            auditions = auditions.filter(q)
        if config.get("only_auditioners",
                      "no").lower() == "yes" or auditions.exists():
            actors = list(auditions.values("actor__id", "actor__first_name",
                                           "actor__last_name"))
            for i in actors:
                i["id"] = i["actor__id"]
                i["text"] = (i["actor__first_name"] + " " +
                             i["actor__last_name"])
        else:
            users = get_user_model().objects.filter(
                Q(suspended_until__lte=timezone.localdate()) |
                Q(suspended_until__isnull=True))
            for term in terms:
                q = Q(first_name__icontains=term) | Q(last_name__icontains=term)
                users = users.filter(q)
            actors = list(users.values("id", "first_name", "last_name"))
            for i in actors:
                i["text"] = (i["first_name"] + " " + i["last_name"])
        return JsonResponse(actors, safe=False)
 
class ActorName(UserIsPdsmMixin, BaseDetailView):
    model = get_user_model()

    def get(self, *args, **kwargs):
        user = self.get_object()
        return JsonResponse({
            "id": user.pk,
            "text": user.get_full_name(),
        })

class TechReqView(ShowStaffMixin, UserIsPdsmMixin, DetailView):
    template_name = "casting/tech_reqs.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        return context
    
urlpatterns = [
    url('^$', IndexView.as_view(), name='index'),
    
    url(r'^show/(?P<pk>\d+)/', include([
        url(r'^edit/$', ShowEditor.as_view(), name="edit_show"),

        url('^actors/$', ShowActors.as_view(), name="show_actors"),
        
        url(r'^auditions/', include([
            url('^$', AuditionView.as_view(), name="audition"),
            url('^call/$', AuditionCallView.as_view(), name="audition_call"),
            url('^cancel/$', AuditionCancelView.as_view(),
                name="audition_cancel"),
            url('^done/$', AuditionDoneView.as_view(), name="audition_done"),
            url('^export/$', AuditionExportView.as_view(),
                name="audition_export"),
        ])),
        
        url(r'^callbacks/', include([
            url('^$', CallbackView.as_view(), name="callbacks"),
            url('^submit/$', CallbackSubmitView.as_view(),
                name="callback_submit"),
        ])),
        
        url(r'^cast/', include([
            url('^$', CastListView.as_view(), name="cast_list"),
            url('^submit/$', CastSubmitView.as_view(), name="cast_submit"),
        ])),
        
        url(r'^techreqs/', include([
            url('^$', TechReqView.as_view(), name="tech_reqs"),
            url('^export/$', TechReqExportView.as_view(),
                name="tech_req_export"),
        ])),
    ])),
    url('^show/\d+/[a-z]+/actor/(?P<pk>\d+)$', ActorName.as_view(),
        name="casting_actor_name"),
    
    url('^building/(?P<pk>\d+)/$', TablingView.as_view(), name="tabling"),
]
