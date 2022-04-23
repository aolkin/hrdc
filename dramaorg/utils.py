from django.db.utils import OperationalError, ProgrammingError
from django.db.models import Q
from django.views.generic.detail import SingleObjectMixin
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout, login
from django.contrib import messages
from django.core.exceptions import PermissionDenied

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
    add_permissions(models,
                    Q(codename__contains="view") |
                    Q(codename__contains="delete"))

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

class InitializedLoginMixin:
    @method_decorator(login_required)
    @method_decorator(user_is_initialized)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class ShowStaffMixin(InitializedLoginMixin, SingleObjectMixin):
    test_silent = False

    def test_func(self):
        if super().test_func():
            if self.get_object().show.user_is_staff(self.request.user):
                return True
            else:
                if not self.test_silent:
                    messages.error(self.request, "You are not a member of the "
                                   "executive staff of that show. Log in as a "
                                   "different user?")
        return False

class UserStaffMixin:
    @method_decorator(login_required)
    @method_decorator(user_is_initialized)
    def dispatch(self, *args, **kwargs):
        if not self.request.user.show_set.filter(
                pk=self.get_object().show.pk).exists():
            raise PermissionDenied()
        return super().dispatch(*args, **kwargs)


def social_create_user(strategy, details, backend, request, user=None, *args, **kwargs):
    fields = {
        "email":  details.get("email"),
        "source": "social"
    }

    User = import_module("django.contrib.auth").get_user_model()
    qs = User.objects.filter(email__iexact=fields["email"])

    is_new = not qs.exists()

    if user and user.email != details.get("email"):
        logout(request)
        if qs.exists():
            user = qs.first()
        else:
            user = None

    if user is None:
        user = strategy.create_user(**fields)
        is_new = True

    login(request, user, backend=settings.AUTHENTICATION_BACKENDS[-1])

    return {
        'is_new': is_new,
        'user': user
    }
