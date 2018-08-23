from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Q

from django.contrib.auth.decorators import user_passes_test

from importlib import import_module
from django.conf import settings

def get_admin_group():
    auth = import_module("django.contrib.auth.models")
    try:
        return auth.Group.objects.get_or_create(
            name=settings.ADMIN_GROUP_NAME)[0]
    except OperationalError:
        return None
    except ProgrammingError:
        return None

def add_view_permissions(*models):
    add_permissions(models, Q(codename__contains="view"))
    
def add_change_permissions(*models):
    add_permissions(models,
                    Q(codename__contains="add") |
                    Q(codename__contains="change"))
    
def add_all_permissions(*models):
    add_permissions(models,
                    Q(codename__contains="add") |
                    Q(codename__contains="delete") |
                    Q(codename__contains="change"))
    
def add_delete_permissions(*models):
    add_permissions(models, Q(codename__contains="delete"))
    
def add_permissions(models, q):
    group = get_admin_group()
    if group:
        Permission = import_module("django.contrib.auth.models").Permission
        cts = import_module("django.contrib.contenttypes.models")
        
        types = cts.ContentType.objects.get_for_models(*models)
        perms = Permission.objects.filter(q, content_type__in=types.values())
        group.permissions.add(*perms)
    
def test_initialized(user):
    return user.is_authenticated and user.is_initialized

def user_is_initialized(func):
    f  = user_passes_test(test_initialized, login_url="dramaorg:profile")
    return f(func)

