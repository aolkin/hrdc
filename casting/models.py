from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

import datetime

class AssociateShowMixin(models.Model):
    show = models.ForeignKey(settings.SHOW_MODEL)

    class Meta:
        abstract = True

class AssociateActorMixin(models.Model):
    actor = models.ForeignKey(get_user_model())

    class Meta:
        abstract = True    
    
class Audition(AssociateShowMixin, AssociateActorMixin):
    STATUSES = (
        ("waiting", "Waiting"),
        ("called", "Called"),
        ("done", "Auditioned")
    )
    signed_in = models.DateTimeField(auto_now_add=True)
    status = models.CharField(default=STATUSES[0][0], max_length=20,
                              choices=STATUSES)

    def __str__(self):
        return "{} for {}".format(self.actor, self.show.name)

class Character(AssociateShowMixin):
    name = models.CharField(max_length=60)
    callback_description = models.TextField(blank=True)
    allowed_signers = models.PositiveSmallIntegerField(default=1)
    
    def __str__(self):
        return self.name
    
class Callback(AssociateActorMixin):
    character = models.ForeignKey(Character)

    @property
    def show(self):
        return self.character.show
    
    def __str__(self):
        return "{} for {} in {}".format(self.actor, self.character,
                                        self.show)
    
class Signing(Callback):
    order = models.PositiveSmallIntegerField()
    response = models.NullBooleanField()

    class Meta:
        ordering = ("character__show", "character", "order")

class CastingReleaseMeta(models.Model):
    publish_callbacks = models.DateTimeField(null=True, blank=True)
    publish_casts = models.DateTimeField(null=True, blank=True)
    signing_opens = models.DateTimeField(null=True, blank=True)
    second_signing_opens = models.DateTimeField(null=True, blank=True)

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

class CastingMeta(models.Model):
    show = models.OneToOneField(settings.SHOW_MODEL, on_delete=models.CASCADE,
                                related_name="casting_meta")
    callback_description = models.TextField(blank=True)
    cast_list_description = models.TextField(blank=True)
    contact_email = models.EmailField(blank=True)
    release_meta = models.ForeignKey(
        CastingReleaseMeta, verbose_name=CastingReleaseMeta._meta.verbose_name)

    class Meta:
        verbose_name = "Casting Information"
        verbose_name_plural = "Casting Information"

    def __str__(self):
        return str(self.show)
        
    @property
    def audition_slots(self):
        return self.slot_set.filter(type=Slot.TYPES[0][0])
    
    @property
    def callback_slots(self):
        return self.slot_set.filter(type=Slot.TYPES[1][0])

STANDARD_TIMES = (
    datetime.time(hour=18),
    datetime.time(hour=21),
    datetime.time(hour=0),
    datetime.time(hour=23, minute=30),
    datetime.time(hour=11),
    datetime.time(hour=19)
)
ALL_TIMES = list(sorted(
    [datetime.time(hour=i) for i in range(9, 24)] +
    [datetime.time(hour=i, minute=30) for i in range(9, 24)]))
ALL_TIMES.append(datetime.time())
def make_time_choices(times):
    return tuple(zip(times, [i.strftime("%I:%M %p") for i in times]))
STANDARD_TIME_CHOICES = make_time_choices(STANDARD_TIMES)
ALL_TIME_CHOICES = make_time_choices(ALL_TIMES)
TIME_CHOICES = (
    ("Common Times", STANDARD_TIME_CHOICES),
    ("All Times", ALL_TIME_CHOICES)
)

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
    
    def __str__(self):
        return "{} Slot for {}".format(Slot.TYPES[self.type][1], self.show)
