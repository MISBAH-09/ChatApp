from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import IntegrityError
from ChatApp import settings
from ..models import User , Conversations ,Conversations_Users
from ChatApp.middleware.auth import require_token
from django.core.files import File

from django.db import transaction

class getConversationAPI(APIView):
  @require_token
  def post(self, request):
    try:
      user = request.auth_user
      my_id = user.id

      other_user_id = request.data.get('user_id')
      title = request.data.get('title', 'New Chat')
      # print("amhereeee at backend", other_user_id)

      if not other_user_id:
          return Response(
              {'success': False, 'message': 'user_id is required'},
              status=status.HTTP_400_BAD_REQUEST
          )

      # does common conversation
      common_conversation = Conversations_Users.objects.filter(
          user_id=my_id,
          conversation_id__in=Conversations_Users.objects.filter(
              user_id=other_user_id
          ).values_list('conversation_id', flat=True)
      ).values_list('conversation_id', flat=True).first()

      # if yes 
      if common_conversation:
        return Response({
          'success': True,
          'message': 'Conversation already exists',
          'data': {
              'conversation_id': common_conversation
          }
        }, status=status.HTTP_200_OK)

      # new
      # with transaction.atomic():
      conversation = Conversations.objects.create(title=title)

      Conversations_Users.objects.create(
        conversation_id=conversation,
        user_id=user
      )

      Conversations_Users.objects.create(
        conversation_id=conversation,
        user_id=User.objects.get(id=other_user_id)
      )

      return Response({
        'success': True,
        'message': 'New conversation created',
        'data': {
            'conversation_id': conversation.id
        }
      }, status=status.HTTP_201_CREATED)

    except Exception as e:
      return Response(
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )
