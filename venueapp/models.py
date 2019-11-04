from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models.signals import (post_save, pre_delete, pre_save,
                                      m2m_changed)
from django.dispatch import receiver

from django.conf import settings

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

class VenueApp(Season):
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="venue_manager",
        help_text="These users will get application submission notifications.")
    readers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        help_text="These users can view submitted applications.")
    contact_email = models.EmailField(help_text="Displayed to applicants as the point of contact for this application.")

    venue = models.ForeignKey(Space, on_delete=models.PROTECT)
    prelim_due = models.DateTimeField()
    full_due = models.DateTimeField()
    live = models.BooleanField(default=False)

    residency_instr = models.TextField(
        blank=True, verbose_name="Residency Description")
    budget_instr = models.TextField(
        blank=True, verbose_name="Budget Notes or Instructions")
    questions = models.ManyToManyField(Question, blank=True)

    objects = AppManager()

    def __str__(self):
        return "{} - {}".format(self.venue, self.seasonstr())

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
        return "{} from {} to {}".format(self.venue.venue, self.start, self.end)

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
    band_size = models.CharField(max_length=80)
    cast_breakdown = models.CharField(max_length=80)
    script = models.FileField(
        upload_to=upload_destination,
        blank=True, help_text="Only include for original or unknown works.",
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    created = models.DateTimeField(auto_now_add=True)

    pre_submitted = models.DateTimeField(null=True)
    full_submitted = models.DateTimeField(null=True)

    length_description = models.TextField(help_text="Please elaborate on your preferences for residency length, if necessary.", verbose_name="Residency Length Preferences", blank=True)

    @property
    def prelim_due(self):
        return self.venues.all().order_by("prelim_due").first().prelim_due

    @property
    def full_due(self):
        return self.venues.all().order_by("full_due").first().full_due

    def __str__(self):
        return str(self.show)

    def venuestr(self):
        return ", ".join(
            [str(i.venue) for i in self.venues.all()])

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
    answer = models.TextField()

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
    conflicts = models.TextField(help_text="Big-picture conflicts for the upcoming season, such as other leadership positions or involvements.")

    objects = SeasonManager()

    def __str__(self):
        return str(self.user)

class RoleManager(models.Manager):
    def active(self):
        return self.filter(archived=False)

class StaffRole(models.Model):
    CATEGORIES = (
        (5, "Author"),
        (10, "Executive"),
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

    def __str__(self):
        return self.name

class RoleQuestion(AbstractQuestion):
    role = models.ForeignKey(StaffRole, on_delete=models.CASCADE)

class MemberManager(models.Manager):
    def create_from_user(self, show, user, **kwargs):
        meta, created = SeasonStaffMeta.objects.get_or_create_in_season(
            show.show, user=user)
        return self.create(show=show, person=meta, **kwargs)

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
        return self.other_role if self.role.other else str(self.role)

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
        (0, "Income"),
        (10, "Administrative Expenses"),
        (20, "Production Expenses"),
        (50, "Other Expenses"),
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

    class Meta:
        unique_together = ("app", "ordering")
