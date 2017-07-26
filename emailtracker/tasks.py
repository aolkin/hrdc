from celery import shared_task

from importlib import import_module

@shared_task(acks_late=True, ignore_result=True)
def send_queued(pk):
    email = import_module('emailtracker.models').QueuedEmail.objects.get(pk=pk)
    email.send()
