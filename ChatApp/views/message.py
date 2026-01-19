from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, Conversations, Conversations_Users ,Message
from ..middleware.auth import require_token

class sendMessageAPI(APIView):
  @require_token
  def post(self, request):
    try:
      user = request.auth_user

      conversation_id = request.data.get('conversation_id')
      type = request.data.get('type', "")
      body = request.data.get('body', "")  # your payload uses 'body'
      media_url = request.data.get('media_url', "")
      message_status = request.data.get('status', "active")

      if not conversation_id:
          return Response(
              {'success': False, 'error': 'conversation_id is required'},
              status=status.HTTP_400_BAD_REQUEST
          )

      # Fetch the actual Conversations object
     
      conversation = Conversations.objects.get(id=conversation_id)
  
      # Create message
      message = Message.objects.create(
        type=type,
        body=body,
        status=message_status,
        media_url=media_url,
        sender_id=user,          # use sender_id, not sender
        conversation_id=conversation
      )

      return Response({
        'success': True,
        'message': 'Message sent successfully',
        'data': {
            'id': message.id,
            'body': message.body,
            'sender_id': user.id,
            'conversation_id': conversation.id,
            'created_at' : message.created_at
        }
      }, status=status.HTTP_201_CREATED)

    except Exception as e:
      return Response(
        {'success': False, 'error': str(e)},
        status=status.HTTP_400_BAD_REQUEST
      )

class getConversationMessages(APIView):
  @require_token
  def post(self, request):
    try:
      user = request.auth_user
      conversation_id = request.data.get('conversation_id')  # Use query_params for GET

      if not conversation_id:
        return Response({'success': False, 'error': 'conversation_id is required'},status=status.HTTP_400_BAD_REQUEST)

      conversation = Conversations.objects.get(id=conversation_id)
      messages = Message.objects.filter(conversation_id=conversation).order_by('created_at')

 
      messages_data = []
      for m in messages:
        
        senderdata =User.objects.get(id=m.sender_id.id)

        messages_data.append({
          'id': m.id,
          'type': m.type,
          'body': m.body,
          'media_url': m.media_url,
          # 'status': getattr(m, 'status', 'active'),
          'created_at': m.created_at,
          'updated_at': m.updated_at,
          'user_id' : user.id,
          'sender_id': m.sender_id.id,
          'conversation_id': m.conversation_id.id,
          'sender_first_name':senderdata.first_name,
          'sender_last_name':senderdata.last_name,
          'sender_profile':senderdata.profile,
          'sender_username':senderdata.username
        })
          
      return Response({
        'success': True,
        'message': 'Messages fetched successfully',
        'data': messages_data
      }, status=status.HTTP_200_OK)

    except Conversations.DoesNotExist:
      return Response({'success': False, 'error': 'Conversation not found'},status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
      return Response({'success': False, 'error': str(e)},status=status.HTTP_400_BAD_REQUEST)
