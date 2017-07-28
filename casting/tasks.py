from celery import shared_task

from importlib import import_module
from collections import defaultdict

from emailtracker.tools import render_for_user

from django.utils import timezone
from django.contrib.auth import get_user_model

class UnsubmittedShows(Exception): pass

def get_model(name):
    return getattr(import_module('casting.models'), name)

def get_crm(crm_pk):
    crm = get_model("CastingReleaseMeta").objects.get(pk=crm_pk)
    if crm.prevent_advancement:
        return None
    else:
        return crm

def get_shows(crm, arg):
    test_kwargs = { arg: False }
    if crm.castingmeta_set.filter(**test_kwargs).exists():
        raise UnsubmittedShows("Some shows have not submitted yet; waiting.")
    kwargs = { arg: True }
    metas = crm.castingmeta_set.filter(**kwargs)
    if metas.exists():
        return list(map(lambda x: x["pk"], metas.values("pk")))
    
@shared_task(ignore_result=True)
def release_callbacks(pk):
    crm = get_crm(pk)
    if crm and crm.stage == 0:
        shows = get_shows(crm, "callbacks_submitted")
        if shows:
            cbs = get_model("Callback").objects.filter(
                character__show__in=shows).order_by("character__show")
            actor_cbs = defaultdict(list)
            for i in cbs:
                actor_cbs[i.actor].append(i)
            for actor, acbs in actor_cbs.items():
                render_for_user(actor, "casting/email/callback.html",
                                "callbacks", crm.pk,
                                { "callbacks": acbs, "crm": crm },
                                subject="Your {} Callbacks".format(crm))
        crm.stage = 1
        crm.save()
    
@shared_task(ignore_result=True)
def release_first_round(pk):
    crm = get_crm(pk)
    if crm and crm.stage == 1:
        for i in crm.castingmeta_set.all().distinct().values("show__staff"):
            user = get_user_model().objects.get(pk=i["show__staff"])
            render_for_user(user, "casting/email/firstround.html",
                                "first-round", crm.pk,
                                { "crm": crm },
                                subject="{} First-Round Casting".format(crm))
        crm.stage = 2
        crm.save()

@shared_task(ignore_result=True)
def release_casting(pk):
    crm = get_crm(pk)
    if crm and crm.stage == 2:
        shows = get_shows(crm, "cast_submitted")
        if shows:
            signings = get_model("Signing").objects.filter(
                character__show__in=shows).order_by("character__show",
                                                    "order")
            actor_roles = defaultdict(list)
            for i in signings:
                actor_roles[i.actor].append(i)
            for actor, roles in actor_roles.items():
                if not actor.login_token:
                    actor.new_token()
                render_for_user(actor, "casting/email/casting.html",
                                "casting", crm.pk,
                                { "signings": roles, "crm": crm },
                                subject="Your {} Roles".format(crm))
        crm.stage = 3
        crm.save()

@shared_task(ignore_result=True)
def signing_email(pk):
    actor = get_user_model().objects.get(pk=pk)
    return render_for_user(actor, "casting/email/signing-link.html",
                           "requested-link", timezone.now(),
                           subject="Requested Casting Signing Link")

@shared_task(ignore_result=True)
def open_signing(pk):
    crm = get_crm(pk)
    if crm and crm.stage == 3:
        signings = get_model("Signing").objects.filter(
            character__show__in=get_shows(crm, "cast_submitted"))
        actors = [get_user_model().objects.get(pk=i[0]) for i in
                  signings.distinct().values_list("actor")]
        for actor in actors:
            firstroles = signings.filter(order=0, actor=actor)
            render_for_user(actor, "casting/email/signing.html",
                            "signing", crm.pk,
                            { "firstroles": firstroles, "crm": crm },
                            subject="Sign for {} Roles Now".format(crm))
        crm.stage = 4
        crm.save()

@shared_task(ignore_result=True)
def open_second_signing(pk):
    crm = get_crm(pk)
    if crm and crm.stage == 4:
        shows = get_shows(crm, "cast_submitted")
        signings = get_model("Signing").objects.filter(
            character__show__in=shows, order=0, response=None,
            character__allowed_signers=1)
        for i in signings:
            alternates = get_model("Signing").objects.filter(
                character=i.character, order__gte=1).exclude(
                    response=False)
            if alternates.exists():
                i.response = False
                i.timed_out = True
                i.save()
        crm.stage = 5
        crm.save()

@shared_task(ignore_result=True)
def notify_alternates(pk):
    signing = get_model("Signing").objects.get(pk=pk)
    previous = get_model("Signing").objects.filter(
        character=signing.character, order__lt=signing.order, response=False)
    if len(previous) != signing.order:
        return
    alternates = get_model("Signing").objects.filter(
        character=signing.character, order__gt=signing.order).exclude(
            response=False).select_related("character", "character__show")
    if alternates.exists():
        return render_for_user(alternates[0].actor,
                               "casting/email/role-available.html",
                               "role-available", pk,
                               { "role": alternates[0] },
                               subject="{} in {} Now Available".format(
                                   alternates[0].character,
                                   alternates[0].character.show))
      
@shared_task(ignore_result=True)
def update_releases(scheduled=True):
    releases = get_model("CastingReleaseMeta").objects.filter(
        prevent_advancement=False)
    cbs = releases.filter(publish_callbacks__lte=timezone.now(),
                          stage=0).values("pk")
    for i in cbs:
        release_callbacks.delay(i["pk"])
    cbs = releases.filter(publish_first_round_casts__lte=timezone.now(),
                          stage=1).values("pk")
    for i in cbs:
        release_first_round.delay(i["pk"])
    cbs = releases.filter(publish_casts__lte=timezone.now(),
                          stage=2).values("pk")
    for i in cbs:
        release_casting.delay(i["pk"])
    cbs = releases.filter(signing_opens__lte=timezone.now(),
                          stage=3).values("pk")
    for i in cbs:
        open_signing.delay(i["pk"])
    cbs = releases.filter(second_signing_opens__lte=timezone.now(),
                          stage=4).values("pk")
    for i in cbs:
        open_second_signing.delay(i["pk"])
