from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from channels.generic.websockets import JsonWebsocketConsumer

from django.conf import settings
from django.utils import timezone

class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True,
                             on_delete=models.SET_NULL)
    nickname = models.CharField(max_length=30)

    room = models.CharField(max_length=32, db_index=True)
    message = models.TextField()

    timestamp = models.DateTimeField(auto_now_add=True)
    
    def set_user(self, obj):
        self.user = obj
        self.nickname = self.user.get_full_name()

    def __str__(self):
        return "{} to {}".format(self.nickname, self.room)

    @classmethod
    def create(cls, user, room, msg):
        obj = cls(room = room, message = msg)
        obj.set_user(user)
        obj.save()
        return obj

@receiver(post_save)
def send_message(sender, instance, created, raw, **kwargs):
    if sender == Message and created:
        JsonWebsocketConsumer.group_send("chat-{}".format(instance.room), {
            "container": "#chat",
            "element": "<li>",
            "id": "chat-msg-{}".format(instance.pk),
            "scroll": "#chat-window .card-body",
            "html": render_to_string("casting/pieces/chat_msg.html", {
                "chat" : instance
            }),
            "pulse": "bg-dark text-light",
            "pulse_el": "#chat-window .card-header",
        })
