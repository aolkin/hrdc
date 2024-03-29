from django.db import models
from django.db.models import Avg
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.template.loader import render_to_string
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.contrib.humanize.templatetags import humanize

from channels.generic.websockets import JsonWebsocketConsumer
from model_utils import FieldTracker

from django.utils import timezone
import datetime
from datetime import timedelta
from config import config

from dramaorg.models import Season

class CastingReleaseMeta(Season):
    publish_callbacks = models.DateTimeField(null=True, blank=True)
    publish_first_round_casts = models.DateTimeField(null=True, blank=True)
    publish_casts = models.DateTimeField(null=True, blank=True)

    STAGES = (
        (0, "Auditions"),
        (1, "Callback Lists Released"),
        (2, "First-Round Casting Released"),
        (3, "Cast Lists Released"),
        (4, "Signing Open"),
        (5, "Sent Signing Reminder"),
        (6, "Alternate Signing Open"),
    )
    stage = models.PositiveSmallIntegerField(choices=STAGES, default=0)
    prevent_advancement = models.BooleanField(
        default=False,
        help_text="If this is set, the stage will not advance until it is "
        "cleared again, regardless of set times.")
    disable_signing = models.BooleanField(
        default=False,
        help_text="Checking this will temporarily prevent actors from signing.")

    signing_opens = models.DateTimeField(null=True, blank=True)
    second_signing_opens = models.DateTimeField(
        null=True, blank=True, verbose_name="Signing closes")
    second_signing_warning = models.DateTimeField(
        null=True, blank=True, verbose_name="Signing closes warning",
        help_text="Sends a reminder to unsigned actors at this time.")

    tracker = FieldTracker(fields=("publish_callbacks",
                                   "publish_first_round_casts",
                                   "publish_casts",
                                   "signing_opens",
                                   "second_signing_opens",
                                   "second_signing_warning"))

    class Meta:
        verbose_name = "Casting Release Group"
        permissions = (
            ("view_first_cast_lists", "Can view first-round cast lists"),
            ("update_castingreleasemeta_stage", "Can manually set the stage"),
        )


    @property
    def association(self):
        if self.castingmeta_set.exists():
            return self.castingmeta_set.all()[0].show
        else:
            return None

    def __str__(self):
        return self.seasonstr()

    def clean(self):
        if (self.publish_callbacks and
            self.stage > 0 and self.publish_callbacks >= timezone.now()):
            self.publish_callbacks = self.tracker.previous("publish_callbacks")
            raise ValidationError(
                { "publish_callbacks":
                  "Callbacks have already been published, cannot set to "
                  "publish at a future time." })
        if self.publish_first_round_casts:
            if not (self.publish_callbacks and
                    self.publish_callbacks < self.publish_first_round_casts):
                self.publish_first_round_casts = self.tracker.previous(
                    "publish_first_round_casts")
                self.publish_callbacks = self.tracker.previous(
                    "publish_callbacks")
                raise ValidationError(
                    { "publish_first_round_casts":
                      "First-round cast lists must be published after "
                      "callback lists." })
            if (self.stage > 1 and
                self.publish_first_round_casts >= timezone.now()):
                self.publish_first_round_casts = self.tracker.previous(
                    "publish_first_round_casts")
                raise ValidationError(
                    { "publish_first_round_casts":
                      "First-round cast lists have already been published, "
                      "cannot set to publish at a future time." })
        if self.publish_casts:
            if not (self.publish_first_round_casts and
                    self.publish_first_round_casts < self.publish_casts):
                self.publish_first_round_casts = self.tracker.previous(
                    "publish_first_round_casts")
                self.publish_casts = self.tracker.previous("publish_casts")
                raise ValidationError(
                    { "publish_casts":
                      "Cast lists must be published after first-round cast "
                      "lists." })
            if self.stage > 2 and self.publish_casts >= timezone.now():
                self.publish_casts = self.tracker.previous("publish_casts")
                raise ValidationError(
                    { "publish_casts":
                      "Cast lists have already been published, cannot "
                      "set to publish at a future time." })
            if not (self.signing_opens and self.second_signing_opens):
                self.publish_casts = self.tracker.previous("publish_casts")
                raise ValidationError(
                    { "publish_casts":
                      "Cannot publish casts without setting signing options."})
            if (self.signing_opens and
                (self.stage > 2 or (
                    not self.tracker.has_changed("publish_casts") and
                    self.publish_casts <= timezone.now())) and
                self.tracker.has_changed("signing_opens")):
                self.signing_opens = self.tracker.previous("signing_opens")
                raise ValidationError(
                    { "signing_opens":
                      "Cast lists have already been published, cannot edit "
                      "signing options." })
            if self.second_signing_warning:
                if ((self.stage > 2 or (
                        not self.tracker.has_changed("publish_casts") and
                        self.publish_casts <= timezone.now())) and
                    self.tracker.has_changed("second_signing_warning")):
                    self.second_signing_warning = self.tracker.previous(
                        "second_signing_warning")
                    raise ValidationError(
                        { "second_signing_warning":
                          "Cast lists have already been published, cannot "
                          "edit signing options." })
                if self.publish_casts >= self.second_signing_warning:
                    self.second_signing_warning = self.second_signing_warning
                    raise ValidationError(
                        { "second_signing_warning":
                          "Second-round signing warning must happen after "
                          "casts have been published." })
            if self.second_signing_opens:
                if ((self.stage > 2 or (
                        not self.tracker.has_changed("publish_casts") and
                        self.publish_casts <= timezone.now())) and
                    self.tracker.has_changed("second_signing_opens")):
                    self.second_signing_opens = self.tracker.previous(
                        "second_signing_opens")
                    raise ValidationError(
                        { "second_signing_opens":
                          "Cast lists have already been published, cannot "
                          "edit signing options." })
                if self.publish_casts >= self.second_signing_opens:
                    self.signing_opens = self.signing_opens
                    self.second_signing_opens = self.second_signing_opens
                    raise ValidationError(
                        { "second_signing_opens":
                          "Second-round signing must open after casts have "
                          "been published." })
        if self.signing_opens and self.second_signing_opens:
            if self.signing_opens >= self.second_signing_opens:
                raise ValidationError(
                { "second_signing_opens":
                  "Second-round signing must open after first-round signing."})

