from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse, resolve
from django.urls.exceptions import NoReverseMatch
from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator 

from django import forms
from django.views.generic.edit import FormView, UpdateView
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from .utils import user_is_initialized
from .email import send_reset
from .models import User

all_indexes = []
admin_indexes = [
    (reverse_lazy("admin:index"), "Site Admin",
     "edit objects, invite users, etc."),
]

@login_required
@user_is_initialized
def index(request):
    if not all_indexes:
        for i in settings.INSTALLED_APPS:
            try:
                u = reverse(i+":index")
                r = resolve(u)
                if r.func != index:
                    name = r.func.verbose_name if hasattr(
                        r.func, "verbose_name") else r.view_name
                    all_indexes.append((u, name,
                                        getattr(r.func, "help_text", "")))
            except NoReverseMatch:
                pass
            try:
                u = reverse(i+":admin")
                r = resolve(u)
                name = r.func.verbose_name if hasattr(
                    r.func, "verbose_name") else r.view_name
                admin_indexes.append((u, name,
                                      getattr(r.func, "help_text", "")))
            except NoReverseMatch:
                pass
    context = { "indexes": all_indexes, "admin_indexes": admin_indexes }
    return render(request, "dramaorg/index.html", context)

# These variables are set here only for documentation purposes
index.verbose_name = "This Page!"
index.help_text = "List of your shows"

SESSION_TOKEN_KEY = "_CAPTURED_LOGIN_TOKEN"

def capture_token(request, token):
    request.session[SESSION_TOKEN_KEY] = token
    return HttpResponseRedirect(reverse("dramaorg:password_token"))

class TokenView(FormView):
    form_class = SetPasswordForm
    success_url = reverse_lazy('dramaorg:index')
    template_name = "dramaauth/set_password.html"
    
    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        try:
            t = self.request.session[SESSION_TOKEN_KEY]
            self.user = get_user_model().objects.get(login_token=t)
            if (self.user.is_initialized and
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
        login(self.request, user)
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

class ResetView(FormView):
    form_class = PasswordResetForm
    success_url = reverse_lazy("dramaorg:login")
    template_name = "dramaauth/reset_password_form.html"

    def form_valid(self, form):
        form.send()
        messages.success(self.request, "Password reset email sent.")
        return super().form_valid(form)

class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    fields = ['first_name', 'last_name', 'pgps', 'phone', 'email']
    template_name = "dramaauth/user_profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return self.request.GET.get("next", reverse("dramaorg:index"))
