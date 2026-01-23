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
from ChatApp.middleware.auth import require_token
import hashlib
import base64
import os
import re
from django.core.files import File
from ChatApp.EmailEnqueue import EmailEnqueue
import os

class addbyemailAPI(APIView):
  def post(self, request):
    response_data = {'success': False, 'message': '', 'data': None}
    
    # Setup
    os.environ['EMAIL_QUEUE_PATH'] = 'D:/Internship/ChatApp/ChatApp/email_queue.pkl'
    email = request.data.get('email')
    password = request.data.get('password', 'Pakistan123@')
    
    # 1. EMAIL VALIDATION (No try needed)
    if not email:
        response_data['message'] = 'Email is required'
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # 2. DATABASE + QUEUE 
    try:
        # Create user
        user = User.objects.create(
            email=email,
            password=make_password(password),
        )
        print(f"User created: {email}")
        
        # Queue 
        enqueue_instance = EmailEnqueue()
        enqueue_instance.email_enqueue(email, password)
        print(f"Email queued for {email}")
        
    except IntegrityError as e:
        if '1062' in str(e):
            response_data['message'] = 'Email already exists'
            return Response(str(e), status=status.HTTP_409_CONFLICT)
        response_data['message'] = 'Database error'
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        response_data['message'] = 'Registration failed'
        return Response(e, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # SUCCESS 
    response_data['success'] = True
    response_data['data'] = {'email': user.email}
    response_data['message'] = 'User registered successfully'
    return Response(response_data, status=status.HTTP_201_CREATED)


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

      errors = []

      # Username validation
      if not username:
        errors.append('username is required')
      else:
        valid_username, message = Validations().isvalidusername(username)
        if not valid_username:
          errors.append(message)

      # Password validation
      if not password:
          errors.append('password is required')
      else:
        valid_password, message = Validations().isvalidPassword(password)
        if not valid_password:
          errors.append(message)

      # Email validation
      if not email:
          errors.append('email is required')
      else:
        try:
          validate_email(email) 
        except:
          errors.append('Invalid email format')
      if errors:
          response_data['message'] = ', '.join(errors)
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
        
      #password validation
      valid_password, message = Validations().isvalidPassword(password)
      if not valid_password:
        response_data['message'] = message
        return Response(response_data, status=http_status)
      
      try:
        user = User.objects.create(
          username=username,
          email=email,
          first_name=first_name,
          last_name=last_name,
          password=make_password(password),
          profile=profile
        )
      except IntegrityError as e:
        if '1062' in str(e):
          if 'username' in str(e):
            response_data['message'] = 'Username already exists'
          elif 'email' in str(e):
            response_data['message'] = 'Email already exists'
          else:
            response_data['message'] = 'Duplicate entry detected'
          return Response(response_data, status=http_status)
        else:
          response_data['message'] = str(e)
          return Response(response_data, status=http_status)

      
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
  @require_token
  def get(self, request, id=None):
    response_data = {
      'success': True,
      'message': '',
      'data': None
    }
    http_status = status.HTTP_400_BAD_REQUEST
    try:
      user = request.auth_user
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
    except Exception as e:
      return Response(
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )
    

class updateAPI(APIView):
  @require_token
  def put(self, request):
    response_data = {
      'success': False,
      'message': '',
      'data': None
    }
    user = getattr(request, 'auth_user', None)
    # print("Authenticated user:", user)  # For debugging purposes
    if not user:
      return Response(
        {'success': False, 'message': 'Unauthorized'},
        status=status.HTTP_401_UNAUTHORIZED
      )

    username = request.data.get('username', user.username)
    email = request.data.get('email', user.email)
    first_name = request.data.get('first_name', user.first_name)
    last_name = request.data.get('last_name', user.last_name)
    password = request.data.get('password', None)
    profile_path = user.profile

    # Handle profile image if provided
    if 'profile' in request.data:
      profile_data = request.data.get('profile')
      b64_string = profile_data 
      filename = f"user_{user.id}_profile.jpg"
      img_data = base64.b64decode(b64_string)
      # print("Decoded image data:", img_data)  # For debugging purposes
      profile_path = save_base64_image(b64_string, filename)
      # print("Profile path:", profile_path)  # For debugging purposes

    # Username validation
    if 'username' in request.data:
      valid_username, message = Validations().isvalidusername(username)
      if not valid_username:
        response_data['message'] = message
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Email validation
    if 'email' in request.data:
      try:
        validate_email(email)
      except ValidationError:
        response_data['message'] = 'Invalid email format'
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # First name validation
    if 'first_name' in request.data:
      valid_firstname, message = Validations().isvalidName(first_name)
      if not valid_firstname:
        response_data['message'] = 'Invalid first name: ' + message
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Last name validation
    if 'last_name' in request.data:
      valid_lastname, message = Validations().isvalidName(last_name)
      if not valid_lastname:
        response_data['message'] = 'Invalid last name: ' + message
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Password validation & hashing
    if password:
      valid_password, message = Validations().isvalidPassword(password)
      if not valid_password:
        response_data['message'] = message
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
      password = make_password(password)
    else:
      password = user.password  # keep old password if not updating

    # Save updates safely
    try:
      user.username = username
      user.email = email
      user.first_name = first_name
      user.last_name = last_name
      user.password = password
      user.profile = profile_path
      user.updated_at = timezone.now()
      user.save()
    except IntegrityError as e:
      if '1062' in str(e):
        if 'username' in str(e):
          response_data['message'] = 'Username already exists'
        elif 'email' in str(e):
          response_data['message'] = 'Email already exists'
        else:
          response_data['message'] = 'Duplicate entry detected'
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
      else:
        response_data['message'] = str(e)
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    # Return updated user data
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


class fetchallusersAPI(APIView):
  @require_token
  def get(self, request, id=None):
    response_data = {
      'success': True,
      'message': '',
      'data': None
    }
    http_status = status.HTTP_400_BAD_REQUEST
    try:
      user = request.auth_user
      
      users=User.objects.exclude(id=user.id)
      # print(users)

      users_list=[]

      for user in users:
        users_list.append({
          'id' : user.id,
          'username': user.username,
          'first_name' : user.first_name,
          'last_name' : user.last_name,
          'profile' : user.profile,
          'email' :user.email,
        })

      response_data['success']=True
      response_data ['message'] = "All users"
      response_data ['data'] = users_list

      return Response(response_data, status=status.HTTP_200_OK)
    except Exception as e:
      return Response(
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )
  


class Validations:
  def isvalidusername(self, username):
    message = ""

    # Check if the first character is a letter
    if not username[0].isalpha():
        message =  "Username must start with a letter not with '" + username[0] + "'"
        return (False, message)

    if not re.fullmatch(r'[A-Za-z0-9._]+', username):
        return False, "Username can only contain letters, numbers, '.' and '_'"
    
    if "@" in username:
      message = "Username cannot contain '@'"
      return (False, message)

    return (True, "Valid username")

  def isvalidName(self, name):
    message = ""
    if not name[0].isalpha():
        message = "Name must start with a letter"
        return (False, message)

    if not re.fullmatch(r"[A-Za-z' -]+", name):
        message = "Name can only contain letters, spaces, hyphens (-), and apostrophes (')"
        return (False, message)
    return (True, "Valid name")


  def isvalidPassword(self, password):
    message = ""
    if len(password) < 8:
      message = "Password must be at least 8 characters long"
      return (False, message)
    
    if not re.search(r'[A-Z]', password):
      message = "Password must contain at least one uppercase letter"
      return (False, message)
    
    if not re.search(r'[a-z]', password):
      message = "Password must contain at least one lowercase letter"
      return (False, message)
    
    if not re.search(r'[0-9]', password):
      message = "Password must contain at least one digit"
      return (False, message)
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
      message = "Password must contain at least one special character"
      return (False, message)

    return (True, "Valid password")