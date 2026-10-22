import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrdc.settings")

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter
from .routing import websocket_application

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": websocket_application,
})
