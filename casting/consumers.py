from channels.generic.websockets import JsonWebsocketConsumer

from .utils import test_pdsm
from .models import CastingMeta

class TablingConsumer(JsonWebsocketConsumer):
    http_user = True

    def connection_groups(self, **kwargs):
        return ["auditions-building-{}".format(kwargs["building"])]

    def connect(self, message, **kwargs):
        if not test_pdsm(message.user):
            message.reply_channel.send({"close": True})
            return False
        super().connect(message, **kwargs)
        
class ShowConsumer(JsonWebsocketConsumer):
    http_user = True

    def connection_groups(self, **kwargs):
        return ["auditions-show-{}".format(kwargs["show"])]

    def connect(self, message, **kwargs):
        if not (test_pdsm(message.user) and (CastingMeta.objects.get(
                pk=kwargs["show"]).show.staff.filter(
                    pk=message.user.pk))):
            message.reply_channel.send({"close": True})
            return False
        super().connect(message, **kwargs)
