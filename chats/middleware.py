from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from ChatApp.models import User


@database_sync_to_async
def get_user(token):
    try:
        return User.objects.get(token=token)
    except User.DoesNotExist:
        return None


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        params = parse_qs(query_string)

        token = params.get("token", [None])[0]
        scope["user"] = await get_user(token) if token else None

        return await super().__call__(scope, receive, send)


# THIS IS IMPORTANT
def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(inner)
