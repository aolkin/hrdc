from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.apps import apps

from ..models import *

from ..utils import *

from config import config
from datetime import timedelta

def get_current_slots():
    return Slot.objects.auditions().filter(
        day=timezone.localdate(),
        start__lte=timezone.localtime() + timedelta(
            minutes=config.get_float("casting_advance_signin_minutes", 0)),
        end__gte=timezone.localtime())

def get_active_slot(show):
    slots = get_current_slots().filter(show_id=show)
    return slots[0] if slots else None

show_model = apps.get_model(settings.SHOW_MODEL)
building_model = apps.get_model(settings.BUILDING_MODEL)

@user_passes_test(test_board)
def admin(request):
    cm = show_model.objects.current_season().filter(
        casting_meta__isnull=False)[0].casting_meta
    if cm.release_meta.stage < 1:
        return redirect("casting:view_callbacks", cm.pk)
    else:
        return redirect("casting:view_cast", cm.pk)
    return render(request, "bt/default.html")
admin.verbose_name = "Common Casting"
admin.help_text = "view Common Casting lists"
