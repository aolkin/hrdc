from django.shortcuts import render
from django.http import HttpResponse

from django.views import View

def index(request):
    return HttpResponse("")

class TokenView(View):
    create = False
    def get(self, request, token):
        return HttpResponse("")

class ResetView(View):
    def get(self, request):
        return HttpResponse("")

class CreateView(View):
    def get(self, request):
        return HttpResponse("")
