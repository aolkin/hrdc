
from django.contrib.auth.mixins import UserPassesTestMixin

import contextlib

def test_board(user):
    return user.is_authenticated and user.is_board

def test_pdsm(user):
    return user.is_authenticated and user.is_pdsm

class UserIsPdsmMixin(UserPassesTestMixin):
    def test_func(self):
        return test_pdsm(self.request.user) or test_board(self.request.user)

@contextlib.contextmanager
def suppress_autotime(model, fields):
    _original_values = {}
    for field in model._meta.local_fields:
        if field.name in fields:
            _original_values[field.name] = {
                'auto_now': field.auto_now,
                'auto_now_add': field.auto_now_add,
            }
            field.auto_now = False
            field.auto_now_add = False
    try:
        yield
    finally:
        for field in model._meta.local_fields:
            if field.name in fields:
                field.auto_now = _original_values[field.name]['auto_now']
                field.auto_now_add = _original_values[field.name]['auto_now_add']
