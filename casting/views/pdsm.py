
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import UpdateView
from django.views.generic.detail import *
from django.urls import reverse
from django.conf.urls import url
from django.http import HttpResponseRedirect, HttpResponse

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
            submenu.append({
                "name": "Cast List",
                "url": "#",
                "active": False
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
            space__building=self.object)
        return context

class ShowStaffMixin(StaffViewMixin):
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

class CallbackView(ShowStaffMixin, DetailView):
    template_name = "casting/callbacks.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["character_blank"] = Character()
        return context
    
urlpatterns = [
    url('^$', IndexView.as_view(), name='index'),
    url('^building/(?P<pk>\d+)/$', TablingView.as_view(), name="tabling"),
    
    url('^auditions/(?P<pk>\d+)/$', AuditionView.as_view(), name="audition"),
    url('^auditions/(?P<pk>\d+)/call/$', AuditionCallView.as_view(),
        name="audition_call"),
    url('^auditions/(?P<pk>\d+)/done/$', AuditionDoneView.as_view(),
        name="audition_done"),
    
    url('^callbacks/(?P<pk>\d+)/$', CallbackView.as_view(),
        name="callbacks"),
]
