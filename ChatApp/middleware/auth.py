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
    if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
      return None

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    token = auth_header.strip()

    request.auth_user = None 

    if token:
      try:
        user = User.objects.get(token=token)

        if user.id is not None:
          request.auth_user = user

      except User.DoesNotExist:
        pass

    return None

def require_token(view_func):
  @wraps(view_func)
  def wrapper(self, request, *args, **kwargs):

    if not hasattr(request, 'auth_user') or not request.auth_user:
      return Response(
        {'success': False, 'message': 'Unauthorized', 'data': None},
        status=status.HTTP_401_UNAUTHORIZED
      )

    return view_func(self, request, *args, **kwargs)

  return wrapper
