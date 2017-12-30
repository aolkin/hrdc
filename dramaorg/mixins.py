from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages

from .utils import test_initialized

class InitializedMixin(UserPassesTestMixin):
    login_url = "dramaorg:profile"
    def test_func(self):
        return test_initialized(self.request.user)
