from channels.routing import include

from .consumers import *

channel_routing = [
    include([
        BudgetConsumer.as_route(path=r'^budget/ws/$'),
    ], path="^show/(?P<show>\d+)/"),
]
