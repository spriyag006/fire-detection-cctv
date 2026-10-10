import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "firewatch.settings")

django_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path

from core.consumers import AlertConsumer


application = ProtocolTypeRouter({
    "http": django_app,

    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/alerts/", AlertConsumer.as_asgi()),
        ])
    ),
})