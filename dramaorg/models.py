from django.db import models
from django.contrib import auth
from django.conf import settings
from django.utils import text, timezone

from django.db.models.signals import post_save
from django.dispatch import receiver

import hashlib, base64, uuid

from . import get_admin_group
from . import email

class UserManager(auth.models.BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password):
        return self.create_user(email, password, is_superuser=True)

def generate_token():
    b = hashlib.blake2b(uuid.uuid4().bytes).digest()
    return base64.b64encode(b)[:-2].decode().replace("/","-")
    
class User(auth.models.AbstractBaseUser, auth.models.PermissionsMixin):
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"

    first_name = models.CharField(max_length=60)
    last_name = models.CharField(max_length=60)
    email = models.CharField(max_length=254, unique=True, db_index=True)
    phone = models.CharField(max_length=20)
    
    is_active = models.BooleanField(default=True)
    login_token = models.CharField(max_length=86, default=generate_token)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(default=timezone.now)
    
    objects = UserManager()

    def new_token(self):
        self.login_token = generate_token()
        self.save()
        return self.login_token

    def clear_token(self):
        self.login_token = ""
        self.save()
    
    @property
    def is_initialized(self):
        return bool(self.first_name and self.last_name and self.phone
                    and self.has_usable_password())

    @property
    def is_board(self):
        return self.groups.filter(id=get_admin_group().id).exists()
    
    @property
    def is_pdsm(self):
        return self.show_set.exists()
    
    @property
    def is_staff(self):
        return self.is_board or self.is_superuser
    
    def get_full_name(self):
        full_name = '{} {}'.format(self.first_name, self.last_name).strip()
        if full_name:
            return full_name
        else:
            return "<{}>".format(self.email)
    get_full_name.short_description = "Full Name"
    get_full_name.admin_order_field = "first_name"
    
    def get_short_name(self):
        return self.first_name.strip()

    __str__ = get_full_name

@receiver(post_save)
def invite_user(sender, instance, created, raw, **kwargs):
    if sender == User and created:
        email.send_invite(instance)
    
def _get_year():
    return timezone.now().year
    
class Show(models.Model):
    title = models.CharField(max_length=150)
    staff = models.ManyToManyField(settings.AUTH_USER_MODEL)
    
    SEASONS = (
        (0, "Winter"),
        (1, "Spring"),
        (2, "Summer"),
        (3, "Fall"),
    )
    year = models.PositiveSmallIntegerField(default=_get_year)
    season = models.PositiveSmallIntegerField(choices=SEASONS, default=3)
    
    slug = models.SlugField(unique=True, db_index=True)
    invisible = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def people(self):
        return ", ".join([i.get_full_name() for i in self.staff.all()])
