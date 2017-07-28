
from django.urls import reverse
from django.conf import settings

from django.core.mail import EmailMultiAlternatives

from config import config

def send_invite(user):
    url = (settings.SITE_URL +
           reverse("dramaorg:token_reset", args=(user.login_token,)))
    msg = EmailMultiAlternatives(
        subject="Please activate your account",
        body="Click to activate your account: {}".format(url),
        to=[user.email])
    msg.send()

def send_reset(user):
    url = (settings.SITE_URL +
           reverse("dramaorg:token_reset", args=(user.login_token,)))
    msg = EmailMultiAlternatives(
        subject="Reset your password",
        body="A password reset was requested."
        "Please click here to reset your password: {}".format(url),
        to=[user.email])
    msg.send()
