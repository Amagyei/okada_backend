# jwt_middleware.py
import jwt
from django.conf import settings
from django.db import close_old_connections
from channels.db import database_sync_to_async

class JWTAuthMiddleware:
    """
    Custom JWT middleware that authenticates WebSocket connections.
    Expects the token in the query parameter `token`.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()
        
        # Import Django models and JWT components inside the method to avoid AppRegistryNotReady
        from django.contrib.auth.models import AnonymousUser
        from django.contrib.auth import get_user_model
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        
        scope['user'] = AnonymousUser()

        # Extract token from query string
        query_string = scope.get('query_string', b'').decode()
        token = None
        for part in query_string.split('&'):
            if part.startswith('token='):
                token = part.split('token=')[1]
                break

        if token is None:
            return await self.inner(scope, receive, send)

        try:
            # Validate the token
            UntypedToken(token)

            # Decode token to extract user ID
            decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_data.get('user_id')

            # Fetch user instance
            User = get_user_model()
            
            # Use database_sync_to_async for the database operation
            @database_sync_to_async
            def get_user_by_id(user_id):
                return User.objects.get(id=user_id)
            
            scope['user'] = await get_user_by_id(user_id)

        except Exception:
            # If any error occurs, user remains anonymous
            pass

        return await self.inner(scope, receive, send)

