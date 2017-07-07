
from django.urls import reverse

from django.core.mail import EmailMultiAlternatives
from anymail.message import attach_inline_image_file

from config import config

def send_invite(user):
    url = (config.get("root_url","http://localhost") +
           reverse("token_create", args=(user.login_token,)))
    msg = EmailMultiAlternatives(
        subject="Please activate your account",
        body="Click to activate your account: {}".format(url),
        to=[user.email])
    msg.send()

def send_reset(user):
    pass
