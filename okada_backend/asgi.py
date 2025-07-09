<<<<<<< HEAD
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



=======
"""
ASGI config for okada_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "okada_backend.settings")

application = get_asgi_application()
>>>>>>> refs/remotes/origin/main