class CastingMeta(models.Model):
    show = models.OneToOneField(settings.SHOW_MODEL, on_delete=models.CASCADE,
                                related_name="casting_meta")
    callback_description = models.TextField(
        blank=True, verbose_name="Callback Information",
        help_text="Extra information about all callbacks " +
        "(location, date, etc).")
    callbacks_submitted = models.BooleanField(default=False,
                                              verbose_name="Callbacks")
    cast_list_description = models.TextField(
        blank=True, verbose_name="Cast List Information",
        help_text="Extra information to display with the cast list. " +
        "Include shows you cannot share actors with here.")
    first_cast_submitted = models.BooleanField(
        default=False, verbose_name="First-round Cast")
    cast_submitted = models.BooleanField(
        default=False, verbose_name="Full Cast")
    contact_email = models.EmailField(
        blank=True, verbose_name="Show Contact Email")

    release_meta = models.ForeignKey(
        CastingReleaseMeta, verbose_name=CastingReleaseMeta._meta.verbose_name,
        on_delete=models.CASCADE)

    tech_req_pool = models.ManyToManyField(
        "self", blank=True, verbose_name="Actors must tech req on one of",
        symmetrical=False, related_name="tech_req_contributor_set")
    exempt_year = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Actors in this year do not need to sign for a tech req.")
    num_tech_reqers = models.PositiveSmallIntegerField(
        default=999, verbose_name="Tech Reqers Allowed",
        help_text="How many tech reqers can this show have?")

    class Meta:
        verbose_name = "Casting-Enabled Show"
        permissions = (
            ("modify_submission_status", "Can change list submission status"),
            ("view_unreleased_callbacks", "Can view unreleased callbacks"),
            ("view_unreleased_cast", "Can view unreleased cast"),
        )

    def __str__(self):
        return self.show.name

    @property
    def signed_actors(self):
        return [i.actor for i in
                Signing.objects.filter(character__show=self, response=True)]

    @property
    def tech_actors(self):
        return [i.actor for i in
                Signing.objects.filter(tech_req=self, response=True)]

    @property
    def tech_reqers(self):
        return Signing.objects.filter(tech_req=self, response=True)

    @property
    def tech_reqer_count(self):
        return Signing.objects.filter(tech_req=self, response=True).count()

    @property
    def needs_more_tech_reqers(self):
        return self.tech_reqer_count < self.num_tech_reqers

    @property
    def tech_req_contributors(self):
        return self.tech_req_contributor_set.all()

    @property
    def audition_avg(self):
        avg = Audition.objects.filter(
            show=self, audition_length__isnull=False).aggregate(
                Avg("audition_length"))["audition_length__avg"]
        return round(avg.total_seconds() / 60) if avg else avg

    @property
    def callbacks_released(self):
        return self.callbacks_submitted and self.release_meta.stage > 0

    @property
    def first_cast_released(self):
        return self.first_cast_submitted and self.release_meta.stage > 1

    @property
    def cast_list_released(self):
        return self.cast_submitted and self.release_meta.stage > 2

    @property
    def audition_slots(self):
        return self.slot_set.filter(type=Slot.TYPES[0][0]).order_by(
            "day", "start")

    @property
    def callback_slots(self):
        return self.slot_set.filter(type=Slot.TYPES[1][0])

