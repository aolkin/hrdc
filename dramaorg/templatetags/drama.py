from django import template
from django.conf import settings
from config import config

from ..models import Season

register = template.Library()

@register.simple_tag
def current_season():
    return "{} {}".format(
        Season.SEASONS[config.get_int(
            settings.ACTIVE_SEASON_KEY, 0)][1],
        config.get(settings.ACTIVE_YEAR_KEY, ""))
