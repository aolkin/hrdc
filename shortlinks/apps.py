from django.apps import AppConfig

from utils import (add_all_permissions, add_change_permissions,
                   add_view_permissions, add_delete_permissions)

from importlib import import_module

class ShortlinksConfig(AppConfig):
    name = 'shortlinks'

    def ready(self):
        models = import_module("shortlinks.models")
        add_all_permissions(models.Link)
