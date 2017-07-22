from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.template.loader import render_to_string
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from channels.generic.websockets import JsonWebsocketConsumer
from model_utils import FieldTracker

from django.utils import timezone
import datetime

class CastingReleaseMeta(models.Model):
    publish_callbacks = models.DateTimeField(null=True, blank=True)
    publish_first_round_casts = models.DateTimeField(null=True, blank=True)
    publish_casts = models.DateTimeField(null=True, blank=True)

    STAGES = (
        (0, "Auditions"),
        (1, "Callback Lists Released"),
        (2, "First-Round Casting Released"),
        (3, "Cast Lists Released"),
    )
    stage = models.PositiveSmallIntegerField(choices=STAGES, default=0)
    
    signing_opens = models.DateTimeField(null=True, blank=True)
    second_signing_opens = models.DateTimeField(null=True, blank=True)

    tracker = FieldTracker(fields=("publish_callbacks",
                                   "publish_first_round_casts",
                                   "publish_casts",
                                   "signing_opens",
                                   "second_signing_opens"))
    
    class Meta:
        verbose_name = "Casting Release Settings"
        verbose_name_plural = "Casting Release Settings"

    @property
    def association(self):
        if self.castingmeta_set.exists():
            return self.castingmeta_set.all()[0].show
        else:
            return None
    
    def __str__(self):
        n = self.castingmeta_set.count()
        if n > 0:
            show = self.association
            if n > 1:
                season = ""
                for i in self.castingmeta_set.prefetch_related("show").all():
                    if season and i.show.seasonstr() != season:
                        return "({} associated with multiple seasons)".format(
                            self._meta.verbose_name)
                    else:
                        season = i.show.seasonstr()
                return season
            else:
                return show.title
        else:
            if self.id:
                return "(Unassociated {})".format(self._meta.verbose_name)
            else:
                return "(New {})".format(self._meta.verbose_name)
            
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
        help_text="Extra information about all callbacks (location, etc).")
    callbacks_submitted = models.BooleanField(default=False)
    cast_list_description = models.TextField(
        blank=True, verbose_name="Cast List Information",
        help_text="Extra information to display with the cast list.")
    first_cast_submitted = models.BooleanField(
        default=False, verbose_name="First-round Cast List Submitted")
    cast_submitted = models.BooleanField(
        default=False, verbose_name="Full Cast List Submitted")
    contact_email = models.EmailField(
        blank=True, verbose_name="Show Contact Email")
    release_meta = models.ForeignKey(
        CastingReleaseMeta, verbose_name=CastingReleaseMeta._meta.verbose_name)

    class Meta:
        verbose_name = "Casting Information"
        verbose_name_plural = "Casting Information"

    def __str__(self):
        return str(self.show)

    @property
    def callbacks_released(self):
        return self.callbacks_submitted and self.release_meta.stage > 0
    
    @property
    def audition_slots(self):
        return self.slot_set.filter(type=Slot.TYPES[0][0])
    
    @property
    def callback_slots(self):
        return self.slot_set.filter(type=Slot.TYPES[1][0])
    
class AssociateShowMixin(models.Model):
    show = models.ForeignKey(CastingMeta)

    class Meta:
        abstract = True
    
class Audition(AssociateShowMixin):
    STATUSES = (
        ("waiting", "Waiting"),
        ("called", "Called"),
        ("done", "Auditioned")
    )
    actor = models.ForeignKey(get_user_model())
    signed_in = models.DateTimeField(auto_now_add=True)
    status = models.CharField(default=STATUSES[0][0], max_length=20,
                              choices=STATUSES)
    space = models.ForeignKey(settings.SPACE_MODEL, blank=True, null=True)

    def __str__(self):
        return "{} for {}".format(self.actor, self.show)

STATUS_CLASSES = {
    "waiting": "bg-warning",
    "called": "bg-primary",
    "done": "bg-success",
}       
@receiver(post_save)
def send_auditions(sender, instance, *args, **kwargs):
    if sender == Audition:
        def make_message(template, status="waiting"):
            return {
                "container": "table tbody",
                "element": "<tr>",
                "pulse": STATUS_CLASSES[status],
                "id": "audition-{}".format(instance.pk),
                "html": render_to_string(template, { "audition": instance })
            }
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
    allowed_signers = models.PositiveSmallIntegerField(
        default=1, help_text="Number of actors allowed to sign.")
    added_for_signing = models.BooleanField(default=False)

    @property
    def editable(self):
        if self.show.first_cast_submitted:
            return False
        if self.show.callbacks_submitted:
            return self.added_for_signing
        return True
    
    def __str__(self):
        return self.name if self.name else "<Unnamed Character>"

class ActorMapping(models.Model):
    character = models.ForeignKey(Character)
    actor = models.ForeignKey(get_user_model(), null=True)

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
    notified = models.BooleanField(default=False)
    
class Signing(ActorMapping):
    order = models.PositiveSmallIntegerField(default=0)
    response = models.NullBooleanField()
    notified_first = models.BooleanField(default=False)
    notified_second = models.BooleanField(default=False)

    @property
    def editable(self):
        if self.show.cast_submitted:
            return False
        if self.show.first_cast_submitted:
            return self.order >= self.character.allowed_signers
        return True
    
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
        
STANDARD_TIMES = (
    datetime.time(hour=18),
    datetime.time(hour=21),
    datetime.time(hour=23, minute=30),
    datetime.time(hour=23, minute=59, second=59),
    datetime.time(hour=11),
    datetime.time(hour=19),
    datetime.time()
)
ALL_TIMES = list(sorted(
    [datetime.time(hour=i) for i in range(9, 24)] +
    [datetime.time(hour=i, minute=30) for i in range(9, 24)]))
def make_time_choices(times):
    return tuple(zip(times, [i.strftime("%I:%M %p") for i in times]))
STANDARD_TIME_CHOICES = make_time_choices(STANDARD_TIMES)
ALL_TIME_CHOICES = make_time_choices(ALL_TIMES)
TIME_CHOICES = (
    ("Common Times", STANDARD_TIME_CHOICES),
    ("All Times", ALL_TIME_CHOICES)
)

class SlotManager(models.Manager):
    def auditions(self):
        return self.filter(type=Slot.TYPES[0][0])
    
    def callbacks(self):
        return self.filter(type=Slot.TYPES[1][0])

class Slot(models.Model):
    show = models.ForeignKey(CastingMeta)
    space = models.ForeignKey(settings.SPACE_MODEL)
    day = models.DateField()
    start = models.TimeField(choices=TIME_CHOICES)
    end = models.TimeField(choices=TIME_CHOICES)
    TYPES = (
        (0, "Audition"),
        (1, "Callback"),
    )
    type = models.PositiveSmallIntegerField(default=0, choices=TYPES)

    objects = SlotManager()
    
    def __str__(self):
        return "{} Slot for {}".format(Slot.TYPES[self.type][1], self.show)
