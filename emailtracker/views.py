from django.shortcuts import render
from django.conf import settings
from django.conf.urls import url

class _DummyMessage:
    def __getattr__(self, attr):
        return self
    
    def __call__(self, *args, **kwargs):
        return

def preview(request):
    context = {
        "IS_HTML": int(request.GET.get("html", 1)),
        "MESSAGE": _DummyMessage(),
        "SUBJECT": "Email Preview",
    }
    return render(request, request.GET["template"], context)

urlpatterns = []
if settings.DEBUG:
    urlpatterns.append(url(r'^$', preview))
