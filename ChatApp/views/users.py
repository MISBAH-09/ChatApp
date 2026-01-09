from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from ..models import User
import hashlib


class AuthenticationAPI(APIView):
      
  def post(self, request):
      
    request_path = request.path
    
    # signup request
    if 'signup' in request_path:
      return self._handle_signup(request)
    
    # login request
    elif 'login' in request_path:
      return self._handle_login(request)
    
    else:
      return Response(
        {'success': False, 'error': 'Invalid endpoint'},
        status=status.HTTP_400_BAD_REQUEST
      )
  
  def _handle_signup(self, request):
    try:
      username = request.data.get('username')
      email = request.data.get('email')
      first_name = request.data.get('first_name', '')
      last_name = request.data.get('last_name', '')
      profile = request.data.get('profile')
      
      # Validate required fields
      if not username or not email:
        return Response(
          {'success': False, 'error': 'username and email are required'},
          status=status.HTTP_400_BAD_REQUEST
        )
        
      if User.objects.filter(username=username).exists():
        return Response(
          {'success': False, 'error': 'Username already exists'},
          status=status.HTTP_400_BAD_REQUEST
        )
        
      if User.objects.filter(email=email).exists():
        return Response(
          {'success': False, 'error': 'Email already exists'},
          status=status.HTTP_400_BAD_REQUEST
        )
      
      # Create user with current timestamp
      user = User.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        profile=profile
      )
        
      return Response(
        {
          'success': True,
          'message': 'User registered successfully',
          'data': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
          }
        },
        status=status.HTTP_201_CREATED
      )
    except Exception as e:
      return Response(
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )
  
  def _handle_login(self, request):
    
    try:
      username = request.data.get('username')
      email = request.data.get('email')

      if not username or not email:
        return Response(
          # print ("Missing username or email:"),
          {'success': False, 'error': 'username and email are required'},
          status=status.HTTP_400_BAD_REQUEST
        )
        
      try:
        user = User.objects.get(username=username)
        # print("User found:", user.username)  
      except User.DoesNotExist:
        return Response(
          {'success': False, 'error': 'Invalid username or email'},
          status=status.HTTP_400_BAD_REQUEST
        )

      if user.email != email:
        return Response(
          # print ("Email does not match:"),
          {'success': False, 'error': 'Invalid username or email'},
          status=status.HTTP_400_BAD_REQUEST
        )
      
      raw_string = f"{user.id}{user.username}"
      token = hashlib.sha256(raw_string.encode()).hexdigest()
      # print("Generated token:", token)  
      if(token):
        print("Token generated successfully")
        self.add_token_intodb(user.id, token)
        return Response(
        {
          'success': True,
          'message': 'Login successful',
          'data': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile': user.profile,
            'token': token,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
          }
        },
        status=status.HTTP_200_OK
      )
      else:
        print("Token generation failed")
        return Response(
          {'success': False, 'error': 'Token generation failed'},
          status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

      
    except Exception as e:
      return Response(
          print ("Error during login:"),
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )


  def add_token_intodb(self, id, token):
    if User.objects.filter(id=id).exists():
        user = User.objects.get(id=id)
        user.token = token
        user.save()
        return True
    else:
      return False

  

