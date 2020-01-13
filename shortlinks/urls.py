
from django.urls import path

from .views import *

app_name = "shortlinks"
urlpatterns = [
    path('', LinksView.as_view(), name="index"),
]
