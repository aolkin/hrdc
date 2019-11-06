from django import template

register = template.Library()

@register.filter
def forvenue(qs, venue):
    return qs.filter(venue=venue)

@register.filter
def forvenue_count(qs, venue):
    return qs.filter(venue=venue).count()

@register.filter
def forvenue_exists(qs, venue):
    return qs.filter(venue=venue).exists()
