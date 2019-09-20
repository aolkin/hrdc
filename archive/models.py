from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy

from dramaorg.models import Show

class ArchivalInfo(models.Model):
    show = models.OneToOneField(settings.SHOW_MODEL, on_delete=models.CASCADE,
                                related_name="archival_info")

    is_published = models.BooleanField(default=False)
    
    def __str__(self):
        return str(self.show)

    def get_absolute_url(self):
        return reverse_lazy("archive:show", args=(self.pk,))