class TechReqCastingMeta(CastingMeta):
    class Meta:
        proxy = True
        verbose_name = "Casting-Enabled Show - Tech Req Info"
        verbose_name_plural = "Casting-Enabled Shows - Tech Req Info"

class AuditionCastingMeta(CastingMeta):
    class Meta:
        proxy = True
        verbose_name = "Casting-Enabled Show - Audition Info"
        verbose_name_plural = "Casting-Enabled Shows - Audition Info"

class AssociateShowMixin(models.Model):
    show = models.ForeignKey(CastingMeta, on_delete=models.CASCADE)

    class Meta:
        abstract = True

class ActorSeasonMeta(Season):
    actor = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    conflicts = models.TextField(blank=True, null=True)

    def __str__(self):
        return "{} Meta for {}".format(self.seasonstr(), self.actor)

    class Meta:
        unique_together = ('year', 'season', 'actor')

class Audition(AssociateShowMixin):
    STATUSES = (
        ("waiting", "Waiting"),
        ("called", "Fetched"),
        ("done", "Auditioned")
    )
    actor = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    signed_in = models.DateTimeField(auto_now_add=True)
    sign_in_complete = models.BooleanField(default=False)
    status = models.CharField(default=STATUSES[0][0], max_length=20,
                              choices=STATUSES)
    called_time = models.DateTimeField(null=True)
    done_time = models.DateTimeField(null=True)
    audition_length = models.DurationField(null=True)
    busy = models.ForeignKey("self", null=True, on_delete=models.SET_NULL)
    space = models.ForeignKey(settings.SPACE_MODEL, blank=True, null=True,
                              on_delete=models.SET_NULL)
    tech_interest = models.TextField(
        null=True, blank=True, default=None, verbose_name="Technical Interests")

    class Meta:
        permissions = (
            ("table_auditions", "Can table at audition sign-ins"),
        )

    @property
    def actorseasonmeta(self):
        if not hasattr(self, "_cached_actorseasonmeta"):
            self._cached_actorseasonmeta, created = (
                ActorSeasonMeta.objects.get_or_create_in_season(
                    self.show.show, actor_id=self.actor_id))
        return self._cached_actorseasonmeta

    def audition_minutes(self):
        return round(self.audition_length.seconds / 60)

    def __str__(self):
        return "{} for {}".format(self.actor, self.show)

STATUS_CLASSES = {
    Audition.STATUSES[0][0]: "bg-warning",
    Audition.STATUSES[1][0]: "bg-primary",
    Audition.STATUSES[2][0]: "bg-success",
}

