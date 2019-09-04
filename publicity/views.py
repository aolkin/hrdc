from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

from django import forms
    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from utils import user_is_initialized

class InitializedLoginMixin:
    @method_decorator(login_required)
    @method_decorator(user_is_initialized)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class MenuMixin:
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        current_url = self.request.resolver_match.url_name
        menu = context["sidebar_menu"] = {}
        menu[""] = [{
            "name": "Publicity",
            "url": reverse_lazy("publicity:index"),
            "active": current_url == "index"
        }]
        
        for show in [i for i in
                     self.request.user.show_set.all().order_by("-pk")
                     if hasattr(i, "title")]:
            submenu = menu[str(show)] = []
            is_active = hasattr(self, "object") and self.object.pk == show.pk
            submenu.append({
                "name": "Show Info",
                "url": reverse_lazy("casting:callbacks", args=(show.pk,)),
                "active": is_active and current_url == "info"
            })
            submenu.append({
                "name": "Cast and Staff",
                "url": reverse_lazy("casting:audition", args=(show.pk,)),
                "active": is_active and current_url == "people"
            })
        return context

class IndexView(MenuMixin, InitializedLoginMixin, TemplateView):
    verbose_name = "Show Publicity"
    help_text = "Update your web listing"
    
    template_name = "publicity/index.html"
