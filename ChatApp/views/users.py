from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from ChatApp import settings
from ..models import User
import hashlib
import base64
import os
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
      profile = request.data.get('profile')
      
      # Validate required fields
      if not username or not email:
        response_data['message'] = 'username and email are required'
        return Response(response_data, status=http_status)
        
      if User.objects.filter(username=username).exists():
        response_data['message'] = 'Username already exists'
        return Response(response_data, status=http_status)
        
      if User.objects.filter(email=email).exists():
        response_data['message'] = 'Email already exists'
        return Response(response_data, status=http_status)
      
      # Create user with current timestamp
      user = User.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
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

      if not username or not email:
        response_data['message'] = 'username and email are required'
        return Response(response_data, status=http_status)
        
      try:
        user = User.objects.get(username=username)  
      except User.DoesNotExist:
        response_data['message'] = 'Invalid username or email'
        return Response(response_data, status=http_status)

      if user.email != email:
        response_data['message'] = 'Invalid username or email'
        return Response(response_data, status=http_status)
      
      # Generate token
      raw_string = f"{user.id}{user.username}"
      token = hashlib.sha256(raw_string.encode()).hexdigest()
      
      if(token):
         # Add token to database
        result= self.add_token_intodb(user.id, token)

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
    if User.objects.filter(id=id).exists():
        user = User.objects.get(id=id)
        user.token = token
        user.save()
        return True
    else:
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
  def put(self, request, id=None, headers=None):
    response_data = {
      'success': False,
      'message': '',
      'data': None
    }
    http_status = status.HTTP_400_BAD_REQUEST
    try:
      if headers:
        print("Headers:", headers)  

      if id:
        try:         
          user = User.objects.get(id=id)
          if('profile' in request.data):
            profile_data = request.data.get('profile')
            b64_string = profile_data 
            filename = f"user_{id}_profile.jpg"
            img_data = base64.b64decode(b64_string)
            # print("Decoded image data:", img_data)  # For debugging purposes
            profile_path = save_base64_image(b64_string, filename)
            # print("Profile path:", profile_path)  # For debugging purposes
          else:
            filename = user.profile if user.profile else ""

          user_name = request.data.get('username', user.username)

          if User.objects.filter(username=user_name).exclude(id=id).exists():
              response_data['message'] = 'Username already exists'
              return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
          else:
              user.username = user_name

          email = request.data.get('email', user.email)
          if User.objects.filter(email=email).exclude(id=id).exists():
              response_data['message'] = 'Email already exists'
              return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
          else:
              user.email = email

          user.first_name = request.data.get('first_name', user.first_name)
          user.last_name = request.data.get('last_name', user.last_name)
          user.profile = profile_path if 'profile' in request.data else user.profile
          user.updated_at = timezone.now()
          user.save()
          
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
          http_status = status.HTTP_200_OK
        except User.DoesNotExist:
          response_data['message'] = 'User not found'
          http_status = status.HTTP_404_NOT_FOUND
    except Exception as e:
      response_data['message'] = str(e)
      http_status = status.HTTP_400_BAD_REQUEST
    
    return Response(response_data, status=http_status)




