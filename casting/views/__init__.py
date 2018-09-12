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
    return Slot.objects.current_slots()

def get_active_slot(show):
    return Slot.objects.active_slot(show)

show_model = apps.get_model(settings.SHOW_MODEL)
building_model = apps.get_model(settings.BUILDING_MODEL)

@user_passes_test(test_board)
def admin(request):
    shows = show_model.objects.current_season().filter(
        casting_meta__isnull=False)
    if not shows.exists():
        return redirect("casting:index")
    cm = shows[0].casting_meta
    if cm.release_meta.stage < 1:
        return redirect("casting:view_callbacks", cm.pk)
    else:
        return redirect("casting:view_cast", cm.pk)
    return render(request, "bt/default.html")
admin.verbose_name = "Common Casting"
admin.help_text = "view Common Casting lists"
