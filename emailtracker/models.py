from django.db import models
from django.utils import timezone
from django.conf import settings

import pickle, logging
from traceback import print_exc
from tempfile import mkstemp
from os import fdopen, unlink, write
from anymail.message import UNSET as AM_UNSET

from .utils import *

EMAIL_TEMP_DIR = getattr(settings, "TEMP", None)
EMAIL_TEMP_DIR = getattr(settings, "QUEUED_EMAIL_TEMP", EMAIL_TEMP_DIR)

LOGGER = logging.getLogger("emailtracker.models")

class MissingEmailMessage(FileNotFoundError): pass

UNSET = "<ANYMAIL_OBJECT_UNSET>"

def prep_for_pickling(obj, allow_prep=True):
    for i in obj.__dict__:
        if obj.__dict__[i] == UNSET:
            obj.__dict__[i] = AM_UNSET
        elif obj.__dict__[i] == AM_UNSET and allow_prep:
            obj.__dict__[i] = UNSET

class QueuedEmail(models.Model):
    to = models.CharField(max_length=254)
    subject = models.CharField(max_length=255)

    msg = models.TextField()

    msg_id = models.CharField(max_length=80)
    status = models.CharField(max_length=20)
    
    name = models.CharField(max_length=20)
    ident = models.CharField(max_length=60)

    sent = models.DateTimeField(null=True)
    added = models.DateTimeField(auto_now_add=True)

    def set_msg(self, msg):
        fd, fn = mkstemp(".eml.pkl", "queued-", dir=EMAIL_TEMP_DIR)
        prep_for_pickling(msg)
        pickle.dump(msg, fdopen(fd, "wb"))
        prep_for_pickling(msg, False)
        self.msg = fn
        self.subject = msg.subject
        self.to = extract_address(msg.to[0])

    def get_msg(self):
        try:
            fd = open(self.msg, "rb")
        except FileNotFoundError:
            return None
        msg = pickle.load(fd)
        prep_for_pickling(msg, False)
        return msg

    def send(self, quiet=not settings.DEBUG):
        msg = self.get_msg()
        if not msg:
            self.status = "<Missing>"
            self.save()
            if quiet:
                LOGGER.error("Missing message {} file: {}".format(
                    self.pk, self.msg))
                return msg
            else:
                raise MissingEmailMessage(self.msg)
        if getattr(settings, "QUEUED_EMAIL_DEBUG", False):
            fd, fn = mkstemp(".eml.txt", "debug-",
                             dir=EMAIL_TEMP_DIR, text=True)
            write(fd, msg.body.encode())
            print("Email body written to: {}".format(fn))
            if len(msg.alternatives) > 0:
                fd, fn = mkstemp(".eml.html", prefix="debug-",
                                 dir=EMAIL_TEMP_DIR, text=True)
                write(fd, msg.alternatives[0][0].encode())
                print("Email HTML written to: {}".format(fn))
            self.status = "<DEBUG>"
        else:
            try:
                msg.send()
                self.status = ""
            except Exception as err:
                self.status = "<Failed>"
                if quiet:
                    LOGGER.warn("Message {} sending failed: {}".format(
                        self.pk, repr(err)))
                else:
                    print_exc()
        if not self.status:
            if hasattr(msg, "anymail_status"):
                self.msg_id = str(msg.anymail_status.message_id)
                if self.to in msg.anymail_status.recipients:
                    self.status = msg.anymail_status.recipients[self.to]
                else:
                    self.status = "<Unknown>"
            else:
                self.status = "<Not AnyMail>"
            unlink(self.msg)
        self.sent = timezone.now()
        self.save()
        return msg
        
    def __str__(self):
        return '<{} "{}" to {}>'.format("Sent" if self.sent else "Unsent",
                                        self.subject, self.to)
