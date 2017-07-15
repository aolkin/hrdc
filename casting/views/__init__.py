from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.apps import apps

from ..models import *

from ..utils import *

class ShowEditor(UpdateView):
    model = CastingMeta
    fields = ("contact_email",)
    success_url = reverse_lazy("casting:index")
    template_name = "casting/show_editor.html"
    
    def test_func(self):
        return (self.request.user.is_authenticated() and
                self.get_object().show.staff.filter(
                    id=self.request.user.id).exists())

    def post(self, *args, **kwargs):
        if self.test_func():
            return super().post(*args, **kwargs)
        else:
            messages.error(self.request,
                           "You do not have access to that show.")
            return HttpResponseRedirect(reverse("login"))
        
    def get(self, *args, **kwargs):
        if not self.request.is_ajax():
            return HttpResponseRedirect(reverse("casting:index"))
        else:
            return super().get(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["legal"] = self.test_func()
        return context

def get_current_slots():
    return Slot.objects.auditions().filter(
        day=timezone.localdate(),
        start__lte=timezone.localtime(),
        end__gte=timezone.localtime())

building_model = apps.get_model(settings.BUILDING_MODEL)

@user_passes_test(test_board)
def admin(request):
    return render(request, "bt/default.html")
admin.verbose_name = "Common Casting"
admin.help_text = "administer Common Casting"
