from django.shortcuts import render

from config import config

def index(request):
    return render(request, "bt/default.html")
index.verbose_name = "Common Casting"
index.help_text = "audition actors and cast your shows"

def admin(request):
    return render(request, "bt/default.html")
admin.verbose_name = "Common Casting"
admin.help_text = "administer Common Casting"
