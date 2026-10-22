from channels.routing import URLRouter
from django.urls import path

from .consumers import *

urlpatterns = [
    path("staff/", URLRouter([
        path("building/<int:building>/ws/", TablingConsumer.as_asgi()),
        path("show/<int:show>/", URLRouter([
            path("auditions/ws/", ShowConsumer.as_asgi()),
            path("callbacks/ws/", CallbackConsumer.as_asgi()),
            path("cast/ws/", CastListConsumer.as_asgi()),
        ])),
    ])),
]
