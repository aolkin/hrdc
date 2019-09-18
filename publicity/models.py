from django.db import models
from django.conf import settings
from django.utils import timezone

from django.contrib.auth import get_user_model

from django.urls import reverse_lazy

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

    website_page = models.URLField(blank=True)

    class Meta:
        verbose_name = "Publicity-Enabled Show"

    def hidden_people(self):
        return self.showperson_set.filter(type=0)

    def staff(self):
        return self.showperson_set.filter(type=1)

    def cast(self):
        return self.showperson_set.filter(type=2)
    
    def get_absolute_url(self):
        return reverse_lazy("publicity:display", args=(self.id,))
    
    def __str__(self):
        return str(self.show)

    @property
    def next_performance(self):
        return self.performancedate_set.filter(
            performance__gte=timezone.now()).first()
    
class PerformanceDate(models.Model):
    show = models.ForeignKey(PublicityInfo, on_delete=models.CASCADE,
                             db_index=True)
    performance = models.DateTimeField()
    note = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = "performance",
        unique_together = "show", "performance"

    @property
    def datestr(self):
        return timezone.localtime(
            self.performance).strftime("%A, %B %-d at %-I:%M %p")
    
    def __str__(self):
        return self.datestr + (" ({})".format(self.note) if self.note else "")

class ShowPerson(models.Model):
    TYPE_CHOICES = (
        (0, "Hidden"),
        (1, "Staff"),
        (2, "Cast")
    )
    
    show = models.ForeignKey(PublicityInfo, on_delete=models.CASCADE,
                             db_index=True)

    name = models.CharField(max_length=120)
    year = models.PositiveSmallIntegerField(blank=True, null=True)

    email = models.EmailField(blank=True,
                              help_text="This will not be shown publicly.")
    phone = models.CharField(max_length=20, blank=True,
                             help_text="This will not be shown publicly.")
    
    position = models.CharField(max_length=120, verbose_name="Role or Position")
    
    type = models.PositiveSmallIntegerField(default=0, choices=TYPE_CHOICES,
                                            db_index=True)
    order = models.SmallIntegerField(db_index=True, default=0)
    
    class Meta:
        ordering = "type", "order",
        #unique_together = "order", "show", "type"
    
    def yearstr(self):
        return "'{:02d}".format(self.year % 100) if self.year else ""
    
    def __str__(self):
        return "{}: {} {}".format(self.position, self.name, self.yearstr())
