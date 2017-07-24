from django import template
from django.urls import reverse

register = template.Library()

@register.inclusion_tag("emailtracker/image.html", takes_context=True)
def image(context, fn, alt="Image"):
    cid = context["MESSAGE"].attach_inline_image_file(fn)
    return { "cid": cid, "alt": alt }

@register.inclusion_tag("emailtracker/href.html", takes_context=True)
def href(context, url, text, *args, **kwargs):
    return { "url": reverse(url, args=args, kwargs=kwargs),
             "text": text,
             "is_html": context["IS_HTML"] }
    
