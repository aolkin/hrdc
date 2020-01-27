from django import template
from django.utils.html import format_html
from decimal import Decimal

register = template.Library()

@register.filter
def accounting_fmt(val):
    if not val or val == 0:
        return format_html('<span class="">-</span>')
    if type(val) != Decimal:
        val = Decimal(val)
    val = val.quantize(Decimal('.01'))
    if val < 0:
        return format_html('<span class="text-danger">$ ({})</span>', val * -1) 
    else:
        return format_html('<span class="">$ {}</span>', val)
