from django import template

from django.utils.text import slugify
from django.utils.html import format_html

register = template.Library()

def getattrs(obj, field=None):
    out = {}
    out["cls"] = slugify(obj.__class__.__name__)
    out["pk"] = getattr(obj, "pk", 0)
    out["id"] = '{}-{}'.format(out["cls"], out["pk"])
    out["field"] = field
    if field:
        out["id"] += '-{}'.format(field)
        out["name"] = obj._meta.get_field(field).verbose_name.title()
        out["value"] = getattr(obj, field)
    else:
        out["name"] = obj.__class__.__name__
        out["value"] = ""
    return out

@register.simple_tag
def boundattrs(obj=None, field=None, attrs=None):
    assert attrs or obj
    attrs = attrs or getattrs(obj, field)
    out = format_html('data-stream="{}" data-pk="{}" ',
                      attrs["cls"], attrs["pk"])
    #out += format_html('id="{}" ', attrs["id"])
    if attrs["field"]:
        out += format_html('placeholder="{}" ', attrs["name"])
        out += format_html('value="{}" ', attrs["value"])
        out += format_html('data-field="{}" ', attrs["field"])
    return out

@register.simple_tag
def boundinput(obj=None, field=None, classes="", attrs=None):
    return format_html('<input type="text" class="form-control {}" {}>',
                       classes, boundattrs(obj, field, attrs))

@register.simple_tag
def boundlabel(obj=None, field=None, label=None, classes="", attrs=None):
    assert (obj and field) or attrs
    attrs = attrs or getattrs(obj, field)
    return format_html('<label for="{}" class="{}">{}</label>', attrs["id"],
                       classes, label or attrs["name"])

@register.simple_tag
def helpp(obj, field, classes=""):
    helpt = obj._meta.get_field(field).help_text
    if helpt:
        return format_html('<p class="form-text text-muted {}">{}</p>',
                           classes, helpt)
    else:
        return ""

@register.simple_tag
def boundformgroup(obj, field, label=None, classes=""):
    attrs = getattrs(obj, field)
    return format_html('<div class="form-group">{} {} {}</div>',
                       boundlabel(label=label, attrs=attrs),
                       boundinput(attrs=attrs),
                       helpp(obj, field))
    
