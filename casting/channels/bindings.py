from channels.binding.websockets import WebsocketBinding

from ..models import *

class CastingMetaBinding(WebsocketBinding):
    model = CastingMeta
    stream = "castingmeta"
    fields = ("contact_email", "callback_description", "cast_list_description")

    @classmethod
    def group_names(cls, instance):
        return ["callbacks-show-{}".format(instance.pk)]

    def has_permission(self, user, action, pk):
        return (action == "update" and
                self.model.objects.get(pk=pk).show.user_is_staff(user))
    
class CharacterBinding(WebsocketBinding):
    model = Character
    stream = "character"
    fields = ("name", "callback_description", "allowed_signers")

    @classmethod
    def group_names(cls, instance):
        return ["callbacks-show-{}".format(instance.show.pk)]

    def create(self, data):
        show = CastingMeta.objects.get(pk=data["show"])
        if show.show.user_is_staff(self.user):
            super().create(data)
    
    def has_permission(self, user, action, pk):
        if action == "create":
            return True
        if action == "update" or action == "delete":
            return self.model.objects.get(pk=pk).show.show.user_is_staff(user)
            
