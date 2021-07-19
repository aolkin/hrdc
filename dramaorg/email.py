
from django.urls import reverse
from django.conf import settings

from django.core.mail import EmailMultiAlternatives

from emailtracker.tools import render_for_user

from config import config

import time

def activate(user, uniq=""):
    render_for_user(user, "dramaemail/activate.html",
                    "activate", str(user.pk) + str(uniq),
                    tags=["auth", "activate"],
                    subject="Welcome to {}".format(settings.BT_SITE_TITLE))

def send_reset(user):
    render_for_user(user, "dramaemail/reset.html", "reset", time.time(),
                    tags=["auth", "reset"], subject="Password Reset")