@receiver(pre_save)
def update_audition_length(sender, instance, *args, **kwargs):
    if sender == Audition and instance.done_time:
        instance.audition_length = instance.done_time - instance.called_time

@receiver(post_save)
def send_auditions(sender, instance, *args, **kwargs):
    if sender == Audition and instance.actor.is_initialized:
        def make_message(template, status="waiting"):
            return {
                "container": "table tbody",
                "element": "<tr>",
                "pulse": STATUS_CLASSES[status],
                "id": "audition-{}".format(instance.pk),
                "html": render_to_string(template, { "audition": instance })
            }
        if instance.status == Audition.STATUSES[1][0]:
            if instance.space:
                for aud in Audition.objects.filter(
                        actor_id=instance.actor_id,
                        space__building=instance.space.building,
                        signed_in__date=instance.signed_in).exclude(
                            id=instance.id).exclude(
                                status=Audition.STATUSES[1][0]):
                    aud.busy = instance
                    aud.save()
        else:
            for aud in Audition.objects.filter(actor_id=instance.actor_id,
                                               busy=instance):
                aud.busy = None
                aud.save()
        if not instance.sign_in_complete:
            return
        if instance.space:
            JsonWebsocketConsumer.group_send(
                "auditions-building-{}".format(instance.space.building.pk),
                make_message("casting/pieces/tabling_row.html",
                             instance.status))
        JsonWebsocketConsumer.group_send(
            "auditions-show-{}".format(instance.show.pk),
            make_message("casting/pieces/audition_row.html"))

class Character(AssociateShowMixin):
    name = models.CharField(max_length=60, verbose_name="Character Name")
    callback_description = models.TextField(
        blank=True, verbose_name="Character Callback Information",
        help_text="Extra information about callbacks for this character.")
    cast_description = models.TextField(
        blank=True, verbose_name="Character Details",
        help_text="Additional information for actors about this character.")
    allowed_signers = models.PositiveSmallIntegerField(
        default=1,
        help_text="Number of actors allowed to sign for this character.")
    added_for_signing = models.BooleanField(default=False)
    hidden_for_signing = models.BooleanField(default=False)
    allow_multiple_signatures = models.BooleanField(default=False)

    @property
    def editable(self):
        if self.show:
            if self.show.first_cast_submitted:
                return False
            if self.show.callbacks_submitted:
                return self.added_for_signing
        return True

    @property
    def uneditable(self):
        return not self.editable

    @property
    def actors(self):
        responses = self.signing_set.filter(response=True)
        if responses:
            if self.signing_set.filter(order__lt=responses.last().order,
                                       response__isnull=True):
                return None
        if len(responses) >= self.allowed_signers:
            signers = list([i.actor for i in responses])
            if len(signers) > self.allowed_signers:
                return signers[:self.allowed_signers]
            else:
                return signers
        else:
            return None

    def __str__(self):
        return self.name if self.name else "<Unnamed Character>"

    class Meta:
        ordering = "pk",

