from django.utils import timezone

from hrdc.websockets import DemultiplexConsumer, GroupConsumer

from ..utils import test_pdsm, test_board
from ..models import CastingMeta
from ..views import get_active_slot

from .bindings import *

from chat.models import Message


class ChatConsumer(GroupConsumer):
    def get_building(self):
        return self.url_kwargs["building"]

    def get_name(self):
        return "building-{}-{}".format(self.get_building(),
                                       timezone.localdate())

    def connection_groups(self):
        return ["chat-" + self.get_name()]

    def receive_json(self, content, **kwargs):
        Message.create(self.user, self.get_name(), content["msg"])


class TablingConsumer(ChatConsumer):
    def has_access(self):
        return test_pdsm(self.user) or test_board(self.user)

    def connection_groups(self):
        return (super().connection_groups() +
                ["auditions-building-{}".format(self.get_building())])


def user_is_show_staff(user, show):
    return test_pdsm(user) and CastingMeta.objects.get(
        pk=show).show.user_is_staff(user)


class ShowConsumer(ChatConsumer):
    def get_building(self):
        active_slot = get_active_slot(self.url_kwargs["show"])
        return active_slot.space.building.pk if active_slot else 0

    def has_access(self):
        return user_is_show_staff(self.user, self.url_kwargs["show"])

    def connection_groups(self):
        return (super().connection_groups() +
                ["auditions-show-{}".format(self.url_kwargs["show"])])


class ListConsumer(DemultiplexConsumer):
    def has_access(self):
        return user_is_show_staff(self.user, self.url_kwargs["show"])


class CallbackConsumer(ListConsumer):
    bindings = {
        "castingmeta": CastingMetaBinding,
        "character": CharacterBinding,
        "callback": CallbackBinding,
    }

    def connection_groups(self):
        return ["callbacks-show-{}".format(self.url_kwargs["show"])]


class CastListConsumer(ListConsumer):
    bindings = {
        "castingmeta": CastingMetaBinding,
        "character": CharacterBinding,
        "signing": SigningBinding,
    }

    def connection_groups(self):
        return ["cast-show-{}".format(self.url_kwargs["show"])]
