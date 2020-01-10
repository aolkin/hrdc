from django.contrib.auth import get_user_model
from anymail.message import AnymailMessage
from django.template.loader import get_template
from django.db import transaction
import logging, bleach, re, time

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

def _query(name, ident, to):
    return QueuedEmail.objects.filter(
        name=name, ident=str(ident), to=extract_address(to))

def exists(*args, **kwargs):
    return _query(*args, **kwargs).exists()

def get(*args, **kwargs):
    obj = _query(*args, **kwargs)
    if obj.exists():
        return obj[0]
    else:
        return None

def queue_msg(msg, name, ident="", silent=True):
    if not ident:
        ident = time.time()
    obj, created = QueuedEmail.objects.get_or_create(
        name=name, ident=str(ident), to=extract_address(msg.to[0]))
    if obj.sent:
        if not silent:
            raise EmailSent(
                "Attempting to queue message that has already been sent.")
    else:
        obj.set_msg(msg)
        obj.save()
        transaction.on_commit(lambda id=obj.pk: send_queued.delay(id))
        return True

def _fix_to(kwargs):
    if type(kwargs["to"]) not in (list, tuple):
        kwargs["to"] = [kwargs["to"]]
        
def queue_email(name, ident="", silent=True, **kwargs):
    _fix_to(kwargs)
    msg = AnymailMessage(**kwargs)
    return queue_msg(msg, name, ident, silent)

NEWLINE_COLLAPSE_RE = re.compile('\n\\W*\n')
WHITESPACE_COLLAPSE_RE = re.compile('[ \t]{2,}')

def render_msg(template, context={}, **kwargs):
    msg = AnymailMessage(**kwargs)
    if "tags" in kwargs:
        msg.tags = kwargs["tags"]
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

    return msg

def render_to_queue(template, name, ident="", context={}, silent=True,
                    **kwargs):
    _fix_to(kwargs)
    if not kwargs["to"]:
        return False
    existing = get(name, ident, kwargs["to"][0])
    if existing and existing.sent:
        if silent:
            return
        else:
            raise EmailSent("Attempting to render and queue email that has "
                            "already been sent.")
    msg = render_msg(template, context, **kwargs)
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
