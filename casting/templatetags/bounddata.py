from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify
from django.utils.html import format_html, mark_safe

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
        try:
            out["value"] = getattr(obj, field)
            if out["value"] is None or out["value"] is False:
                out["value"] = ""
        except ObjectDoesNotExist:
            out["value"] = ""
    else:
        out["name"] = obj.__class__.__name__
        out["value"] = ""
    return out

@register.simple_tag
def boundattrs(obj=None, field=None, attrs=None, **kwargs):
    assert attrs or obj
    attrs = attrs or getattrs(obj, field)
    attrs.update(kwargs)
    out = format_html('data-stream="{}" data-pk="{}" ',
                      attrs["cls"], attrs["pk"] or "")
    #out += format_html('id="{}" ', attrs["id"])
    if attrs["field"]:
        out += format_html('placeholder="{}" ',
                           attrs.get("placeholder", None) or attrs["name"])
        out += format_html('value="{}" ', attrs["value"])
        out += format_html('data-field="{}" ', attrs["field"])
    for i, j in [(i[5:], j) for i, j in attrs.items()
                 if i.startswith("attr_")]:
        if j != False:
            out += format_html('{}="{}" ' , i, j)
    return out

@register.simple_tag
def boundinput(obj=None, field=None, classes="", attrs=None, **kwargs):
    attrs = attrs or getattrs(obj, field)
    attrs.update(kwargs)
    attrs.setdefault("type", "text")
    return format_html('<input type="{}" class="form-control {}" {}>',
                       attrs["type"], classes, boundattrs(obj, field,
                                                          attrs=attrs))

@register.simple_tag
def boundlabel(obj=None, field=None, label=None, classes="", attrs=None):
    assert (obj and field) or attrs
    attrs = attrs or getattrs(obj, field)
    return format_html('<label for="{}" class="{}">{}</label>', attrs["id"],
                       classes, label or attrs["name"])

@register.simple_tag
def helpp(obj, field, classes="", small=False):
    helpt = obj._meta.get_field(field).help_text
    if helpt:
        out = format_html('<p class="form-text text-muted {}">{}</p>',
                          classes, helpt)
        return mark_safe("<small>{}</small>".format(out)) if small else out
    else:
        return ""

@register.simple_tag
def boundformgroup(obj, field, label=None, small=False, classes="", **kwargs):
    attrs = getattrs(obj, field)
    attrs.update(kwargs)
    if small:
        classes +=" form-control-sm"
    return format_html('<div class="form-group">{} {} {}</div>',
                       boundlabel(label=label, attrs=attrs) if
                       label != False else "",
                       boundinput(classes=classes, attrs=attrs),
                       helpp(obj, field, small=small))
    
