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

class AssociatedShowBinding(WebsocketBinding):
    model = None
    
    @classmethod
    def group_names(cls, instance):
        return ["callbacks-show-{}".format(instance.show.pk)]

    def has_permission(self, user, action, pk):
        if action == "create":
            return True
        if action == "update" or action == "delete":
            return self.model.objects.get(pk=pk).show.show.user_is_staff(user)

class CharacterBinding(AssociatedShowBinding):
    model = Character
    stream = "character"
    fields = ("name", "callback_description", "allowed_signers")

    def create(self, data):
        show = CastingMeta.objects.get(pk=data["show"])
        if show.show.user_is_staff(self.user):
            super().create(data)

    def delete(self, pk):
        if not self.model.objects.get(pk=pk).show.callbacks_submitted:
            super().delete(pk)
    
class CallbackBinding(AssociatedShowBinding):
    model = Callback
    stream = "callback"
    fields = ("actor", "character")

    def update(self, pk, data):
        if self.model.objects.get(pk=pk).character.show.callbacks_submitted:
            return False
        try:
            int(data["actor"])
            super().update(pk, data)
        except ValueError:
            print(pk, data)
            
    def create(self, data):
        show = Character.objects.get(pk=data["character"]).show
        if show.show.user_is_staff(self.user) and not show.callbacks_submitted:
            super().create(data)
