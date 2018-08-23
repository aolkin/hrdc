from channels.generic.websockets import (JsonWebsocketConsumer,
                                         WebsocketDemultiplexer)

from ..utils import test_pdsm, test_board
from ..models import CastingMeta
from ..views import get_active_slot

from .bindings import *

from django.utils import timezone

from chat.models import Message

class ChatConsumer(JsonWebsocketConsumer):
    http_user = True
    
    def get_name(self):
        return "building-{}-{}".format(self.kwargs["building"],
                                       timezone.localdate())
    
    def connection_groups(self, **kwargs):
        return ["chat-" + self.get_name()]
    
    def receive(self, content, **kwargs):
        Message.create(self.message.user, self.get_name(), content["msg"])
    
class TablingConsumer(ChatConsumer):
    http_user = True

    def connection_groups(self, **kwargs):
        return (super().connection_groups(**kwargs) +
                ["auditions-building-{}".format(kwargs["building"])])

    def connect(self, message, **kwargs):
        if not (test_pdsm(message.user) or test_board(message.user)):
            message.reply_channel.send({"close": True})
            return False
        super().connect(message, **kwargs)
        
class ShowConsumer(ChatConsumer):
    http_user = True

    def __init__(self, *args, **kwargs):
        active_slot = get_active_slot(kwargs["show"])
        pk = active_slot.space.building.pk if active_slot else 0
        kwargs.update({ "building": pk })
        super().__init__(*args, **kwargs)
    
    def connection_groups(self, **kwargs):
        return (super().connection_groups(**kwargs) +
                ["auditions-show-{}".format(kwargs["show"])])

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
