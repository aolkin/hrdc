from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from .utils import test_initialized, user_is_initialized

class InitializedMixin(UserPassesTestMixin):
    login_url = "dramaorg:profile"
    def test_func(self):
        return test_initialized(self.request.user)

@method_decorator(login_required, name="dispatch")
class InitializedLoginMixin(UserPassesTestMixin):
    def test_func(self):
        return test_initialized(self.request.user)

def test_board(user):
    return user.is_authenticated and user.is_board

def test_pdsm(user):
    return user.is_authenticated and user.is_pdsm

def test_spdsm(user):
    return user.is_authenticated and user.is_season_pdsm

class UserIsPdsmMixin(UserPassesTestMixin):
    def test_func(self):
        return test_pdsm(self.request.user) or test_board(self.request.user)

    def get_permission_denied_message(self):
        return "You are not a member of the executive staff of any shows."

class UserIsSeasonPdsmMixin(UserPassesTestMixin):
    def test_func(self):
        return test_spdsm(self.request.user) or test_board(self.request.user)

    def get_permission_denied_message(self):
        return "You are not a member of the executive staff of any shows this season."
