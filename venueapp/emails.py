from django import forms

from emailtracker.mailer import *

from dramaorg.models import Season, Space
from .models import *

class ApplicationMailForm(MailForm):
    year = forms.IntegerField(min_value=1900, max_value=2500,
                              help_text="Applications for this year")
    season = forms.ChoiceField(choices=Season.SEASONS,
                               help_text="Applications for this season")
    venue = forms.ModelChoiceField(required=False, queryset=Space.objects.all(),
                                   help_text="Only applications for this venue - optional")

@register
class ApplicationTarget(MailTarget):
    name = "venueapp-target"
    tags = "venueapp", "venueapp-application-mailer"
    form_class = ApplicationMailForm
    permission = "venueapp.view_application"

    verbose_name = "Venue Application Executive Staffs" 
    variables_description = """show - the name of the show being applied for
    venues - the venues being applied to
    venue - the selected venue in your filters,
    people - the people to whom this email is addressed
    """

    def get_emails(self, form):
        apps = Application.objects.filter(
            show__year=form.cleaned_data["year"],
            show__season=form.cleaned_data["season"])
        if form.cleaned_data["venue"]:
            apps = apps.filter(venues__venue=form.cleaned_data["venue"])
        if not apps.exists():
            return []
        for app in apps:
            yield ["{} <{}>".format(i.get_full_name(False), i.email)
                   for i in app.show.staff.all()], self.render_body(
                           form, {
                               "show": str(app.show),
                               "venues": app.venuesand(),
                               "venue": form.cleaned_data["venue"],
                               "people": app.exec_staff_names(),
                           })
