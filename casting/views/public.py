from django.views.generic.detail import DetailView
from django.conf.urls import url
from django.urls import reverse

from ..models import *

class CallbackView(DetailView):
    model = CastingMeta
    template_name = "casting/public/callbacks.html"
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["BT_header_url"] = None
        context["user_is_staff"] = self.object.show.user_is_staff(
            self.request.user)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        submenu = menu["Callbacks by Show"] = []
        submenu.append({
            "name": self.object,
            "url": reverse("casting:view_callbacks", args=(self.object.pk,)),
            "active": self.object.pk == self.object.pk
        })
        return context

urlpatterns = [
    url(r'^callbacks/(?P<pk>\d+)/', CallbackView.as_view(),
        name="view_callbacks"),
]
