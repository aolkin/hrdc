from django.contrib.auth import get_user_model
from anymail.message import AnymailMessage
from django.template.loader import get_template
import logging, bleach, re

from .models import *
from .utils import *
from .tasks import *

logger = logging.getLogger("emailtracker.tools")

class EmailSent(RuntimeError): pass

def reschedule_all(name=None):
    emails = QueuedEmail.objects.filter(sent=None).exclude(status="<Missing>")
    if name:
        emails = emails.filter(name=name)
    pks = emails.values_list("pk")
    for i in pks:
        send_queued.delay(i[0])
    return len(pks)

def exists(name, ident, to):
    return QueuedEmail.objects.filter(
        name=name, ident=str(ident), to=extract_address(to)).exists()

def queue_msg(msg, name, ident="", silent=True):
    obj, created = QueuedEmail.objects.get_or_create(
        name=name, ident=str(ident), to=extract_address(msg.to[0]))
    if obj.sent:
        if not silent:
            raise EmailSent(
                "Attempting to queue message that has already been sent.")
    else:
        obj.set_msg(msg)
        obj.save()
        send_queued.delay(obj.pk)

def _fix_to(kwargs):
    if type(kwargs["to"]) not in ("list", "tuple"):
        kwargs["to"] = [kwargs["to"]]
        
def queue_email(name, ident="", silent=True, **kwargs):
    _fix_to(kwargs)
    msg = AnymailMessage(**kwargs)
    return queue_msg(msg, name, ident, silent)

NEWLINE_COLLAPSE_RE = re.compile('\n\\W*\n')
WHITESPACE_COLLAPSE_RE = re.compile('[ \t]{2,}')

def render_to_queue(template, name, ident="", context={}, silent=True,
                    **kwargs):
    _fix_to(kwargs)
    msg = AnymailMessage(**kwargs)
    context["MESSAGE"] = msg
    context["SUBJECT"] = kwargs.get("subject", "")
    
    template = get_template(template)

    context["IS_HTML"] = False
    text = bleach.clean(
        template.render(context),
        tags=[], strip=True)
    text = NEWLINE_COLLAPSE_RE.sub('\n\n', text)
    text = WHITESPACE_COLLAPSE_RE.sub('', text)
    msg.body = text.strip()
    
    context["IS_HTML"] = True
    msg.attach_alternative(template.render(context), 'text/html')

    return queue_msg(msg, name, ident, silent=silent)

def render_for_user(user, *args, **kwargs):
    if len(args) > 3:
        context = args[3]
    else:
        context = kwargs.setdefault("context", {})
    context["user"] = user
    kwargs["to"] = email_from_user(user)
    return render_to_queue(*args, **kwargs)

def render_for_users(users, *args, allow_failure=False, **kwargs):
    for u in users:
        try:
            render_for_user(u, *args, **kwargs)
        except Exception as e:
            if allow_failure:
                logger.error(e)
            else:
                raise e
