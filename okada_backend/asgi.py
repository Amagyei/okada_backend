# okada_backend/asgi.py
import os
import django
django.setup()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "okada_backend.settings")

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

# Wrap the entire ASGI app with JWT middleware
application = JWTAuthMiddleware(base_asgi_app)



