from django.db.models import Q
from django.forms import DateInput, CheckboxSelectMultiple
from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import UpdateView, FormView, FormMixin
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
                    space__isnull=False,
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

SEASONS = list(org.Season.SEASONS)
SEASONS.append((None, '-'))

CREDIT_TYPES = (
    (0, "Creators/Executives"),
    (1, "Staff/Crew"),
    (2, "Cast"),
    (3, "Musicians")
)

class ImprovedDateInput(DateInput):
    input_type = "date"

class SearchForm(forms.Form):
    year = forms.IntegerField(min_value=1900, max_value=2100, required=False)
    season = forms.ChoiceField(choices=SEASONS, required=False)
    title = forms.CharField(required=False)

    residency_date = forms.DateField(required=False, widget=ImprovedDateInput)
    venue = forms.CharField(required=False)
    building = forms.CharField(required=False)
    affiliation = forms.CharField(required=False)
    credit = forms.CharField(required=False)
    credit_type = forms.MultipleChoiceField(choices=CREDIT_TYPES, required=False,
                                            widget=CheckboxSelectMultiple,
                                            help_text="Limit search to the selected type(s) of credit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control-sm"})

class PublicView(FormMixin, ListView):
    verbose_name = "Archives"
    help_text = "view production records"
    template_name = "archive/public_index.html"
    form_class = SearchForm
    model = Show
    paginate_by = 25
    allow_empty = True

    def get_form_kwargs(self):
        return {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
            'data': self.request.GET
        }

    def get_queryset(self):
        form: forms.Form = self.get_form()
        form.full_clean()
        if not form.is_valid():
            return []
        qs = super().get_queryset().filter(space__isnull=False).distinct()
        precise_qs = qs.all()
        for field in form.changed_data:
            value = form.cleaned_data[field]
            if field == "credit_type":
                continue
            elif field == "credit":
                credit_type = form.cleaned_data["credit_type"] if "credit_type" in form.changed_data else []
                q = Q(publicity_info__showperson__type__in=credit_type) if credit_type else Q()
                pq = q
                for word in value.split():
                    q = q & (Q(publicity_info__showperson__person__first_name__icontains=word) |
                             Q(publicity_info__showperson__person__last_name__icontains=word))
                    pq = pq & (Q(publicity_info__showperson__person__first_name__iexact=word) |
                               Q(publicity_info__showperson__person__last_name__iexact=word))
                if '0' in credit_type:
                    q |= Q(publicity_info__credits__icontains=value)
                    pq |= Q(publicity_info__credits__icontains=value)
                print(field, value, q)
            elif field == "venue":
                pq = Q(space__name__iexact=value) | Q(space__nickname__iexact=value)
                if "building" in form.changed_data:
                    q = Q(space__name=value) | Q(space__nickname=value)
                else:
                    q = Q(space__name__icontains=value) | Q(space__nickname__icontains=value) \
                        | Q(space__building__name__icontains=value)
            elif field == "building":
                q = pq = Q(space__building__name=value)
            elif field in ("title", "affiliation"):
                q = Q(**{field + "__icontains": value})
                pq = Q(**{field + "__iexact": value})
            elif field == "residency_date":
                q = pq = Q(residency_starts__lt=value, residency_ends__gt=value)
            else:
                q = pq = Q(**{field: value})
            qs = qs.filter(q)
            precise_qs = precise_qs.filter(pq)

        if precise_qs.exists():
            matches = list(precise_qs)
            qs = qs.exclude(pk__in=[i.pk for i in matches])
            return matches + list(qs)
        else:
            return qs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["existing_query"] = self.request.GET.copy()
        if "page" in data["existing_query"]:
            del data["existing_query"]["page"]
        return data

class PublicDetailView(DetailView):
    template_name = "archive/detail.html"
    model = Show

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        try:
            photos = data["object"].archival_info.productionphoto_set
            data["more_photos_exist"] = photos.private().exists() and not self.request.user.is_authenticated
            data["photos"] = photos.all() if self.request.user.is_authenticated else photos.public()
        except Show.archival_info.RelatedObjectDoesNotExist:
            pass
        return data
