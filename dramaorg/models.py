from django.db import models
from django.contrib import auth
from django.conf import settings
from django.utils import timezone
from django.db.models.functions import Concat
from django.db.models.signals import post_save, pre_save, post_init
from django.contrib.postgres.fields import CIEmailField
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from django.core.exceptions import ValidationError

import hashlib, base64, uuid, datetime, re, urllib.parse

from config import config

from .utils import get_admin_group
from . import email
from . import mailchimp

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
    email = CIEmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, verbose_name=_("Phone Number"))
    year = models.PositiveSmallIntegerField(null=True, blank=True,
                                            verbose_name=_("Graduation Year"))
    affiliation = models.CharField(max_length=160,
                                   verbose_name=_("School or Affiliation"))
    display_affiliation = models.BooleanField(
        default=False,
        help_text=_("Display your affiliation with your name?"))
    pgps = models.CharField(max_length=20, blank=True,
                            verbose_name=_("Preferred Gender Pronouns"))
    gender_pref = models.CharField(max_length=30, blank=True,
                                   verbose_name=_("Preferred Stage Gender"))

    subscribed = models.BooleanField(
        default=True, verbose_name=_("Subscribe to the Newsletter"),
        help_text=_("Uncheck this to unsubscribe."))

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
            extra = " ({}{})".format(self.affiliation, extra)
        return self.get_full_name() + extra

    def __str__(self):
        if self.is_board:
            return self.get_full_name() + " ({})".format(
                get_admin_group().name + " Account")
        return self.display_name

@receiver(post_save, sender=User)
def invite_user(sender, instance, created, raw, **kwargs):
    if sender == User and not raw and created and not instance.password:
        if instance.source == "default":
            email.activate(instance)

@receiver(post_init, sender=User)
def prep_mailchimp(sender, instance, **kwargs):
    instance._was_subscribed = instance.subscribed
    instance._mailchimp_status = None

@receiver(pre_save, sender=User)
def check_mailchimp(sender, instance, raw, **kwargs):
    # Check presence of affiliation to ensure complete profile
    if mailchimp.enabled() and instance.affiliation and not raw:
        status = mailchimp.Contact(instance.email).get_status()
        instance._mailchimp_status = status
        if instance._was_subscribed == instance.subscribed:
            if status not in ("missing", "error"):
                instance.subscribed = status == mailchimp.SUBSCRIBED

@receiver(post_save, sender=User)
def sync_mailchimp(sender, instance, created, raw, **kwargs):
    # Check presence of affiliation to ensure complete profile
    if mailchimp.enabled() and instance.affiliation and not raw:
        contact = mailchimp.Contact(instance.email)
        if instance.subscribed:
            if instance._mailchimp_status == "missing":
                fields = {
                    "NAME": instance.get_full_name(False),
                    "PHONE": instance.phone,
                    "YEAR": instance.year,
                    "PGPS": instance.pgps,
                    "AFFIL": instance.affiliation,
                }
                contact.create(fields)
            elif instance._mailchimp_status == mailchimp.UNSUBSCRIBED:
                contact.update_status(mailchimp.SUBSCRIBED)
        else:
            if instance._mailchimp_status == mailchimp.SUBSCRIBED:
                contact.update_status(mailchimp.UNSUBSCRIBED)

@receiver(user_logged_in)
def clear_token_on_user(sender, request, user, **kwargs):
    user.clear_token()

class Building(models.Model):
    name = models.CharField(max_length=150)
    address = models.TextField(blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    @property
    def maps_link(self):
        if self.address:
            query = self.name + ", " + self.address.replace("\n", ", ")
        elif self.latitude and self.longitude:
            query = "{},{}".format(self.latitude, self.longitude)
        else:
            return ""
        query = urllib.parse.quote_plus(query)
        return "https://www.google.com/maps/search/?api=1&query=" + query

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
    order = models.PositiveSmallIntegerField(default=0)

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
        ordering = ("order",)
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
        ("play", _("Play")),
        ("musical", _("Musical or Opera")),
        ("dance", _("Dance Performance")),
        ("devised", _("Devised Piece")),
        ("workshop", _("Workshop")),
        ("other", _("Other")),
    )

    title = models.CharField(max_length=150)

    creator_credit = models.CharField(max_length=300,
                                      # Translators: site-wide show metadata
                                      verbose_name=_("Author/Composer"))
    affiliation = models.CharField(
        # Translators: this is used for the site-wide show metadata field
        max_length=60, blank=True, verbose_name=_("Sponsorship/Affiliation"),
        # Translators: this is used for the site-wide show metadata field
        help_text=_("Producing or sponsoring group, if applicable."))
    prod_type = models.CharField(default="play", choices=TYPES, max_length=30,
        # Translators: this is used for the site-wide show metadata field
                                 verbose_name=_("Production Type"))

    staff = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True)
    space = models.ForeignKey(Space, null=True, on_delete=models.PROTECT,
                              verbose_name="Venue")

    residency_starts = models.DateField(null=True)
    residency_ends = models.DateField(null=True)

    slug = models.SlugField(unique=True, db_index=True, max_length=120)
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

    @property
    def name(self):
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
    def liaison_str(self):
        return ", ".join([str(i.get_full_name()) for i in self.liaisons.all()])

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
        i = 1
        slug = instance.slug
        while Show.objects.filter(slug=instance.slug).exclude(
                pk=instance.pk).exists():
            if i == 1:
                instance.slug = "{}-{}".format(slug, instance.year)
            else:
                instance.slug = "{}-{}".format(slug, i)
            i += 1
