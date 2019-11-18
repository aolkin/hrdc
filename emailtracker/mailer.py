
from django import forms
from django.template import Template, Context
from django.utils.html import mark_safe

from .tools import render_to_queue

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

    verbose_name = "Sample Target"
    variables_description = """show - the name of the show being applied for
    venues - the venues being applied to
    """

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

targets = {}

def register(target):
    targets["{}.{}".format(target.__module__, target.__name__)] = target
    return target
