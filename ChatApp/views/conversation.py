from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, Conversations, Conversations_Users
from ..middleware.auth import require_token

class getConversationAPI(APIView):
  @require_token
  def post(self, request):
    try:
      user = request.auth_user
      my_id = str(user.id)
      other_user_id = str(request.data.get('user_id'))
      title = request.data.get('title', 'New Chat')

      if not other_user_id:
        return Response(
            {'success': False, 'message': 'user_id is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

      # Wrap IDs with commas for exact match
      search_my_id = f",{my_id},"
      search_other_id = f",{other_user_id},"

      # Query existing conversation containing BOTH IDs
      common_conversation = Conversations_Users.objects.filter(
          user_ids__icontains=search_my_id
      ).filter(
          user_ids__icontains=search_other_id
      ).values_list('conversation_id', flat=True).first()

      if common_conversation:
        return Response({
          'success': True,
          'message': 'Conversation already exists',
          'data': {'conversation_id': common_conversation}
        }, status=status.HTTP_200_OK)

      # Create new conversation
      conversation = Conversations.objects.create(
        title=title
      )

      # Store IDs as comma-separated string with leading/trailing commas
      all_user_ids = f",{my_id},{other_user_id},"

      Conversations_Users.objects.create(
          conversation_id=conversation,
          user_ids=all_user_ids
      )

      return Response({
          'success': True,
          'message': 'New conversation created',
          'data': {'conversation_id': conversation.id}
      }, status=status.HTTP_201_CREATED)

    except Exception as e:
      return Response(
          {'success': False, 'error': str(e)},
          status=status.HTTP_400_BAD_REQUEST
      )
    
class getAllConversationsAPI(APIView):
  @require_token
  def get(self, request):
    try:
      user = request.auth_user
      my_id = str(user.id)

      # Wrap IDs with commas for exact match
      search_my_id = f",{my_id},"

      conversations = Conversations_Users.objects.filter(
        user_ids__icontains=search_my_id
      )
      
      # Serialize to JSON-friendly format
      data = []
      for cu in conversations:
        data.append({
          'conversation_user_ids': cu.user_ids,
          'conversation_id': cu.conversation_id.id,
          'conversation_title': cu.conversation_id.title,
          'created_at': cu.created_at,
          'updated_at': cu.updated_at,
        })

      return Response({
        'success': True,
        'message': 'Conversations fetched',
        'data': data
      }, status=status.HTTP_200_OK)

    except Exception as e:
      return Response(
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )
