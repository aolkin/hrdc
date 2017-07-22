from django.views.generic.base import TemplateView, View
from django.views.generic.edit import UpdateView
from django.views.generic.detail import *
from django.urls import reverse, reverse_lazy
from django.conf.urls import url, include
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib import messages

from django.utils import timezone

from ..models import *
from . import get_current_slots, building_model
from ..utils import UserIsPdsmMixin

class StaffViewMixin(UserIsPdsmMixin):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        menu[""] = [{
            "name": "Common Casting",
            "url": reverse("casting:index"),
            "active": current_url == "index"
        }]
        
        for show in [i.casting_meta for i in
                     self.request.user.show_set.current_season()
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
        return context

class IndexView(StaffViewMixin, TemplateView):
    verbose_name = "Common Casting"
    help_text = "audition actors and cast your shows"

    template_name = "casting/index.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        building_ids = (get_current_slots().distinct()
                        .values_list("space__building"))
        context["buildings"] = building_model.objects.filter(
            pk__in=building_ids).values("pk", "name")
        for b in context["buildings"]:
            shows = get_current_slots().filter(
                space__building=b["pk"]).distinct().values_list(
                    "show__show__title")
            b["slots"] = ", ".join([i[0] for i in shows])
        return context

class TablingView(StaffViewMixin, DetailView):
    template_name = "casting/tabling.html"
    model = building_model

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["auditions"] = Audition.objects.filter(
            signed_in__date=timezone.localdate(),
            space__building=self.object).order_by("signed_in")
        return context

class ShowStaffMixin(StaffViewMixin, SingleObjectMixin):
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

class ShowEditor(ShowStaffMixin, UpdateView):
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

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["legal"] = self.test_func()
        return context
    
class AuditionView(ShowStaffMixin, DetailView):
    template_name = "casting/audition.html"

class AuditionStatusBase(StaffViewMixin, SingleObjectMixin, View):
    model = Audition

    def test_func(self):
        return (super().test_func() and
                self.get_object().show.show.user_is_staff(self.request.user))
    
    def get(self, *args, **kwargs):
        self.object = self.get_object()
        self.object.status = self.new_status
        self.object.save()
        if self.request.is_ajax():
            return HttpResponse("success")
        else:
            return HttpResponseRedirect(self.get_redirect_url())
    
    def get_redirect_url(self):
        return reverse("casting:audition", args=(self.object.show.pk,))
    
class AuditionCallView(AuditionStatusBase):
    new_status = "called"

class AuditionDoneView(AuditionStatusBase):
    new_status = "done"

class ActorListView(ShowStaffMixin, DetailView):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["character_blank"] = Character()
        return context

class CallbackView(ActorListView):
    template_name = "casting/callbacks.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["callback_blank"] = Callback()
        context["characters"] = self.object.character_set.filter(
            added_for_signing=False)
        return context
    
    def get(self, *args, **kwargs):
        obj = self.get_object()
        if "CALLBACK_SUBMIT_ERRORS" in self.request.session:
            del self.request.session["CALLBACK_SUBMIT_ERRORS"]
        if "CALLBACK_SUBMIT_FLOW" in self.request.session:
            del self.request.session["CALLBACK_SUBMIT_FLOW"]
        if obj.callbacks_submitted:
            return HttpResponseRedirect(reverse('casting:view_callbacks',
                                                args=(obj.pk,)))
        else:
            return super().get(*args, **kwargs)
    
class CallbackSubmitView(ShowStaffMixin, View):
    def clean_callbacks(self):
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
    
    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if self.clean_callbacks():
            self.request.session["CALLBACK_SUBMIT_FLOW"] = self.object.pk
        else:
            self.request.session["CALLBACK_SUBMIT_ERRORS"] = self.object.pk
        return HttpResponseRedirect(reverse("casting:view_callbacks",
                                            args=(self.object.pk,)))

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        if ("CALLBACK_SUBMIT_FLOW" in self.request.session and
            self.request.session["CALLBACK_SUBMIT_FLOW"] == self.object.pk):
            del self.request.session["CALLBACK_SUBMIT_FLOW"]
            if self.clean_callbacks():
                if "CALLBACK_SUBMIT_ERRORS" in self.request.session:
                    del self.request.session["CALLBACK_SUBMIT_ERRORS"]
                self.object.callbacks_submitted = True
                self.object.save(update_fields=("callbacks_submitted",))
                messages.success(
                    self.request,
                    "Submitted callback list for {} successfully!".format(
                        self.object))
            else:
                self.request.session["CALLBACK_SUBMIT_ERRORS"] = self.object.pk
            return HttpResponseRedirect(reverse("casting:view_callbacks",
                                                args=(self.object.pk,)))
        else:
            messages.error(self.request,
                           "Failed to submit callback list, please try again.")
            return HttpResponseRedirect(reverse("casting:callbacks",
                                                args=(self.object.pk,)))

class CastSubmitView(ShowStaffMixin, View):
    def clean_cast(self):
        if self.object.cast_submitted:
            messages.error(self.request, "Cast list already submitted!")
            return False
        clean = True
        for c in self.object.character_set.all():
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
            elif len(actors) < c.allowed_signers:
                messages.error(
                    self.request,
                    "Not enough actors have been cast as {}. ".format(c) +
                    "Either cast more or decrease the number of allowed " +
                    "signers.")
                clean = False
            elif len(actors) == c.allowed_signers:
                messages.warning(
                    self.request,
                    "No alternates have been provided for {}.".format(c))
        if not self.object.character_set.filter().exists():
            messages.error(self.request,
                           "No characters have been cast!")
            clean = False
        if self.object.character_set.filter(name="").exists():
            messages.error(self.request,
                             "One or more characters are missing names.")
            clean = False
        return clean
    
    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if self.clean_cast():
            self.request.session["CAST_SUBMIT_FLOW"] = self.object.pk
        else:
            self.request.session["CAST_SUBMIT_ERRORS"] = self.object.pk
        return HttpResponseRedirect(reverse("casting:view_cast",
                                            args=(self.object.pk,)))

    def post(self, *args, **kwargs):
        self.object = self.get_object()
        if ("CAST_SUBMIT_FLOW" in self.request.session and
            self.request.session["CAST_SUBMIT_FLOW"] == self.object.pk):
            del self.request.session["CAST_SUBMIT_FLOW"]
            if self.clean_cast():
                if "CAST_SUBMIT_ERRORS" in self.request.session:
                    del self.request.session["CAST_SUBMIT_ERRORS"]
                #self.object.callbacks_submitted = True
                #self.object.save(update_fields=("callbacks_submitted",))
                messages.warning(
                    self.request,
                    "Submitted cast list for {} successfully!".format(
                        self.object))
            else:
                self.request.session["CAST_SUBMIT_ERRORS"] = self.object.pk
            return HttpResponseRedirect(reverse("casting:view_cast",
                                                args=(self.object.pk,)))
        else:
            messages.error(self.request,
                           "Failed to submit cast list, please try again.")
            return HttpResponseRedirect(reverse("casting:cast_list",
                                                args=(self.object.pk,)))

# Disable the default behavior and only display actors who auditioned
ONLY_AUDITIONS = False
    
class ShowActors(ShowStaffMixin, DetailView):
    def get(self, *args, **kwargs):
        if "term" in self.request.GET:
            terms = self.request.GET["term"].split(" ")
        else:
            terms = ("",)
        auditions = self.get_object().audition_set.all()
        for term in terms:
            q = Q(actor__first_name__contains=term)
            q |= Q(actor__last_name__contains=term)
            auditions = auditions.filter(q)
        if ONLY_AUDITIONS or auditions.exists():
            actors = list(auditions.values("actor__id", "actor__first_name",
                                           "actor__last_name"))
            for i in actors:
                i["id"] = i["actor__id"]
                i["text"] = (i["actor__first_name"] + " " +
                             i["actor__last_name"])
        else:
            users = get_user_model().objects.all()
            for term in terms:
                q = Q(first_name__contains=term) | Q(last_name__contains=term)
                users = users.filter(q)
            actors = list(users.values("id", "first_name", "last_name"))
            for i in actors:
                i["text"] = (i["first_name"] + " " + i["last_name"])
        return JsonResponse(actors, safe=False)

class CastListView(ActorListView):
    template_name = "casting/cast_list.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["signing_blank"] = Signing()
        return context
    
class ActorName(UserIsPdsmMixin, BaseDetailView):
    model = get_user_model()

    def get(self, *args, **kwargs):
        user = self.get_object()
        return JsonResponse({
            "id": user.pk,
            "text": user.get_full_name(),
        })
    
urlpatterns = [
    url('^$', IndexView.as_view(), name='index'),
    
    url(r'^show/(?P<pk>\d+)/', include([
        url(r'^edit/$', ShowEditor.as_view(), name="edit_show"),

        url('^actors/$', ShowActors.as_view(), name="show_actors"),
        
        url(r'^auditions/', include([
            url('^$', AuditionView.as_view(), name="audition"),
            url('^call/$', AuditionCallView.as_view(), name="audition_call"),
            url('^done/$', AuditionDoneView.as_view(), name="audition_done")
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
    ])),
    url('^show/\d+/[a-z]+/actor/(?P<pk>\d+)$', ActorName.as_view(),
        name="casting_actor_name"),
    
    url('^building/(?P<pk>\d+)/$', TablingView.as_view(), name="tabling"),
]
