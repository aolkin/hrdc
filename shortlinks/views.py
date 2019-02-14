from django.shortcuts import redirect, get_object_or_404

from .models import Link

def link(request, slug):
    l = get_object_or_404(Link, url=slug)
    return redirect(l.destination)
