from django.db import models

from django.conf import settings

from django.contrib.auth import get_user_model

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
    
    # cast and staff

    class Meta:
        verbose_name = "Publicity-Enabled Show"

    def __str__(self):
        return str(self.show)

class PerformanceDate(models.Model):
    show = models.ForeignKey(PublicityInfo, on_delete=models.CASCADE,
                             db_index=True)
    performance = models.DateTimeField()

    class Meta:
        ordering = "performance",
        unique_together = "show", "performance"
    
    def __str__(self):
        return self.performance.strftime("%A, %B %-d at %-I:%M %p")

class ShowPerson(models.Model):
    TYPE_CHOICES = (
        (0, "Staff"),
        (1, "Cast")
    )
    
    show = models.ForeignKey(PublicityInfo, on_delete=models.CASCADE,
                             db_index=True)

    name = models.CharField(max_length=120, blank=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)

    position = models.CharField(max_length=120, blank=True)
    type = models.PositiveSmallIntegerField(default=0, choices=TYPE_CHOICES)

    def yearstr(self):
        return "'{:02d}".format(self.year % 100) if self.year else ""
    
    def __str__(self):
        return "{}: {} {}".format(self.position, self.name, self.yearstr())
