from django.db import models

from django.conf import settings

from dramaorg.models import Space, Season, Show, StaffMember

class VenueApp(Season):
    managers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name="venue_manager",
        help_text="These users will get application submission notifications.")
    readers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        help_text="These users can view submitted applications.")

    venue = models.ForeignKey(Space, on_delete=models.PROTECT)
    prelim_due = models.DateTimeField()
    full_due = models.DateTimeField()

    instructions = models.TextField()

class AvailableDates(models.Model):
    venue = models.ForeignKey(VenueApp, on_delete=models.CASCADE)
    start = models.DateField()
    end = models.DateField()

class Application(models.Model):
    show = models.ForeignKey(Show, on_delete=models.PROTECT)

    band_size = models.CharField(max_length=80)
    cast_breakdown = models.CharField(max_length=80)
    
    personnel_note = models.TextField()

    calendar = models.FileField()
    budget = models.FileField(help_text="Please submit a single document with separate budgets for each venue you are applying to.")

class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    resume = models.FileField()
    
class StaffApp(models.Model):
    app = models.ForeignKey(Application, on_delete=models.CASCADE)
    staff = models.ForeignKey(StaffMember, on_delete=models.CASCADE)
    resume = models.ForeignKey(Resume, on_delete=models.PROTECT)
    conflicts = models.TextField(blank=True)
    submission = models.FileField(null=True,
                                  verbose_name="Statement or design plan")
    
class SlotPreference(models.Model):
    app = models.ForeignKey(Application, on_delete=models.CASCADE)
    venue = models.ForeignKey(VenueApp, on_delete=models.CASCADE)
    ordering = models.PositiveSmallIntegerField(default=1)
    start = models.DateField()
    end = models.DateField()
