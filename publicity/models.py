from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.html import format_html, mark_safe
from django.urls import reverse_lazy, reverse

from config import config

import bleach

from django_thumbs.fields import ImageThumbsField

from collections import defaultdict

from dramaorg.models import Space, Season, Show

class PublicityInfo(models.Model):
    show = models.OneToOneField(settings.SHOW_MODEL, on_delete=models.CASCADE,
                                related_name="publicity_info")

    credits = models.TextField(blank=True, verbose_name="Masthead Credits", help_text="Include authorial credits, as well as directors and producers.")
    contact_email = models.EmailField(blank=True,
                                      verbose_name="Email for Publicity")
    runtime = models.CharField(
        max_length=80, blank=True,
        help_text="E.g. 2 hours with a 10-minute intermission")
    blurb = models.TextField(blank=True, verbose_name="About the Show")
    content_warning = models.TextField(blank=True)
    ticket_link = models.URLField(blank=True)
    band_term = models.CharField(max_length=20, blank=True, choices=(
        ("", "Not Applicable"),
        ("Band", "Band"),
        ("Orchestra", "Orchestra"),
        ("Musicians", "Musicians"),
    ), default="", verbose_name="Term for Pit Musicians")

    website_page = models.URLField(blank=True)

    def upload_destination(instance, filename):
        return "publicity/{}/{}/{}/covers/{}".format(
            instance.show.year, instance.show.get_season_display(),
            instance.show.slug, filename)
    THUMB_SIZES = (
        { "code": "thumb", "wxh": "320x240", "resize": "crop" },
        { "code": "cover", "wxh": "650x250", "resize": "scale" }
    )
    cover = ImageThumbsField(upload_to=upload_destination, sizes=THUMB_SIZES,
                             null=True, blank=True,
                             verbose_name="Cover Graphic")

    class Meta:
        verbose_name = "Publicity-Enabled Show"

    def hidden_people(self):
        return self.showperson_set.filter(type=0)

    def staff(self):
        return self.showperson_set.filter(type=1)

    def cast(self):
        return self.showperson_set.filter(type=2)

    def band(self):
        return self.showperson_set.filter(type=3)

    def get_absolute_url(self):
        return reverse_lazy("publicity:display", args=(self.id,))

    def embed_code(self, wrap=True):
        if self.id:
            code = '<script src="{}{}"></script>'.format(
                settings.SITE_URL, reverse("publicity:script", args=(self.id,),
                                           kwargs={"format": "js"}))
            if wrap:
                return format_html("<pre>{}</pre>", code)
            else:
                return code
        return format_html(
            "<i>Please save this object to view the embed code.</i>")

    @property
    def link(self):
        return self.website_page or config.publicity_shows_base_url + self.show.slug + "/"

    def __str__(self):
        return str(self.show)

    @property
    def next_performance(self):
        return self.performancedate_set.filter(
            performance__gte=timezone.now()).first()

class AbstractEvent:
    @property
    def performance_date(self):
        return timezone.localtime(self.performance).date()

    @property
    def datestr(self):
        return timezone.localtime(
            self.performance).strftime("%A, %B %-d at %-I:%M %p")

class AbstractEventModel(AbstractEvent, models.Model):
    performance = models.DateTimeField(verbose_name="Time and Date")
    note = models.CharField(max_length=120, blank=True)

    class Meta:
        abstract = True

class PerformanceDate(AbstractEventModel):
    show = models.ForeignKey(PublicityInfo, on_delete=models.CASCADE,
                             db_index=True)

    class Meta:
        ordering = "performance",
        unique_together = "show", "performance"

    @property
    def name(self):
        return str(self.show)

    @property
    def webpage(self):
        return self.show.link

    @property
    def venue(self):
        return self.show.show.space

    def __str__(self):
        return self.datestr + (" ({})".format(self.note) if self.note else "")

class Event(AbstractEventModel):
    name = models.CharField(max_length=120)

    venue = models.ForeignKey("dramaorg.Space", blank=True, null=True,
                              on_delete=models.PROTECT)
    webpage = models.URLField(blank=True)

    def __str__(self):
        return "{} @ {}".format(self.name, self.datestr)

class ShowPerson(models.Model):
    TYPE_CHOICES = (
        (0, "Hidden"),
        (1, "Staff"),
        (2, "Cast"),
        (3, "Band"),
    )

    show = models.ForeignKey(PublicityInfo, on_delete=models.PROTECT,
                             db_index=True)
    person = models.ForeignKey(get_user_model(), on_delete=models.PROTECT)

    @property
    def name(self):
        return self.person.get_full_name()

    @property
    def year(self):
        return self.person.year

    position = models.CharField(max_length=120, verbose_name="Role or Position",
                                blank=True)

    type = models.PositiveSmallIntegerField(default=0, choices=TYPE_CHOICES,
                                            db_index=True)
    order = models.SmallIntegerField(db_index=True, default=0)

    class Meta:
        ordering = "type", "order", "pk"

    def yearstr(self):
        return "'{:02d}".format(self.year % 100) if self.year else ""

    def __str__(self):
        return "{}: {}".format(self.position, self.person)

    @staticmethod
    def collate(qs):
        people = defaultdict(list)
        positions = []
        for person in qs:
            if not people[person.position]:
                positions.append((person.position, people[person.position]))
            people[person.position].append(person)
        return positions

SAFE_TAGS = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i',
             'li', 'ol', 'strong', 'ul', 'p', 'br']

class Announcement(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT,
                             verbose_name="Submitting user")

    title = models.CharField(max_length=100)
    message = models.TextField()
    graphic = models.ImageField(
        blank=True, help_text="Optional graphic to include with your message. "
        "Graphics may be ommitted at the editor's discretion.",
        upload_to='publicity/announcements/%Y/%m/%d/')
    note = models.TextField(blank=True, verbose_name="Note for the Editor",
                            help_text="This will not be published.")

    start_date = models.DateField(
        help_text="Do not include in the newsletter before this date.")
    end_date = models.DateField(
        help_text="Do not include in the newsletter after this date.")

    submitted = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    published = models.BooleanField(default=False)

    class Meta:
        ordering = ("-end_date", "start_date", "-submitted")

    @property
    def rendered_message(self):
        return mark_safe(bleach.clean(self.message, tags=SAFE_TAGS, strip=True))

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError({
                "start_date": "Must be before end date.",
                "end_date": "Must be after start date.",
            })

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse_lazy("publicity:edit_announcement", args=(self.pk,))

    def active(self):
        return (timezone.now().date() >= self.start_date and
                timezone.now().date() <= self.end_date)
    active.boolean = True
