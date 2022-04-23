import logging

from django.conf.urls import url
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings

from social_django.urls import urlpatterns as socialurls
from social_core.exceptions import AuthException

logger = logging.getLogger(__name__)

app_name = 'social'

urlpatterns = []

def wrapped(callback):
    def wrapper(request, *args, **kwargs):
        try:
            return callback(request, *args, **kwargs)
        except AuthException as e:
            logger.exception("AuthException while completing OAuth login")
            messages.error(request, str(e) + " Please try again.")
            return redirect(settings.LOGOUT_URL)
    return wrapper

for existing in socialurls:
    if existing.name == "complete":
        urlpatterns.append(url(existing.pattern, wrapped(existing.callback),
                               name="complete"))
    else:
        urlpatterns.append(existing)
