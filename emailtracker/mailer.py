
from django import forms
from django.template import Template, Context
from django.utils.html import mark_safe

from .tools import render_to_queue, render_for_user

class MailForm(forms.Form):
    reply_to = forms.EmailField(label="Reply-to")
    subject = forms.CharField(max_length=160)
    cc = forms.CharField(max_length=160, label="CC", required=False,
                         help_text="Separate with semicolons")
    body = forms.CharField(
        widget=forms.Textarea,
        help_text="Variables described above may be referenced in the email body by wrapping them in {{ curly braces }}.")

class MailTarget:
    name = "sample-target"
    tags = ["sample-target"]
    template = "emailtracker/mailer.html"
    form_class = MailForm
    permission = None

    verbose_name = "Sample Target"

    def get_form_args(self):
        return {}

    def render_body(self, form, context):
        template = Template(form.cleaned_data["body"].strip().replace(
            "\n", "<br>"))
        try:
            return mark_safe(template.render(Context(context)))
        except Exception as e:
            return e

    def get_emails(self, form):
        return []

    def send(self, emails, form):
        kwargs = {}
        if form.cleaned_data["cc"]:
            kwargs["cc"] = form.cleaned_data["cc"].split(";")
        kwargs["reply_to"] = form.cleaned_data["reply_to"].split(";")
        count = 0
        for to, body in emails:
            render_to_queue(
                self.template, self.name, context={ "body": body }, to=to,
                tags=self.tags, subject=form.cleaned_data["subject"], **kwargs
            )
            count += 1
        return count

    def send_preview(self, emails, form, user):
        kwargs = {}
        kwargs["reply_to"] = form.cleaned_data["reply_to"].split(";")
        for to, body in emails:
            render_for_user(
                user, self.template, self.name, context={ "body": body },
                tags=list(self.tags) + ["emailer-preview-test"],
                subject="[Test] " + form.cleaned_data["subject"], **kwargs
            )
            return 1
        return 0

targets = {}

def register(target):
    targets["{}.{}".format(target.__module__, target.__name__)] = target
    return target
