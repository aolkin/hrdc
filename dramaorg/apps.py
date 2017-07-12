from django.apps import AppConfig

from importlib import import_module

from .utils import add_change_permissions

class DramaorgConfig(AppConfig):
    name = 'dramaorg'
    verbose_name = "Organization Data"

    def ready(self):
        models = import_module("dramaorg.models")
        add_change_permissions(models.Show, models.User, models.Space,
                               models.Building)
