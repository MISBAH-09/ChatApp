from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from ChatApp.models import User

@database_sync_to_async
def get_user_from_token(token):
    try:
        return User.objects.get(token=token)
    except User.DoesNotExist:
        return None

class TokenAuthMiddleware(BaseMiddleware):
    """
    Custom token auth middleware for Django Channels.
    Checks token from query params or headers.
    """
    async def __call__(self, scope, receive, send):
        token = None

        # 1️⃣ Check query string first
        query_string = scope.get("query_string", b"").decode()
        if query_string:
            for param in query_string.split("&"):
                key, value = param.split("=")
                if key == "token":
                    token = value
                    break

        # 2️⃣ Optionally: check headers
        if not token:
            headers = dict(scope.get("headers", []))  # headers are list of tuples
            if b'sec-websocket-protocol' in headers:
                token = headers[b'sec-websocket-protocol'].decode()

        # Fetch user from DB
        scope['user'] = await get_user_from_token(token) if token else None

        return await super().__call__(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(inner)
