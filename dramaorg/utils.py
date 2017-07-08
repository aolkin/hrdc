from django.db.utils import OperationalError
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

def test_initialized(user):
    return user.is_authenticated and user.is_initialized

def user_is_initialized(func):
    f  = user_passes_test(test_initialized, login_url="dramaorg:create")
    return f(func)

