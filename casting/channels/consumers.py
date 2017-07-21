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

class ListConsumer(WebsocketDemultiplexer):
    http_user = True

    def connect(self, message, **kwargs):
        if not (test_pdsm(message.user) and (CastingMeta.objects.get(
                pk=kwargs["show"]).show.user_is_staff(message.user))):
            message.reply_channel.send({"close": True})
            return False
        super().connect(message, **kwargs)

class CallbackConsumer(ListConsumer):
    consumers = {
        "castingmeta": CastingMetaBinding.consumer,
        "character": CharacterBinding.consumer,
        "callback": CallbackBinding.consumer,
    }
    
    def connection_groups(self, **kwargs):
        return ["callbacks-show-{}".format(kwargs["show"])]

class CastListConsumer(ListConsumer):
    consumers = {
        "castingmeta": CastingMetaBinding.consumer,
        "character": CharacterBinding.consumer,
        "signing": SigningBinding.consumer,
    }
    
    def connection_groups(self, **kwargs):
        return ["cast-show-{}".format(kwargs["show"])]
