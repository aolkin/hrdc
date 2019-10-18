from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

from django_thumbs.fields import ImageThumbsField

from config import config

import os.path

from dramaorg.models import Show

class ArchivalInfo(models.Model):
    show = models.OneToOneField(settings.SHOW_MODEL, on_delete=models.CASCADE,
                                related_name="archival_info")

    def pub_destination(instance, filename):
        return "archive/{}/{}/{}/pub/{}".format(
            instance.show.year, instance.show.get_season_display(),
            instance.show.slug, filename)
    poster = models.FileField(upload_to=pub_destination, blank=True)
    program = models.FileField(upload_to=pub_destination, blank=True)

    is_published = models.BooleanField(default=False)

    def poster_name(self):
        return os.path.basename(self.poster.name)

    def program_name(self):
        return os.path.basename(self.program.name)
    
    def __str__(self):
        return str(self.show)

    def get_absolute_url(self):
        return reverse_lazy("archive:show", args=(self.pk,))

    @property
    def complete(self):
        return (self.poster and self.program and
                self.productionphoto_set.count() >=
                config.get_int("archive_min_photos", 0))

    class Meta:
        verbose_name = "Show in archive"
        verbose_name_plural = "Shows in Archive"

class ExtraFile(models.Model):
    def upload_destination(instance, filename):
        return "archive/{}/{}/{}/files/{}".format(
            instance.show.show.year, instance.show.show.get_season_display(),
            instance.show.show.slug, filename)

    show = models.ForeignKey(ArchivalInfo, on_delete=models.PROTECT)
    credit = models.CharField(max_length=120)
    description = models.CharField(max_length=240)
    file = models.FileField(upload_to=upload_destination)

    def __str__(self):
        return "{} by {}".format(os.path.basename(self.file.name), self.credit)

    def filename(self):
        return os.path.basename(self.file.name)

class ProductionPhoto(models.Model):
    def upload_destination(instance, filename):
        return "archive/{}/{}/{}/photos/{}".format(
            instance.show.show.year, instance.show.show.get_season_display(),
            instance.show.show.slug, filename)

    THUMB_SIZES = (
        { "code": "thumb", "wxh": "320x240", "resize": "crop" },
        { "code": "preview", "wxh": "1200x1200", "resize": "scale" }
    )

    show = models.ForeignKey(ArchivalInfo, on_delete=models.PROTECT)
    credit = models.CharField(max_length=120)
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    img = ImageThumbsField(upload_to=upload_destination, sizes=THUMB_SIZES,
                           height_field="height", width_field="width")

    def __str__(self):
        return "{} by {}".format(os.path.basename(self.img.name), self.credit)
