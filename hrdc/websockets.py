import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import JsonWebsocketConsumer
from channels.layers import get_channel_layer
from django.apps import apps
from django.core import serializers
from django.db.models.signals import (post_delete, post_save, pre_delete,
                                       pre_save)

CREATE = "create"
UPDATE = "update"
DELETE = "delete"


def group_send(group, content):
    layer = get_channel_layer()
    if layer is not None:
        async_to_sync(layer.group_send)(
            group, {"type": "send.content", "content": content})


class GroupConsumer(JsonWebsocketConsumer):
    """Joins the groups from connection_groups() after has_access() passes."""

    def has_access(self, **kwargs):
        return True

    def connection_groups(self, **kwargs):
        return []

    @property
    def user(self):
        return self.scope["user"]

    @property
    def url_kwargs(self):
        return self.scope["url_route"]["kwargs"]

    def connect(self):
        if not self.has_access(**self.url_kwargs):
            self.close()
            return
        self.joined_groups = self.connection_groups(**self.url_kwargs)
        for group in self.joined_groups:
            async_to_sync(self.channel_layer.group_add)(
                group, self.channel_name)
        self.accept()

    def disconnect(self, code):
        for group in getattr(self, "joined_groups", []):
            async_to_sync(self.channel_layer.group_discard)(
                group, self.channel_name)

    def send_content(self, event):
        self.send_json(event["content"])


class Binding:
    """
    Sends model changes to groups and applies permitted changes received
    from clients.
    """

    model = None
    stream = None
    fields = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.__dict__.get("model") is not None:
            cls.model_label = "{}.{}".format(
                cls.model._meta.app_label.lower(),
                cls.model._meta.object_name.lower())
            for signal, receiver in (
                    (pre_save, cls.pre_save_receiver),
                    (post_save, cls.post_save_receiver),
                    (pre_delete, cls.pre_delete_receiver),
                    (post_delete, cls.post_delete_receiver)):
                signal.connect(receiver, sender=cls.model)

    @classmethod
    def group_names(cls, instance):
        raise NotImplementedError()

    def has_permission(self, user, action, pk):
        raise NotImplementedError()

    @classmethod
    def pre_save_receiver(cls, instance, **kwargs):
        cls.pre_change_receiver(
            instance, CREATE if instance._state.adding else UPDATE)

    @classmethod
    def post_save_receiver(cls, instance, created, **kwargs):
        cls.post_change_receiver(instance, CREATE if created else UPDATE)

    @classmethod
    def pre_delete_receiver(cls, instance, **kwargs):
        cls.pre_change_receiver(instance, DELETE)

    @classmethod
    def post_delete_receiver(cls, instance, **kwargs):
        cls.post_change_receiver(instance, DELETE)

    @classmethod
    def pre_change_receiver(cls, instance, action):
        if not hasattr(instance, "_binding_group_names"):
            instance._binding_group_names = {}
        instance._binding_group_names[cls] = (
            set() if action == CREATE else set(cls.group_names(instance)))

    @classmethod
    def post_change_receiver(cls, instance, action):
        old_groups = instance._binding_group_names[cls]
        new_groups = (set() if action == DELETE
                      else set(cls.group_names(instance)))
        self = cls()
        self.send_messages(instance, old_groups - new_groups, DELETE)
        self.send_messages(instance, old_groups & new_groups, UPDATE)
        self.send_messages(instance, new_groups - old_groups, CREATE)

    def send_messages(self, instance, groups, action):
        if not groups:
            return
        content = {"stream": self.stream,
                   "payload": self.serialize(instance, action)}
        for group in groups:
            group_send(group, content)

    def serialize(self, instance, action):
        return {
            "action": action,
            "pk": instance.pk,
            "data": self.serialize_data(instance),
            "model": self.model_label,
        }

    def serialize_data(self, instance):
        data = serializers.serialize("json", [instance], fields=self.fields)
        return json.loads(data)[0]["fields"]

    @classmethod
    def handle(cls, user, payload):
        self = cls()
        self.user = user
        action = payload["action"]
        pk = payload.get("pk")
        data = payload.get("data")
        if not self.has_permission(user, action, pk):
            return
        if action == CREATE:
            self.create(data)
        elif action == UPDATE:
            self.update(pk, data)
        elif action == DELETE:
            self.delete(pk)
        else:
            raise ValueError("Bad action %r" % action)

    def _hydrate(self, pk, data):
        return list(serializers.deserialize("python", [{
            "pk": pk, "model": self.model_label, "fields": data}]))[0]

    def create(self, data):
        self._hydrate(None, data).save()

    def update(self, pk, data):
        instance = self.model.objects.get(pk=pk)
        hydrated = self._hydrate(pk, data)
        for name in data.keys():
            if name in self.fields:
                setattr(instance, name, getattr(hydrated.object, name))
        instance.save()

    def delete(self, pk):
        self.model.objects.filter(pk=pk).delete()


class DemultiplexConsumer(GroupConsumer):
    """Routes {"stream": ..., "payload": ...} messages to a binding."""

    bindings = {}

    def receive_json(self, content, **kwargs):
        binding = self.bindings.get(content.get("stream"))
        if binding:
            binding.handle(self.user, content["payload"])
