from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from django import forms
from django.contrib import messages

from .mailer import targets

class _DummyMessage:
    def __getattr__(self, attr):
        return self

    def __call__(self, *args, **kwargs):
        return

def preview(request):
    context = {
        "IS_HTML": int(request.GET.get("html", 1)),
        "MESSAGE": _DummyMessage(),
        "SUBJECT": "Email Preview",
    }
    return render(request, request.GET["template"], context)

class TargetsForm(forms.Form):
    def get_targets():
        return [(key, val.verbose_name) for key, val in targets.items()]
    target = forms.ChoiceField(choices=get_targets)

class EmailerView(TemplateView):
    verbose_name = _("Mail Merge")
    help_text = "email users, staffs, et al"

    template_name = "emailtracker/emailer.html"

    def get_target(self):
        if "target" in self.request.GET:
            target = targets.get(self.request.GET["target"], None)
            if target:
                if target.permission:
                    if not self.request.user.has_perm(target.permission):
                        raise PermissionDenied()
                self.target = target()
            else:
                raise Http404("Mail merge target not found.")
        else:
            self.target = None
        return self.target

    def dispatch(self, *args, **kwargs):
        self.get_target()
        if not self.request.user.is_staff:
            raise PermissionDenied()
        return super().dispatch(*args, **kwargs)

    def get_form(self):
        form_args = self.target.get_form_args(
            self.request) if self.target else {}
        if self.request.method in ('POST', 'PUT'):
            form_args.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return (self.target.form_class(**form_args) if self.target else
                TargetsForm(**form_args))

    def get_context_data(self, **kwargs):
        kwargs["target"] = self.target
        if not "form" in kwargs:
            kwargs["form"] = self.get_form()
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        if not self.target:
            return redirect(request.path)
        form = self.get_form()
        if form.is_valid():
            emails = self.target.get_emails(form)
            if request.POST["form_action"] == "Preview":
                return self.render_to_response(
                    self.get_context_data(form=form, emails=emails))
            elif request.POST["form_action"] == "Send Test to Yourself":
                res = self.target.send_preview(
                    self.target.get_emails(form), form, request.user)
                if res:
                    messages.success(request, "Sent first previewed email as test email - check your inbox!")
                else:
                    messages.error(request, "Failed to send test email!")
                return self.render_to_response(
                    self.get_context_data(form=form, emails=emails))
            elif request.POST["form_action"] == "Send":
                count = self.target.send(emails, form)
                messages.success(request, "Sent {} emails!".format(count))
                return self.render_to_response(
                    self.get_context_data(form=form, emails=emails))
                return redirect(request.path)
        return self.render_to_response(self.get_context_data(form=form))
