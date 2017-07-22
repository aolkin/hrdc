from django.views.generic.detail import DetailView
from django.conf.urls import url, include
from django.urls import reverse

from ..models import *

class PublicView(DetailView):
    model = CastingMeta

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if self.request.user.is_authenticated():
            if self.request.user.is_pdsm:
                context["BT_header_url"] = 'casting:index'
        else:
            context["BT_header_url"] = None
        context["user_is_staff"] = self.object.show.user_is_staff(
            self.request.user)
        context["sidebar_menu"] = {}
        if self.request.user.is_authenticated() and self.request.user.is_pdsm:
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
        if self.request.user.is_authenticated() and self.request.user.is_board:
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
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["allow_view_first_cast"] = (
            self.object.first_cast_released and
            self.request.user.is_authenticated() and self.request.user.is_pdsm)
        context["show_all_actors"] = ((self.object.first_cast_submitted and
                                       context["user_is_staff"]) or
                                      self.object.cast_list_released)
        menu = context["sidebar_menu"]
        submenu = menu[self.object.show.seasonstr() + " Cast Lists"] = []
        if self.request.user.is_authenticated() and self.request.user.is_board:
            filter_args = {}
        elif (self.request.user.is_authenticated() and
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
        return context

urlpatterns = [
    url(r'^show/(?P<pk>\d+)/', include([
        url(r'^callbacks/$', CallbackView.as_view(),
            name="view_callbacks"),
        url(r'^cast/$', CastView.as_view(),
            name="view_cast"),
    ])),
]
