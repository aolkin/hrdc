from django.shortcuts import render
from django.http import HttpResponse

from django.views import View
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .utils import test_initialized, user_is_initialized

class InitializedMixin(UserPassesTestMixin):
    login_url = "dramaorg:create"
    def test_func(self):
        return test_initialized(self.request.user)
    
@user_is_initialized
def index(request):
    return render(request, "bt/default.html")

class TokenView(View):
    create = False
    def get(self, request, token):
        return HttpResponse("")

class ResetView(View):
    def get(self, request):
        return HttpResponse("")

class CreateView(LoginRequiredMixin, View):
    def get(self, request):
        return HttpResponse("")
