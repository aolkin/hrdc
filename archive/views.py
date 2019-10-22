from django.shortcuts import render
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django import forms
from django.contrib import messages
    
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from utils import user_is_initialized

from django.conf import settings

import os, logging
logger = logging.getLogger(__name__)

import dramaorg.models as org

from .models import *

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
            "name": "Archival Tool",
            "url": reverse_lazy("archive:index"),
            "active": current_url == "index"
        }]

        if self.request.user.is_anonymous:
            return context

        shows = [i.archival_info for i in
                 self.request.user.show_set.all().order_by("-pk")
                 if hasattr(i, "archival_info")]
        urls = [
            ("Manage Show", "archive:show"),
            ("Upload Materials", "archive:upload"),
        ]
        
        for show in shows:
            submenu = menu[str(show)] = []
            is_active = (hasattr(self, "object") and
                         self.object.pk == show.pk)
            for name, url in urls:
                submenu.append({
                    "name": name,
                    "url": reverse_lazy(url, args=(show.pk,)),
                    "active": is_active and current_url == url.split(":")[-1]
                })
            if show.is_published:
                submenu.append({
                    "name": "[Public Page]",
                    "url": reverse_lazy("archive:public", args=(show.pk,)),
                    "active": False
                })
        
        return context

class ShowStaffMixin(InitializedLoginMixin, SingleObjectMixin):
    model = ArchivalInfo
    
    test_silent = False
    
    def test_func(self):
        if super().test_func():
            if self.get_object().user_is_staff(self.request.user):
                return True
            else:
                if not self.test_silent:
                    messages.error(self.request, "You are not a member of the "
                                   "executive staff of that show. Log in as a "
                                   "different user?")
        return False

class IndexView(MenuMixin, InitializedLoginMixin, TemplateView):
    verbose_name = "Archival Tool"
    help_text = "upload archival materials"
    template_name = "archive/index.html"

    def get(self, *args, **kwargs):
        if not self.request.user.is_anonymous:
            for i in self.request.user.show_set.filter(
                    archival_info__isnull=True):
                ArchivalInfo(show=i).save()
        return super().get(*args, **kwargs)

class ShowForm(forms.ModelForm):
    class Meta:
        model = ArchivalInfo
        fields = "poster", "program",
        widgets = {
            'poster': forms.FileInput(),
            'program': forms.FileInput(),
        }

class ShowView(MenuMixin, ShowStaffMixin, UpdateView):
    template_name = "archive/show.html"
    model = ArchivalInfo
    form_class = ShowForm

class UploadView(MenuMixin, ShowStaffMixin, DetailView):
    template_name = "archive/upload.html"
    model = ArchivalInfo

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        for f in request.FILES.getlist("files"):
            ExtraFile.objects.create(file=f, show=obj,
                                     credit=request.POST.get("file-credit"),
                                     description=request.POST.get("file-desc"))
        for f in request.FILES.getlist("photos"):
            try:
                ProductionPhoto.objects.create(
                    img=f, show=obj, credit=request.POST.get("photo-credit"),
                    allow_in_publicity=bool(
                        request.POST.get("allow_in_publicity")))
            except Exception as err:
                logger.exception("Photo upload failed: {}".format(f))
                messages.error(
                    request, "Failed to upload photo '{}'.".format(f))
        return redirect(self.get_object().get_absolute_url())

class PublicView(DetailView):
    template_name = "archive/public.html"
    model = ArchivalInfo
