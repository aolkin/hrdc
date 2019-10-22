from django.apps import AppConfig

from importlib import import_module

class DramaorgConfig(AppConfig):
    name = 'dramaorg'
    verbose_name = "Ancillary Data"

    def ready(self):
        views = import_module("dramaorg.views")
        views.load_indexes()
