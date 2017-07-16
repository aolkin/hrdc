
from .consumers import *

channel_routing = [
    ShowConsumer.as_route(path=r'^staff/auditions/(?P<show>\d+)/ws/$'),
    TablingConsumer.as_route(path=r'^staff/building/(?P<building>\d+)/ws/$'),
    CallbackConsumer.as_route(path=r'^staff/callbacks/(?P<show>\d+)/ws/$'),
]
