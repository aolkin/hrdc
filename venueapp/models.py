from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models.signals import (post_save, pre_delete, pre_save,
                                      m2m_changed)
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext

import os.path

from dramaorg.models import Space, Season, Show, SeasonManager

class AbstractQuestion(models.Model):
    short_name = models.CharField(max_length=40)
    question = models.TextField()
    required = models.BooleanField(default=True)

    def __str__(self):
        return self.short_name

    class Meta:
        abstract = True

class Question(AbstractQuestion): pass

class AppManager(SeasonManager):
    def live(self):
        return self.filter(live=True)

    def available(self):
        return self.filter(live=True, due__gt=timezone.now())

class AbstractApp(Season):
    venue = models.ForeignKey(Space, on_delete=models.PROTECT)
    due = models.DateTimeField()
    live = models.BooleanField(default=False)

    objects = AppManager()

    def __str__(self):
        return "{} - {}".format(self.venue, self.seasonstr())

    class Meta:
        abstract = True
        verbose_name = "Venue Application"

class VenueApp(AbstractApp):
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="venue_manager",
        help_text="These users will get application submission notifications.")
    readers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        help_text="These users can view submitted applications.")
    contact_email = models.EmailField(help_text="Displayed to applicants as the point of contact for this application.")

    residency_instr = models.TextField(
        blank=True, verbose_name="Residency Description")
    budget_instr = models.TextField(
        blank=True, verbose_name="Budget Notes or Instructions")
    questions = models.ManyToManyField(Question, blank=True)

class AvailableResidency(models.Model):
    venue = models.ForeignKey(VenueApp, on_delete=models.CASCADE)
    start = models.DateField()
    end = models.DateField()
    type = models.BooleanField(choices=(
        (False, "Available Range"),
        (True, "Single Residency"),
    ))

    def clean(self):
        if self.end < self.start:
            raise ValidationError(
                {"end": "End date must come after start date."})
        if AvailableResidency.objects.filter(
                venue=self.venue, type=not self.type).exclude(
                    pk=self.pk).exists():
            raise ValidationError(
                {"type": "A venue cannot have a mix of ranges and residencies."}
            )

    def __str__(self):
        return "{} from {:%m-%d} to {:%m-%d}".format(self.venue.venue,
                                                     self.start, self.end)

    class Meta:
        ordering = "start",
        verbose_name_plural = "Available Residencies"

