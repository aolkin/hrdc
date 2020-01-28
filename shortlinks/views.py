from django.shortcuts import redirect, get_object_or_404
from django.views.generic.edit import FormView
from django import forms
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.conf import settings

import urllib.parse

from dramaorg.mixins import UserIsPdsmMixin

from config import config

from .models import Link

def link(request, slug):
    l = get_object_or_404(Link, url=slug)
    if config.add_utm_to_shortlinks == "yes":
        sep = "&" if "?" in l.destination else "?"
        return redirect(
            l.destination + sep +
            "utm_medium=referral&utm_source=shortlink&utm_campaign={}".format(
                urllib.parse.quote_plus(l.url)))
    else:
        return redirect(l.destination)

LinkFormSet = forms.inlineformset_factory(
    get_user_model(), Link, fields=("url", "destination"),
    extra=1, can_delete=False)

class LinksView(UserIsPdsmMixin, FormView):
    verbose_name = "Shortlinks"
    help_text = "create {} links".format(settings.SHORTLINK_PREFIX.strip("/"))

    template_name = "shortlinks/editor.html"
    model = Link
    form_class = LinkFormSet
    success_url = reverse_lazy("shortlinks:index")

    def get_form(self, instance=None):
        return self.form_class(
            **self.get_form_kwargs(),
            instance=self.request.user
        )

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
