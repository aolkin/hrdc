from channels.routing import URLRouter
from django.urls import path

from .consumers import *

urlpatterns = [
    path("show/<int:show>/", URLRouter([
        path("budget/ws/", BudgetConsumer.as_asgi()),
    ])),
]
