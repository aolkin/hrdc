from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from django.urls import path

import casting.channels
import finance.channels

websocket_application = AuthMiddlewareStack(URLRouter([
    path("casting/", URLRouter(casting.channels.urlpatterns)),
    path("finance/", URLRouter(finance.channels.urlpatterns)),
]))
