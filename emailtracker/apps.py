from django.apps import AppConfig

from django.conf import settings
            
from importlib import import_module

class EmailtrackerConfig(AppConfig):
    name = 'emailtracker'
    verbose_name = "Email Utilities"

    def ready(self):
        for i in settings.INSTALLED_APPS:
            try:
                import_module(i + ".emails")
            except ImportError:
                pass
