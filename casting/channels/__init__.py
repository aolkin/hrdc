from channels.routing import include

from .consumers import *

channel_routing = [
    include([
        TablingConsumer.as_route(path=r'^building/(?P<building>\d+)/ws/$'),
        include([
            ShowConsumer.as_route(path=r'^auditions/ws/$'),
            CallbackConsumer.as_route(path=r'^callbacks/ws/$'),
            CastListConsumer.as_route(path=r'^cast/ws/$'),
        ], path="^show/(?P<show>\d+)/"),
    ], path="^staff/"),
]
