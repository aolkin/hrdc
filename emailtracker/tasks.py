from celery import shared_task

from importlib import import_module

import logging

LOGGER = logging.getLogger(__name__)

@shared_task(acks_late=True, ignore_result=True)
def send_queued(pk):
    email = import_module('emailtracker.models').QueuedEmail.objects.get(pk=pk)
    email.send()

@shared_task(ignore_result=True)
def send_missing():
    n = import_module('emailtracker.tools').reschedule_all()
    if n:
        LOGGER.warn("{} unsent emails rescheduled.".format(n))
