from django.apps import AppConfig

from utils import add_all_permissions, add_change_permissions

from importlib import import_module

class CastingConfig(AppConfig):
    name = 'casting'
    verbose_name = "Common Casting"

    def ready(self):
        models = import_module("casting.models")
        add_all_permissions(models.Slot)
        add_change_permissions(models.CastingMeta,
                               models.CastingReleaseMeta)
