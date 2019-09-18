from django.apps import AppConfig

from importlib import import_module

class DramaorgConfig(AppConfig):
    name = 'dramaorg'
    verbose_name = "Organization Data"

    def ready(self):
        views = import_module("dramaorg.views")
        views.load_indexes()
