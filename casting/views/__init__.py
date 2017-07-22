from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.apps import apps

from ..models import *

from ..utils import *

def get_current_slots():
    return Slot.objects.auditions().filter(
        day=timezone.localdate(),
        start__lte=timezone.localtime(),
        end__gte=timezone.localtime())

show_model = apps.get_model(settings.SHOW_MODEL)
building_model = apps.get_model(settings.BUILDING_MODEL)

@user_passes_test(test_board)
def admin(request):
    return render(request, "bt/default.html")
admin.verbose_name = "Common Casting"
admin.help_text = "administer Common Casting"
