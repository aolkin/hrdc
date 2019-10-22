from django.db import models

from django.urls import reverse
from django.utils.html import mark_safe

from django.conf import settings

class Link(models.Model):
    url = models.SlugField(unique=True, verbose_name="Short URL")
    destination = models.URLField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "/" + self.url
    
    @property
    def link(self):
        try:
            return settings.SHORTLINK_PREFIX + self.url
        except AttributeError:
            return settings.SITE_URL.partition("://")[2] + reverse(
                "shortlink", kwargs={"slug": self.url})

    def link_markup(self):
        return mark_safe(
            '<a href="http://{0}" target="blank">{0}</a>'.format(self.link))
    link_markup.short_description = "Shortlink"
        
    def get_absolute_url(self):
        return "http://" + self.link
