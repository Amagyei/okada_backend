# okada_backend/asgi.py
import os

# Ensure the settings module is set **before** Django import/setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "okada_backend.settings")

import django
django.setup()

from django.core.asgi import get_asgi_application

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notifications.routing import websocket_urlpatterns
from okada_backend.jwt_middleware import JWTAuthMiddleware

django_asgi_app = get_asgi_application()

# Create the base ASGI app
base_asgi_app = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

application = JWTAuthMiddleware(base_asgi_app)