class Application(models.Model):
    def upload_destination(instance, filename):
        return "venueapp/{}/{}/shows/{}/script/{}".format(
            instance.show.year, instance.show.get_season_display(),
            instance.show.slug, filename)
    
    show = models.OneToOneField(Show, on_delete=models.PROTECT)
    venues = models.ManyToManyField(VenueApp)
    band_size = models.CharField(max_length=80,
                                 verbose_name=_("Band/Orchestra Size"))
    cast_breakdown = models.CharField(
        # Translators: The name of the cast breakdown field
        max_length=80, verbose_name=_("Cast Gender Breakdown"),
        # Translators: The description below the cast breakdown field
        help_text=_("Intended gender preferences for your cast"))
    script = models.FileField(
        upload_to=upload_destination,
        verbose_name=_("Script"),
        # Translators: The description below the script upload button for
        # venue applications
        blank=True, help_text=_("Only include for original or unknown works."),
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    created = models.DateTimeField(auto_now_add=True)

    submitted = models.DateTimeField(null=True)

    length_description = models.TextField(verbose_name=_("Residency Length Preferences"), help_text=_("Please elaborate on your preferences for residency length, if necessary."), blank=True)

    @property
    def due(self):
        return self.venues.all().order_by("due").first().due

    def __str__(self):
        return str(self.show)

    def venuestr(self):
        return ", ".join(
            [str(i.venue) for i in self.venues.all()])

    def venuesand(self):
        out = ""
        count = self.venues.all().count()
        for i, v in enumerate(self.venues.all()):
            out += str(v.venue)
            if i < count - 2:
                out += ", "
            elif i < count - 1:
                if count > 2:
                    out += ", and "
                else:
                    out += " and "
        return out

    def exec_staff_list(self):
        return ", ".join([str(i) for i in self.staffmember_set.filter(
            role__category=10)])

    def exec_staff_names(self):
        qs = self.staffmember_set.filter(role__category=10)
        out = ""
        count = qs.count()
        for i, v in enumerate(qs.all()):
            out += str(v.person)
            if i < count - 2:
                out += ", "
            elif i < count - 1:
                if count > 2:
                    out += ", and "
                else:
                    out += " and "
        return out
    
    def season(self):
        return self.show.seasonstr()
    venuestr.short_description = "Venues"

def update_venues(sender, instance, **kwargs):
    SlotPreference.objects.filter(app=instance).exclude(
        venue__in=instance.venues.all()).delete()
    BudgetLine.objects.filter(show=instance).exclude(
        venue__in=instance.venues.all()).delete()
    Answer.objects.filter(app=instance).exclude(
        venue__in=instance.venues.all()).delete()
    for venue in instance.venues.all():
        if not BudgetLine.objects.filter(show=instance, venue=venue).exists():
            for line in DefaultBudgetLine.objects.filter(
                    venue=venue).values("venue_id", "category", "name",
                                        "amount", "notes"):
                BudgetLine.objects.create(show=instance, required=True, **line)
        for question in venue.questions.all():
            a, created = Answer.objects.get_or_create(
                question=question, app=instance, venue=venue)
m2m_changed.connect(update_venues, sender=Application.venues.through)


class AbstractAnswer(models.Model):
    answer = models.TextField(blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return "Answer to {}".format(self.question)

class Answer(AbstractAnswer):
    question = models.ForeignKey(Question, on_delete=models.PROTECT)
    venue = models.ForeignKey(VenueApp, on_delete=models.CASCADE)
    app = models.ForeignKey(Application, on_delete=models.CASCADE)

class SeasonStaffMeta(Season):
    def upload_destination(instance, filename):
        return "venueapp/{}/{}/resumes/{}".format(
            instance.year, instance.get_season_display(), filename)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    resume = models.FileField(
        upload_to=upload_destination,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    conflicts = models.TextField(help_text=_("Big-picture conflicts for the upcoming season, such as other leadership positions or involvements."))

    objects = SeasonManager()

    @property
    def resume_filename(self):
        return self.resume and os.path.basename(self.resume.name)

    def __str__(self):
        return str(self.user)

class RoleManager(models.Manager):
    def active(self):
        return self.filter(archived=False)

class StaffRole(models.Model):
    CATEGORIES = (
        # Translators: the staff category name
        (5, _("Author")),
        # Translators: the staff category name with special privileges
        (10, _("Executive")),
        (20, "Designer"),
        (30, "Technician"),
        (40, "Assistant"),
        (50, "Advisor"),
        (60, "Other"),
    )

    name = models.CharField(max_length=40, unique=True)
    category = models.PositiveSmallIntegerField(choices=CATEGORIES,
                                                default=10)
    statement_length = models.PositiveIntegerField(default=0)
    accepts_attachment = models.BooleanField(default=False)

    archived = models.BooleanField(default=False)

    objects = RoleManager()

    @property
    def admin(self):
        return self.category == 10

    @property
    def other(self):
        return self.category == 60

    class Meta:
        ordering = "category", "name"
        verbose_name = "Staff Role"

    def __str__(self):
        return self.name

class RoleQuestion(AbstractQuestion):
    role = models.ForeignKey(StaffRole, on_delete=models.CASCADE)

class MemberManager(models.Manager):
    def create_from_user(self, show, user, **kwargs):
        meta, created = SeasonStaffMeta.objects.get_or_create_in_season(
            show.show, user=user)
        return self.create(show=show, person=meta, **kwargs)

    def signed_on(self):
        return self.filter(signed_on=True)

class StaffMember(models.Model):
    def upload_destination(instance, filename):
        return "venueapp/{}/{}/shows/{}/supplements/{}".format(
            instance.show.show.year, instance.show.show.get_season_display(),
            instance.show.show.slug, filename)
    show = models.ForeignKey(Application, on_delete=models.CASCADE,
                             db_index=True)
    person = models.ForeignKey(SeasonStaffMeta,
                               on_delete=models.CASCADE)
    signed_on = models.BooleanField(default=False)
    role = models.ForeignKey(StaffRole, on_delete=models.PROTECT)
    other_role = models.CharField(max_length=40, blank=True)

    statement = models.TextField(blank=True)
    attachment = models.FileField(
        blank=True, upload_to=upload_destination,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    objects = MemberManager()

    @property
    def supplement_status(self):
        statement = bool(self.statement) or self.role.statement_length == 0
        attachment = bool(self.attachment) or not self.role.accepts_attachment
        return statement and attachment and self.question_status

    @property
    def question_status(self):
        return (
            self.role.rolequestion_set.filter(required=True).count() <=
            self.roleanswer_set.exclude(answer="").count()
        )

    @property
    def all_status(self):
        return self.supplement_status and self.person.resume

    @property
    def role_name(self):
        return (self.other_role if self.role.other and self.other_role else
                str(self.role))

    @property
    def attachment_filename(self):
        return self.attachment and os.path.basename(self.attachment.name)

    def __str__(self):
        return "{}: {}".format(self.role_name, self.person)

    class Meta:
        ordering = "role__category", "role__name", "other_role"

@receiver(pre_save)
def coerce_role(sender, instance, raw, **kwargs):
    if sender == StaffMember and not raw:
        if instance.role.other:
            role = StaffRole.objects.filter(name__iexact=instance.other_role)
            if role.exists():
                instance.role = role[0]
        if not instance.role.other:
            instance.other_role = ""

def update_admin(show, person):
    if StaffMember.objects.filter(
            person=person, show=show, role__category=10).exists():
        show.show.staff.add(person.user)
    else:
        show.show.staff.remove(person.user)

@receiver(post_save)
def add_show_staff(sender, instance, created, raw, **kwargs):
    if sender == StaffMember and not raw:
        update_admin(instance.show, instance.person)
        RoleAnswer.objects.filter(person=instance).exclude(
            question__role=instance.role).delete()
        for question in instance.role.rolequestion_set.all():
            a, created = RoleAnswer.objects.get_or_create(
                question=question, person=instance)

@receiver(pre_delete)
def remove_show_staff(sender, instance, **kwargs):
    if sender == StaffMember:
        update_admin(instance.show, instance.person)

class RoleAnswer(AbstractAnswer):
    question = models.ForeignKey(RoleQuestion, on_delete=models.PROTECT)
    person = models.ForeignKey(StaffMember, on_delete=models.CASCADE)

class AbstractBudgetLine(models.Model):
    BUDGET_CATEGORIES = (
        (0, _("Income")),
        (10, _("Administrative Expenses")),
        (20, _("Production Expenses")),
        (50, _("Other Expenses")),
    )

    venue = models.ForeignKey(VenueApp, on_delete=models.CASCADE, db_index=True)
    category = models.PositiveSmallIntegerField(
        choices=BUDGET_CATEGORIES, default=10)
    name = models.CharField(max_length=80)
    amount = models.DecimalField(decimal_places=2, max_digits=7, default=0)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return "{} - {}".format(self.get_category_display(), self.name)

    class Meta:
        abstract = True

class BudgetLine(AbstractBudgetLine):    
    show = models.ForeignKey(
        Application, on_delete=models.CASCADE, db_index=True)
    required = models.BooleanField(default=False)

    class Meta:
        ordering = "show", "venue", "category",

class DefaultBudgetLine(AbstractBudgetLine):
    class Meta:
        ordering = "venue", "category"

class SlotPreference(models.Model):
    app = models.ForeignKey(Application, on_delete=models.CASCADE)
    venue = models.ForeignKey(VenueApp, on_delete=models.CASCADE)
    ordering = models.PositiveSmallIntegerField(default=1)

    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)
    slot = models.ForeignKey(AvailableResidency, on_delete=models.CASCADE,
                             null=True, blank=True,
                             limit_choices_to={ "type": True })

    def __str__(self):
        return (str(self.slot) if self.slot else
                "{} from {:%m-%d} to {:%m-%d}".format(
                    self.venue.venue, self.start, self.end))

    @property
    def start_date(self):
        return self.slot.start if self.slot else self.start

    @property
    def end_date(self):
        return self.slot.end if self.slot else self.end

    @property
    def weeks(self):
        if self.end_date and self.start_date:
            return ((self.end_date - self.start_date).days + 6) // 7
        return 0

    class Meta:
        unique_together = ("app", "ordering")
        ordering = ("-app", "ordering")

class OldStyleApp(AbstractApp):
    def upload_destination(instance, filename):
        return "venueapp/{}/{}/applications/{}/{}".format(
            instance.year, instance.get_season_display(),
            instance.venue, filename)

    url = models.URLField(blank=True)
    download = models.FileField(blank=True, upload_to=upload_destination)

    def clean(self):
        if self.url and self.download:
            raise ValidationError({
                "url": "Cannot provide both URL and download.",
                "download": "Cannot provide both URL and download.",
            })
        if self.live:
            if not (self.url or self.download):
                raise ValidationError({
                    "live": "This application cannot be live without either a URL or downloadable application.",
                })

    @property
    def link(self):
        return self.url or (self.download and self.download.url)

    class Meta:
        verbose_name = "Old-Style Application"
