from django.utils.deprecation import MiddlewareMixin
from ChatApp.models import User
from rest_framework.response import Response
from rest_framework import status
from functools import wraps


class AuthenticationMiddleware(MiddlewareMixin):

  EXEMPT_URLS = [
    '/signup',
    '/login',
    '/admin',
  ]
  
  def process_request(self, request):
    # Skip exempt URLs
    if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
      return None

    # Get Authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = None

    if auth_header.startswith('Bearer '):
      token = auth_header[7:].strip()
    elif auth_header:
      token = auth_header.strip()

    request.auth_user = None

    if token:
      try:
          user = User.objects.get(token=token)
          request.auth_user = user
      except User.DoesNotExist:
          pass

    return None


def require_token(view_func):
  @wraps(view_func)
  def wrapper(self, request, *args, **kwargs):
    if not getattr(request, 'auth_user', None):
      return Response(
        {'success': False, 'message': 'Unauthorized', 'data': None},
        status=status.HTTP_401_UNAUTHORIZED
      )
    return view_func(self, request, *args, **kwargs)
  return wrapper
