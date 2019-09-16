from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse, resolve
from django.urls.exceptions import NoReverseMatch
from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator 

from django import forms
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView, UpdateView
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin

from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .utils import user_is_initialized
from .email import send_reset, activate
from .models import *

from config import config
import time

indexes = {
    "staff_indexes": [],
    "admin_indexes": [
        (reverse_lazy("admin:index"), "Site Management",
         "administer shows, users, etc."),
    ],
    "public_indexes": []
}

def get_link(u):
    r = resolve(u)
    func = r.func.view_class if hasattr(r.func, "view_class") else r.func
    name = func.verbose_name if hasattr(func, "verbose_name") else r.view_name
    return (u, name, getattr(func, "help_text", ""))

def load_indexes():
    for i in settings.INSTALLED_APPS:
        try:
            u = reverse(i+":index")
            indexes["staff_indexes"].append(get_link(u))
        except NoReverseMatch:
            pass
        try:
            u = reverse(i+":admin")
            indexes["admin_indexes"].append(get_link(u))
        except NoReverseMatch:
            pass
        try:
            u = reverse(i+":public_index")
            indexes["public_indexes"].append(get_link(u))
        except NoReverseMatch:
            pass

class SeasonForm(forms.ModelForm):
    class Meta:
        model = Season
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        if not kwargs["initial"]:
            kwargs["initial"] = {
                "year": config.get(settings.ACTIVE_YEAR_KEY, None),
                "season": config.get(settings.ACTIVE_SEASON_KEY, None)
            }
        super().__init__(*args, **kwargs)
        
    def save(self, *args):
        config[settings.ACTIVE_SEASON_KEY] = self.cleaned_data["season"]
        config[settings.ACTIVE_YEAR_KEY] = self.cleaned_data["year"]
                        
class StaffIndexView(SuccessMessageMixin, FormView):
    verbose_name = "Your Shows"
    help_text = "view and manage your shows"

    template_name = "dramaorg/index.html"
    success_url = reverse_lazy("dramaorg:index")
    form_class = SeasonForm

    def get_success_message(self, data):
        return "Season updated successfully."
    
    @method_decorator(login_required)
    @method_decorator(user_is_initialized)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, *args, **kwargs):
        if self.request.user.is_superuser:
            return super().post(*args, **kwargs)
        else:
            messages.error(self.request,
                           "Illegal operation: cannot set current season")
            return super().get(*args, **kwargs)
        
    def form_valid(self, form):
        if self.request.user.is_superuser:
            form.save()
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(indexes)
        return context

class HomePage(TemplateView):
    template_name = "dramaorg/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(indexes)
        return context
    
SESSION_TOKEN_KEY = "_CAPTURED_LOGIN_TOKEN"

def capture_token(request, token):
    request.session[SESSION_TOKEN_KEY] = token
    return HttpResponseRedirect(reverse("dramaorg:password_token"))

class TokenView(FormView):
    form_class = SetPasswordForm
    template_name = "dramaauth/set_password.html"

    def get_success_url(self):
        if self.request.user.post_register:
            url = reverse("dramaorg:profile") + "?next={}".format(
                self.request.user.post_register)
            self.request.user.post_register = ""
        else:
            url = reverse("dramaorg:home")
        return url
            
    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        try:
            t = self.request.session[SESSION_TOKEN_KEY]
            self.user = get_user_model().objects.get(login_token=t)
            if (self.user.has_usable_password() and
                self.user.token_expiry < timezone.now()):
                self.user = None
        except (TypeError, KeyError, ValueError, OverflowError,
                get_user_model().DoesNotExist):
            self.user = None
        
        if self.user is not None:
            return super().dispatch(*args, **kwargs)
        else:
            self.delete_captured_token()
            return self.render_to_response(self.get_context_data(valid=False))
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def delete_captured_token(self):
        if self.request.session.exists(SESSION_TOKEN_KEY):
            self.request.session.delete(SESSION_TOKEN_KEY)
    
    def form_valid(self, form):
        user = form.save()
        self.delete_captured_token()
        login(self.request, user,
              backend="django.contrib.auth.backends.ModelBackend")
        return super().form_valid(form)
        
    def get_context_data(self, valid=True, **kwargs):
        context = super().get_context_data(**kwargs)
        if not valid:
            context.update({
                'form': None,
                'title': 'Password reset unsuccessful',
            })
        return context

class PasswordResetForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

    def send(self):
        users = get_user_model().objects.filter(**{
            '%s__iexact' % get_user_model().get_email_field_name():
            self.cleaned_data["email"],
            'is_active': True,
        })
        for user in users:
            user.new_token(expiring=True)
            send_reset(user)
            return True
        return False

class ResetView(FormView):
    form_class = PasswordResetForm
    success_url = reverse_lazy("dramaorg:login")
    template_name = "dramaauth/reset_password_form.html"

    def form_valid(self, form):
        if form.send():
            messages.success(self.request, "Password reset email sent.")
            return super().form_valid(form)
        else:
            messages.error(self.request, "Unable to find an account with " +
                           "that email, please contact the administrator.")
            return super().form_invalid(form)

class UserRegistrationForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)

class RegisterView(FormView):
    form_class = UserRegistrationForm
    template_name = "dramaauth/create_account.html"

    def get_success_url(self):
        return reverse("dramaorg:register") + "?post={}&from={}".format(
            self.request.GET.get("post",""), self.request.GET.get("from",""))
    
    def form_valid(self, form):
        users = get_user_model().objects.filter(**{
            '%s__iexact' % get_user_model().get_email_field_name():
            form.cleaned_data["email"],
        })
        if len(users) > 1:
            messages.error(self.request, "Multiple users found with this " +
                           "email address. Please contact support.")
            return super().form_invalid(form)
        if users:
            user = users[0]
            if user.password:
                messages.error(self.request, "A user with this email already " +
                               "exists. Please log in instead.")
                return super().form_invalid(form)
        else:
            user = get_user_model()(email=form.cleaned_data["email"])
        user.post_register = self.request.GET.get("post","")
        user.source = "registration"
        user.new_token(save=False, expiring=True)
        user.save()
        activate(user, time.time() if users else "")
        messages.info(self.request, "Check for an email from {} to ".format(
            settings.DEFAULT_FROM_EMAIL) +
                      "complete the sign up process.")
        return super().form_valid(form)
                                                    
class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'pgps', 'gender_pref', 'phone',
              'affiliation', 'year', 'email']
    template_name = "dramaauth/user_profile.html"

    def get(self, *args, **kwargs):
        if self.request.GET.get("next", None):
            messages.add_message(
                self.request, messages.WARNING,
                "Please fill out your missing profile information.")
        return super().get(*args, **kwargs)
    
    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return self.request.GET.get("next", reverse("dramaorg:home"))
