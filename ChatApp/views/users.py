from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.hashers import check_password , make_password

from ChatApp import settings
from ..models import User
import hashlib
import base64
import os
import re
from django.core.files import File

def save_base64_image(base64_data, filename):
   
    # Remove header if present (data:image/jpeg;base64,...)
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]

    img_data = base64.b64decode(base64_data)
    # print("Decoded image data:", img_data)  
    folder_path = os.path.join(settings.MEDIA_ROOT, 'profiles')
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, filename)
    with open(file_path, 'wb') as f:
        f.write(img_data)
    return f'profiles/{filename}'


class signupAPI(APIView):
  def post(self, request):
    response_data = {
      'success': False,
      'message': '',
      'data': None
    }
    http_status = status.HTTP_400_BAD_REQUEST
    
    try:
      username = request.data.get('username')
      email = request.data.get('email')
      first_name = request.data.get('first_name', '')
      last_name = request.data.get('last_name', '')
      password = request.data.get('password')
      profile = request.data.get('profile')
      
      # Validate required fields
      if not username or not password or not email:
        response_data['message'] = 'username, password, and email are required'
        return Response(response_data, status=http_status)
        
      #username validation
      if User.objects.filter(username=username).exists():
        response_data['message'] = 'Username already exists'
        return Response(response_data, status=http_status)
      
      valid_username, message = Validations().isvalidusername(username)
      if not valid_username:
        response_data['message'] = message
        return Response(response_data, status=http_status)

      #email validation
      result = validate_email(email)
      if result is not None:
        response_data['message'] = 'Invalid email format'
        return Response(response_data, status=http_status)
      elif User.objects.filter(email=email).exists():
        response_data['message'] = 'Email already exists'
        return Response(response_data, status=http_status)
      
      #first name and last name validation
      if first_name:
        valid_firstname, message = Validations().isvalidName(first_name)
        if not valid_firstname:
          response_data['message'] = 'Invalid first name: ' + message
          return Response(response_data, status=http_status)
      if last_name:
        valid_lastname, message = Validations().isvalidName(last_name)
        if not valid_lastname:
          response_data['message'] = 'Invalid last name: ' + message
          return Response(response_data, status=http_status)
      
      user = User.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=make_password(password),
        profile=profile
      )
      
      response_data['success'] = True
      response_data['message'] = 'User registered successfully'
      response_data['data'] = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'created_at': user.created_at.isoformat(),
        'updated_at': user.updated_at.isoformat()
      }
      http_status = status.HTTP_201_CREATED
      
    except Exception as e:
      response_data['message'] = str(e)
      http_status = status.HTTP_400_BAD_REQUEST
    
    return Response(response_data, status=http_status)


