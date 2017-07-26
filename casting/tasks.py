from celery import shared_task

from importlib import import_module
from collections import defaultdict

from emailtracker.tools import render_for_user

from django.utils import timezone

def get_model(name):
    return getattr(import_module('casting.models'), name)

def get_crm(crm_pk):
    crm = get_model("CastingReleaseMeta").objects.get(pk=crm_pk)
    if crm.prevent_advancement:
        return None
    else:
        return crm

@shared_task(ignore_result=True)
def release_callbacks(pk):
    crm = get_crm(pk)
    if crm and crm.stage == 0 and not crm.prevent_advancement:
        shows = list(map(lambda x: x["pk"],
                         crm.castingmeta_set.filter(
                             callbacks_submitted=True).values("pk")))
        if not shows:
            return
        cbs = get_model("Callback").objects.filter(
            character__show__in=shows).order_by("character__show")
        actor_cbs = defaultdict(list)
        for i in cbs:
            actor_cbs[i.actor].append(i)
        for actor, acbs in actor_cbs.items():
            render_for_user(actor, "casting/email/callback.html", "callbacks",
                            crm.pk, { "callbacks": acbs, "crm": crm },
                            subject="Your {} Callbacks".format(crm))
        crm.stage = 1
        crm.save()
    
@shared_task(ignore_result=True)
def release_first_round(pk):
    crm = get_crm(pk)
    if crm and crm.stage == 1:
        print(crm, crm.castingmeta_set.all())

@shared_task(ignore_result=True)
def update_releases(scheduled=True):
    releases = get_model("CastingReleaseMeta").objects.filter(
        prevent_advancement=False)
    cbs = releases.filter(publish_callbacks__lte=timezone.now(),
                          stage=0).values("pk")
    for i in cbs:
        release_callbacks.delay(i["pk"])
