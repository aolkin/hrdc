from django.db import models

import pickle

from .utils import *

class QueuedEmail(models.Model):
    to = models.CharField(max_length=254)
    subject = models.CharField(max_length=80)

    msg = models.BinaryField()

    msg_id = models.CharField(max_length=80)
    status = models.CharField(max_length=20)
    
    name = models.CharField(max_length=20)
    ident = models.CharField(max_length=60)

    sent = models.DateTimeField(null=True)
    added = models.DateTimeField(auto_now_add=True)

    def set_msg(self, msg):
        self.msg = pickle.dumps(msg)
        self.subject = msg.subject
        self.to = extract_address(msg.to[0])

    def get_msg(self):
        return pickle.loads(self.msg)
        
    def __str__(self):
        return '<{} "{}" to {}>'.format("Sent" if self.sent else "Unsent",
                                        self.subject, self.to)
