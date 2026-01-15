from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import IntegrityError
from ChatApp import settings
from ..models import User , Conversations ,Conversations_Users
from ChatApp.middleware.auth import require_token
import hashlib
import base64
import os
import re
from django.core.files import File

class getConversationAPI(APIView):
  @require_token
  def post(self, request):
    try:
      user = request.auth_user
      my_id = user.id

      user_ids = request.data.get('user_ids')
      title =request.data.get('title')

      if not user_ids:
        return Response(
          {'success': False, 'message': 'At least select one person to start conversation'},
          status=status.HTTP_400_BAD_REQUEST
        )
      
      try:
        conversation =Conversations.objects.create(
        title=title,
        
        )
        conversation_id =conversation.id
        for user in user_ids:
          conversations_users=Conversations_Users.objects.create(
            conversation_id = conversation_id,
            user_id = user
          )
      except IntegrityError as e:
        pass

      




      response_data = {
        'success': True,
        'message': 'User IDs received',
        'data': {
          'my_id': my_id,
          'user_ids': user_ids
        }
      }

      return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
      return Response(
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )
