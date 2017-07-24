from celery import shared_task

from django.utils import timezone

from importlib import import_module

@shared_task(acks_late=True)
def send_queued(pk):
    email = import_module('emailtracker.models').QueuedEmail.objects.get(pk=pk)
    if not email.sent:
        msg = email.get_msg()
        msg.send()
        if hasattr(msg, "anymail_status"):
            email.msg_id = str(msg.anymail_status.message_id)
            if email.to in msg.anymail_status.recipients:
                email.status = msg.anymail_status.recipients[email.to]
            else:
                email.status = "<Unknown>"
        else:
            email.status = "<Not AnyMail>"
        email.sent = timezone.now()
        email.save()