class ActorMapping(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    actor = models.ForeignKey(get_user_model(), null=True,
                              on_delete=models.CASCADE)

    class Meta:
        abstract = True

    @property
    def show(self):
        return self.character and self.character.show

    def __str__(self):
        try:
            return "{} for {} in {}".format(self.actor, self.character,
                                            self.show)
        except ObjectDoesNotExist:
            return "(Unnassigned {})".format(self.__class__.__name__)

class Callback(ActorMapping):
    pass

class Signing(ActorMapping):
    order = models.PositiveSmallIntegerField(default=0)
    response = models.NullBooleanField(choices=(
        (True, "Accept this Role"),
        (False, "Reject this Role"),
        (None, "No Response"),
    ))
    timed_out = models.BooleanField(default=False)
    alternate_notified = models.BooleanField(default=False)
    tech_req = models.ForeignKey(CastingMeta, null=True, blank=True,
                                 on_delete=models.SET_NULL)

    signed_time = models.DateTimeField(auto_now=True, null=True)

    def order_num(self):
        return self.order + 1

    def order_title(self):
        order = max(self.order - (self.character.allowed_signers - 1), 0)
        if order:
            return humanize.ordinal(order) + " Alternate"
        else:
            return "First Choice"
    order_title.short_description = "Casting Preference Order"
    order_title.admin_order_field = "order"

    def order_title_email(self):
        order = max(self.order - (self.character.allowed_signers - 1), 0)
        if order:
            return "({} alternate)".format(humanize.ordinal(order))
        else:
            return ""

    @property
    def editable(self):
        if self.show.cast_submitted:
            return False
        if self.show.first_cast_submitted:
            return self.order >= self.character.allowed_signers
        return True

    @property
    def uneditable(self):
        return not self.editable

    @property
    def signing_disabled(self):
        return self.show.release_meta.disable_signing

    @property
    def signable(self):
        if self.signing_disabled:
            return False
        signed = len(Signing.objects.filter(character=self.character,
                                            order__lt=self.order,
                                            response=True))
        return signed < self.character.allowed_signers

    class Meta:
        ordering = ("character__show", "character", "order")

@receiver(pre_delete)
def shift_signings(sender, instance, **kwargs):
    if sender == Signing:
        shifts = Signing.objects.filter(character=instance.character,
                                        order__gt=instance.order)
        for signing in shifts:
            signing.order -= 1
            signing.save()

@receiver(post_save)
def notify_alternates(sender, instance, *args, **kwargs):
    if sender == Signing:
        if instance.response == False:
            from .tasks import notify_alternates
            notify_alternates.delay(instance.pk)

STANDARD_TIMES = (
    datetime.time(hour=18),
    datetime.time(hour=21),
    datetime.time(hour=23, minute=30),
    datetime.time(hour=23, minute=59, second=59),
    datetime.time(hour=11),
    datetime.time(hour=19),
)
ALL_TIMES = list(sorted(
    [datetime.time(hour=i) for i in range(9, 24)] +
    [datetime.time(hour=i, minute=30) for i in range(9, 24)]))

def make_time_choices(times):
    return tuple(zip(times, [i.strftime("%I:%M %p") for i in times]))

STANDARD_TIME_ENDS = make_time_choices(STANDARD_TIMES)
STANDARD_TIME_STARTS = make_time_choices(STANDARD_TIMES + (datetime.time(),))
ALL_TIME_CHOICES = make_time_choices(ALL_TIMES)
START_TIME_CHOICES = (
    ("Common Times", STANDARD_TIME_STARTS),
    ("All Times", ALL_TIME_CHOICES)
)
END_TIME_CHOICES = (
    ("Common Times", STANDARD_TIME_ENDS),
    ("All Times", ALL_TIME_CHOICES)
)

class SlotManager(models.Manager):
    def auditions(self):
        return self.filter(type=Slot.TYPES[0][0])

    def callbacks(self):
        return self.filter(type=Slot.TYPES[1][0])

    def current_slots(self):
        return self.auditions().filter(
            day=timezone.localdate(),
            start__lte=timezone.localtime() + timedelta(
                minutes=config.get_float("casting_advance_signin_minutes", 0)),
            end__gte=timezone.localtime())

    def active_slot(self, show):
        slots = self.current_slots().filter(show_id=show)
        return slots[0] if slots else None

class Slot(models.Model):
    show = models.ForeignKey(CastingMeta, on_delete=models.CASCADE)
    space = models.ForeignKey(settings.SPACE_MODEL, on_delete=models.CASCADE)
    day = models.DateField()
    start = models.TimeField(choices=START_TIME_CHOICES)
    end = models.TimeField(choices=END_TIME_CHOICES)
    TYPES = (
        (0, "Audition"),
        (1, "Callback"),
    )
    type = models.PositiveSmallIntegerField(default=0, choices=TYPES)

    objects = SlotManager()

    def __str__(self):
        return "{} Slot for {}".format(Slot.TYPES[self.type][1], self.show)
