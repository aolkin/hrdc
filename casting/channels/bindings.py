from channels.binding.websockets import WebsocketBinding

from django.db.models import F

from ..models import *

class CastingMetaBinding(WebsocketBinding):
    model = CastingMeta
    stream = "castingmeta"
    fields = ("contact_email", "callback_description", "cast_list_description")

    @classmethod
    def group_names(cls, instance):
        return ["callbacks-show-{}".format(instance.pk),
                "cast-show-{}".format(instance.pk)]

    def has_permission(self, user, action, pk):
        return (action == "update" and
                self.model.objects.get(pk=pk).show.user_is_staff(user))

class AssociatedShowBinding(WebsocketBinding):
    model = None

    def has_permission(self, user, action, pk):
        if action == "create":
            return True
        if action == "update" or action == "delete":
            return self.model.objects.get(pk=pk).show.show.user_is_staff(user)

class CharacterBinding(AssociatedShowBinding):
    model = Character
    stream = "character"
    fields = ("name", "callback_description", "allowed_signers")

    @classmethod
    def group_names(cls, instance):
        groups = ["cast-show-{}".format(instance.show.pk)]
        if not instance.added_for_signing:
            groups.append("callbacks-show-{}".format(instance.show.pk))
        return groups
    
    def has_permission(self, user, action, pk):
        perm = super().has_permission(user, action, pk)
        if pk:
            obj = self.model.objects.get(pk=pk)
            if obj.show.callbacks_submitted:
                return perm and obj.added_for_signing
        return perm
            
    def create(self, data):
        show = CastingMeta.objects.get(pk=data["show"])
        if show.show.user_is_staff(self.user):
            if show.first_cast_submitted:
                return False
            if show.callbacks_submitted:
                data["added_for_signing"] = True
            super().create(data)

    def update(self, pk, data):
        obj = self.model.objects.get(pk=pk)
        if "allowed_signers" in data:
            if obj.show.first_cast_submitted:
                data["allowed_signers"] = obj.allowed_signers
        super().update(pk, data)

class CallbackBinding(AssociatedShowBinding):
    model = Callback
    stream = "callback"
    fields = ("actor", "character")

    @classmethod
    def group_names(cls, instance):
        return ["callbacks-show-{}".format(instance.show.pk)]
    
    def has_permission(self, user, action, pk):
        perm = super().has_permission(user, action, pk)
        if pk:
            return perm and not self.model.objects.get(
                pk=pk).character.show.callbacks_submitted
        return perm
            
    def create(self, data):
        show = Character.objects.get(pk=data["character"]).show
        if show.show.user_is_staff(self.user) and not show.callbacks_submitted:
            super().create(data)

class SigningBinding(AssociatedShowBinding):
    model = Signing
    stream = "signing"
    fields = ("actor", "character", "order")

    @classmethod
    def group_names(cls, instance):
        return ["cast-show-{}".format(instance.show.pk)]
    
    def has_permission(self, user, action, pk):
        perm = super().has_permission(user, action, pk)
        if pk:
            obj = self.model.objects.get(pk=pk)
            if obj.character.show.cast_submitted:
                return False
            if obj.character.show.first_cast_submitted:
                if obj.order < obj.character.allowed_signers:
                    return False
                if "order" in data and int(
                        data["order"]) < obj.character.allowed_signers:
                    return False
        return perm
    
    def update(self, pk, data):
        obj = self.model.objects.get(pk=pk)
        if "order" in data:
            order = int(data["order"])
            if (order >= len(self.model.objects.get(character=obj.character))
                or order < 0):
                data["order"] = obj.order
            else:
                old = self.model.objects.get(character=obj.character,
                                             order=order)
                old.order = obj.order
                old.save()
        super().update(pk, data)
            
    def create(self, data):
        show = Character.objects.get(pk=data["character"]).show
        if show.show.user_is_staff(self.user) and not show.cast_submitted:
            data["order"] = len(self.model.objects.filter(
                character_id=data["character"]))
            super().create(data)

    def delete(self, pk):
        obj = self.model.objects.get(pk=pk)
        shifts = self.model.objects.filter(character=obj.character,
                                           order__gt=obj.order)
        for signing in shifts:
            signing.order -= 1
            signing.save()
        super().delete(pk)