class loginAPI(APIView):
  def post(self, request):
    response_data = {
      'success': False,
      'message': '',
      'data': None
    }
    http_status = status.HTTP_400_BAD_REQUEST

    try:
      username = request.data.get('username')
      email = request.data.get('email')
      password = request.data.get('password')

      if not password or (not username and not email):
        response_data['message'] = 'Provide username or email and password'
        return Response(response_data, status=http_status)

      user = None
      if username:
        user = User.objects.filter(username=username).first()
      elif email:
        user = User.objects.filter(email=email).first()

      if not user:
        response_data['message'] = 'Invalid username or email'
        return Response(response_data, status=http_status)

      if not check_password(password, user.password):
        response_data['message'] = 'Invalid password'
        return Response(response_data, status=http_status)

      raw_string = f"{user.id}{user.username}"
      token = hashlib.sha256(raw_string.encode()).hexdigest()

      if token:
        result = self.add_token_intodb(user.id, token)
        if result:
          response_data['success'] = True
          response_data['message'] = 'Login successful'
          response_data['data'] = {
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
          http_status = status.HTTP_200_OK
        else:
          response_data['message'] = 'Failed to update token in database'
          return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      else:
        response_data['message'] = 'Token generation failed'
        http_status = status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as e:
      response_data['message'] = str(e)
      http_status = status.HTTP_400_BAD_REQUEST

    return Response(response_data, status=http_status)

  def add_token_intodb(self, id, token):
      user = User.objects.filter(id=id).first()
      if user:
          user.token = token
          user.save()
          return True
      return False


class getbyIdApi(APIView):
  def get(self, request, id=None):
    response_data = {
      'success': True,
      'message': '',
      'data': None
    }
    http_status = status.HTTP_400_BAD_REQUEST
    try:
      if id:
        try:
          user = User.objects.get(id=id)
          response_data['success'] = True
          response_data['message'] = 'User fetched successfully'
          response_data['data']= {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile': user.profile,
            'token': user.token,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
          }
          return Response(response_data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
          response_data['success'] = False
          response_data['message'] = 'User not found'
          return Response(response_data, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
      return Response(
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )
    

class updateAPI(APIView):
  def put(self, request, id=None):
    response_data = {
    'success': False,
    'message': '',
    'data': None
    }

    try:
      user = User.objects.get(id=id)
    except User.DoesNotExist:
      response_data['message'] = 'User not found'
      return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    profile_path = user.profile
    if 'profile' in request.data:
      profile_data = request.data.get('profile')
      b64_string = profile_data 
      filename = f"user_{id}_profile.jpg"
      img_data = base64.b64decode(b64_string)
      # print("Decoded image data:", img_data)  # For debugging purposes
      profile_path = save_base64_image(b64_string, filename)
      # print("Profile path:", profile_path)  # For debugging purposes

    #username validation
    username = request.data.get('username', user.username)
    if User.objects.filter(username=username).exclude(id=id).exists():
      response_data['message'] = 'Username already exists'
      return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    valid_username, message = Validations().isvalidusername(username)
    if not valid_username:
      response_data['message'] = message
      return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    #email validation
    if 'email' in request.data:
      user_email = request.data.get('email', user.email)
      try:
        validate_email(user_email)
        email = user_email 
      except ValidationError:
        response_data['message'] = 'Invalid email format'
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

      if User.objects.filter(email=email).exclude(id=id).exists():
        response_data['message'] = 'Email already exists'
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    #first name and last name validation
    if 'first_name' in request.data:
      first_name = request.data.get('first_name', user.first_name)
      valid_firstname, message = Validations().isvalidName(first_name)
      if not valid_firstname:
        response_data['message'] = 'Invalid first name: ' + message
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    if 'last_name' in request.data:
      last_name = request.data.get('last_name', user.last_name)
      valid_lastname, message = Validations().isvalidName(last_name)
      if not valid_lastname:
        response_data['message'] = 'Invalid last name: ' + message
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
      
    #password update
    if ('password' in request.data):  
      password = request.data.get('password')
      user.password = make_password(password)

    try:
      user.username = username
      user.email = email
      user.first_name = request.data.get('first_name', user.first_name)
      user.last_name = request.data.get('last_name', user.last_name)
      user.password = user.password
      user.profile = profile_path
      user.updated_at = timezone.now()
      user.save()
    except IntegrityError:
      response_data['message'] = 'Username or Email already exists'
      return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    response_data['success'] = True
    response_data['message'] = 'User updated successfully'
    response_data['data'] = {
      'id': user.id,
      'username': user.username,
      'email': user.email,
      'first_name': user.first_name,
      'last_name': user.last_name,
      'profile': user.profile,
      'created_at': user.created_at.isoformat(),
      'updated_at': user.updated_at.isoformat()
    }

    return Response(response_data, status=status.HTTP_200_OK)


class Validations:
  def isvalidusername(self, username):
    message = ""

    if username[0].isdigit() or username[0] == "_":
      message = "Username cannot start with a number or underscore"
      return (False, message)
    
    if "@" in username:
      message = "Username cannot contain '@'"
      return (False, message)

    # if not re.match(r'^[A-Za-z0-9_-]+$', username):
    #   message = "Username can only contain letters, numbers, underscores, or hyphens"
    #   return (False, message)

    return (True, "Valid username")
    
  def isvalidName(name):
      message = ""
      if name[0].isdigit() or name[0] == "_":
        message = "Username cannot start with a number or underscore"
        return (False, message)
      
      return (True, "Valid name")