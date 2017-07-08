from django.apps import AppConfig
from django.db.models import Q

from importlib import import_module

from .utils import get_admin_group

class DramaorgConfig(AppConfig):
    name = 'dramaorg'
    verbose_name = "Organization Data"

    def ready(self):
        group = get_admin_group()
        if group:
            Permission = import_module("django.contrib.auth.models").Permission
            cts = import_module("django.contrib.contenttypes.models")
            models = import_module("dramaorg.models")

            types = cts.ContentType.objects.get_for_models(models.Show,
                                                           models.User)
            q = Q(codename__contains="add") | Q(codename__contains="change")
            perms = Permission.objects.filter(q,
                                              content_type__in=types.values())
            group.permissions.add(*perms)
