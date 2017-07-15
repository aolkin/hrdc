
from .consumers import *

channel_routing = [
    ShowConsumer.as_route(path=r'^staff/audition/(?P<show>\d+)/ws/$'),
    TablingConsumer.as_route(path=r'^staff/building/(?P<building>\d+)/ws/$'),
]
