from django.db import models
from django.contrib import auth
from django.conf import settings
from django.utils import timezone
from django.db.models.functions import Concat
from django.db.models.signals import post_save, pre_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.text import slugify

from django.core.exceptions import ValidationError

import hashlib, base64, uuid, datetime, re

from config import config

from .utils import get_admin_group
from . import email

class UserManager(auth.models.BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        return self.create_user(email, password, is_superuser=True)

def generate_token():
    b = hashlib.blake2b(uuid.uuid4().bytes).digest()
    return base64.b64encode(b)[:-2].decode().replace("/","-")

class User(auth.models.AbstractBaseUser, auth.models.PermissionsMixin):
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    first_name = models.CharField(max_length=80, db_index=True)
    last_name = models.CharField(max_length=80, db_index=True)
    email = models.CharField(max_length=254, unique=True, db_index=True)
    phone = models.CharField(max_length=20, verbose_name="Phone Number")
    year = models.PositiveSmallIntegerField(null=True, blank=True,
                                            verbose_name="Graduation Year")
    affiliation = models.CharField(max_length=160,
                                   verbose_name="School or Affiliation")
    display_affiliation = models.BooleanField(
        default=False,
        help_text="Include your affiliation with your name and year?")
    pgps = models.CharField(max_length=20, blank=True,
                            verbose_name="Preferred Gender Pronouns")
    gender_pref = models.CharField(max_length=30, blank=True,
                                   verbose_name="Preferred Stage Gender")

    suspended_until = models.DateField(null=True, blank=True)

    @property
    def is_suspended(self):
        return (self.suspended_until and
                self.suspended_until > timezone.localdate())
    
    source = models.CharField(default="default", editable=False,
                              max_length=20)
    post_register = models.CharField(default="", editable=False, max_length=240)
    
    is_active = models.BooleanField(default=True)
    login_token = models.CharField(max_length=86, default=generate_token)
    token_expiry = models.DateTimeField(default=timezone.now)

    admin_access = models.BooleanField(
        default=False, help_text="Has access to this administrative portal")
    
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()

    class Meta:
        permissions = (
            ("modify_user", "Can modify user account details"),
        )

    def set_password(self, *args, **kwargs):
        self.clear_token(False)
        super().set_password(*args, **kwargs)
    
    def new_token(self, save=True, expiring=False):
        self.login_token = generate_token()
        if expiring:
            self.token_expiry = (timezone.now() +
                                 datetime.timedelta(hours=1))
        else:
            self.token_expiry = timezone.now()
        if save:
            self.save()
        return self.login_token

    def clear_token(self, save=True):
        self.login_token = ""
        self.token_expiry = timezone.now()
        if save:
            self.save()

    def pretty_phone(self, partial=""):
        phone = partial or re.sub(r'\D', '', self.phone)
        if len(phone) > 10:
            return "+{} {}".format(phone[:-10], self.pretty_phone(phone[-10:]))
        elif len(phone) > 7:
            return "({}) {}".format(phone[:-7], self.pretty_phone(phone[-7:]))
        elif len(phone) > 4:
            return "{}-{}".format(phone[:-4], self.pretty_phone(phone[-4:]))
        else:
            return phone

    def affiliationyear(self):
        if self.year:
            return "{} ({})".format(self.affiliation, self.year)
        return self.affiliation
    affiliationyear.short_description = "Affiliation"
    affiliationyear.admin_order_field = Concat("affiliation", "year")
    
    @property
    def apostrophe_year(self):
        if self.year and len(str(self.year)) == 4:
            return "'" + str(self.year)[-2:]
        return ""

    @property
    def is_initialized(self):
        return bool(self.first_name and self.last_name and self.phone and
                    self.affiliation)

    @property
    def is_board(self):
        return self.groups.filter(id=get_admin_group().id).exists()
    
    @property
    def is_pdsm(self):
        return self.show_set.exists()
    
    @property
    def is_season_pdsm(self):
        return self.show_set.current_season().exists()
    
    @property
    def is_staff(self):
        return self.admin_access or self.is_superuser or self.is_board
    
    def get_full_name(self, use_email=True):
        full_name = '{} {}'.format(self.first_name, self.last_name).strip()
        if full_name:
            return full_name
        elif use_email:
            return "<{}>".format(self.email)
        else:
            return ""
    get_full_name.short_description = "Full Name"
    get_full_name.admin_order_field = "first_name"
    
    def get_short_name(self):
        return self.first_name.strip()

    def __str__(self):
        if self.is_board:
            return self.get_full_name() + " ({})".format(
                get_admin_group().name)
        return self.get_full_name()

    @property
    def display_name(self):
        extra = year = ""
        if self.apostrophe_year:
            year = self.apostrophe_year
        elif self.display_affiliation:
            year = str(self.year) if self.year else ""
        if year:
            extra = " " + year
        if self.display_affiliation:
            extra = "({}{})".format(self.affiliation, year)
        return self.get_full_name() + (" " + extra if extra else "")

@receiver(post_save, sender=User)
def invite_user(sender, instance, created, raw, **kwargs):
    if sender == User and created and not instance.password:
        if instance.source == "default":
            email.activate(instance)

@receiver(user_logged_in)
def clear_token_on_user(sender, request, user, **kwargs):
    user.clear_token()

class Building(models.Model):
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.name
        
class Space(models.Model):
    name = models.CharField(max_length=150)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    include_building_name = models.BooleanField(
        default=True, help_text="uncheck this to hide the building name when "+
        "displaying the full name of the space")
    nickname = models.CharField(
        max_length=150, blank=True,
        help_text="If set, the space will be displayed using this name.")

    def full_name(self):
        if self.nickname:
            return self.nickname
        elif self.include_building_name:
            return "{} - {}".format(self.building, self.name)
        else:
            return self.name
    
    def __str__(self):
        return self.full_name()

    class Meta:
        unique_together = (("name", "building"),)
    
def _get_year():
    return timezone.now().year

class SeasonManager(models.Manager):
    def in_season(self, obj):
        return self.filter(year=obj.year, season=obj.season)
    
    def current_season(self):
        return self.filter(
            year=config.get(settings.ACTIVE_YEAR_KEY, None),
            season=config.get(settings.ACTIVE_SEASON_KEY, None))

    def get_or_create_in_season(self, season, *args, **kwargs):
        kwargs["year"] = season.year
        kwargs["season"] = season.season
        return super().get_or_create(*args, **kwargs)

class Season(models.Model):    
    SEASONS = (
        (0, "Winter"),
        (1, "Spring"),
        (2, "Summer"),
        (3, "Fall"),
    )
    year = models.PositiveSmallIntegerField(default=_get_year)
    season = models.PositiveSmallIntegerField(choices=SEASONS, default=3)

    objects = SeasonManager()

    @property
    def seasonname(self):
        return Season.SEASONS[self.season][1]
    
    def seasonstr(self):
        return "{} {}".format(self.seasonname, self.year)
    seasonstr.short_description = "Season"
    
    class Meta:
        abstract = True

class ShowManager(SeasonManager):
    def occurring(self):
        return self.exclude(
            space=None, residency_starts=None, residency_ends=None)

class Show(Season):
    TYPES = (
        ("play", "Play"),
        ("musical", "Musical or Opera"),
        ("dance", "Dance Performance"),
        ("devised", "Devised Piece"),
        ("workshop", "Workshop"),
        ("other", "Other"),
    )

    title = models.CharField(max_length=150)

    creator_credit = models.CharField(max_length=300,
                                      verbose_name="Author/Composer")
    affiliation = models.CharField(
        max_length=60, blank=True, verbose_name="Sponsorship/Affiliation",
        help_text="Producing or sponsoring group, if applicable.")
    prod_type = models.CharField(default="play", choices=TYPES, max_length=30,
                                 verbose_name="Production Type")
    
    staff = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    space = models.ForeignKey(Space, null=True, on_delete=models.SET_NULL,
                              verbose_name="Venue")

    residency_starts = models.DateField(null=True)
    residency_ends = models.DateField(null=True)
    
    slug = models.SlugField(unique=True, db_index=True)
    invisible = models.BooleanField(default=False)

    liaisons = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                      related_name="liaison_shows")
    
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = ShowManager()

    def __contains__(self, other):
        return ((other.residency_starts < self.residency_ends and
                 other.residency_starts >= self.residency_starts) or
                (other.residency_ends <= self.residency_ends and
                 other.residency_ends > self.residency_starts))
    
    @property
    def residency_length(self):
        return self.residency_ends - self.residency_starts
    
    def __str__(self):
        return self.title
    
    def people(self):
        return ", ".join([i.get_full_name() for i in self.staff.all()])
    people.short_description = "Exec Staff"

    def user_is_staff(self, user):
        return self.staff.filter(pk=user.pk).exists()

    def clean(self):
        if (self.residency_starts and self.residency_ends and
            self.residency_ends < self.residency_starts):
            raise ValidationError("Residency cannot end before it begins!")
        return super().clean()

    @property
    def enabled_apps(self):
        return [v.related_model.__module__.partition(".")[0]
                for k, v in self._meta.fields_map.items()
                if type(v) == models.OneToOneRel and hasattr(self, k) and
                k != "application"]
    
    @property
    def apps_str(self):
        return ", ".join([i.capitalize() for i in self.enabled_apps])

    class Meta:
        permissions = (
            ("change_current_season", "Can change the current season"),
        )
        ordering = ("-residency_starts", "-residency_ends")

@receiver(pre_save)
def fix_slug(sender, instance, raw, *args, **kwargs):
    if sender == Show and not raw:
        if not instance.slug:
            instance.slug = slugify(instance.title)
        i = 2
        slug = instance.slug
        while Show.objects.filter(slug=instance.slug).exclude(
                pk=instance.pk).exists():
            instance.slug = "{}-{}".format(slug, i)
            i += 1
