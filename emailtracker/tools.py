from django.contrib.auth import get_user_model
from anymail.message import AnymailMessage
from django.template.loader import get_template

from .models import *
from .utils import *
from .tasks import *

class EmailSent(RuntimeError): pass

def reschedule_all(name=None):
    emails = QueuedEmail.objects.filter(sent=False)
    if name:
        emails = emails.filter(name=name)
    pks = emails.values_list("pk")
    for i in pks:
        send_queued.delay(i[0])
    return len(pks)

def queue_msg(msg, name, ident=""):
    obj, created = QueuedEmail.objects.get_or_create(
        name=name, ident=ident, to=extract_address(msg.to[0]))
    if obj.sent:
        raise EmailSent(
            "Attempting to queue message that has already been sent.")
    else:
        obj.set_msg(msg)
        obj.save()
        send_queued.delay(obj.pk)

def _fix_to(kwargs):
    if type(kwargs["to"]) not in ("list", "tuple"):
        kwargs["to"] = [kwargs["to"]]
        
def queue_email(name, ident="", **kwargs):
    _fix_to(kwargs)
    msg = AnymailMessage(**kwargs)
    return queue_msg(msg, name, ident)

def render_to_queue(template, name, ident="", context={}, images={}, **kwargs):
    _fix_to(kwargs)
    msg = AnymailMessage(**kwargs)
    context["MESSAGE"] = msg
    
    template = get_template(template)
    
    context["IS_HTML"] = False
    msg.body = template.render(context)
    
    context["IS_HTML"] = True
    msg.attach_alternative(template.render(context), 'text/html')

    return queue_msg(msg, name, ident)

def render_for_user(user, *args, adjust_ident=True, **kwargs):
    context = kwargs.setdefault("context", {})
    context["user"] = user
    context["to"] = email_from_user(user)
    if adjust_ident:
        kwargs["ident"] = kwargs.get("ident", "") + "-" + user.email
    return render_to_queue(*args, **kwargs)

def render_for_users(users, *args, **kwargs):
    for u in users:
        queue_for_user(u, *args, **kwargs)
