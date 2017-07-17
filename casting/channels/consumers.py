from channels.generic.websockets import (JsonWebsocketConsumer,
                                         WebsocketDemultiplexer)

from ..utils import test_pdsm
from ..models import CastingMeta

from .bindings import *

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
                pk=kwargs["show"]).show.user_is_staff(message.user))):
            message.reply_channel.send({"close": True})
            return False
        super().connect(message, **kwargs)

class CallbackConsumer(WebsocketDemultiplexer):
    http_user = True

    consumers = {
        "castingmeta": CastingMetaBinding.consumer,
        "character": CharacterBinding.consumer,
        "callback": CallbackBinding.consumer,
    }
    
    def connection_groups(self, **kwargs):
        return ["callbacks-show-{}".format(kwargs["show"])]

    def connect(self, message, **kwargs):
        if not (test_pdsm(message.user) and (CastingMeta.objects.get(
                pk=kwargs["show"]).show.user_is_staff(message.user))):
            message.reply_channel.send({"close": True})
            return False
        super().connect(message, **kwargs)
