from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, Conversations, Conversations_Users ,Message
from ..middleware.auth import require_token
from ChatApp import settings
import base64
import os

def save_base64_image(base64_data, filename):
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]

    img_data = base64.b64decode(base64_data)
    folder_path = os.path.join(settings.MEDIA_ROOT, 'ImgMessages')
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, filename)
    with open(file_path, 'wb') as f:
        f.write(img_data)

    return f'ImgMessages/{filename}'


def save_base64_audio(base64_data, filename):
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]

    audio_data = base64.b64decode(base64_data)
    folder_path = os.path.join(settings.MEDIA_ROOT, 'AudioMessages')
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, filename)
    with open(file_path, 'wb') as f:
        f.write(audio_data)

    return f'AudioMessages/{filename}'


class sendMessageAPI(APIView):
    @require_token
    def post(self, request):
        try:
            user = request.auth_user
            conversation_id = request.data.get('conversation_id')
            msg_type = request.data.get('type', "").lower()
            body = request.data.get('body', "")
            message_status = request.data.get('status', "active")
            base64_media = request.data.get('media')

            if not conversation_id:
                return Response(
                    {'success': False, 'error': 'conversation_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            conversation = Conversations.objects.get(id=conversation_id)

            # Create message first
            message = Message.objects.create(
                type=msg_type,
                body=body,
                status=message_status,
                sender_id=user,
                conversation_id=conversation
            )

            # Handle media
            if msg_type == "image" and base64_media:
                filename = f"user_{message.id}.jpg"
                image_path = save_base64_image(base64_media, filename)
                message.media_url = image_path
                message.save()

            elif msg_type == "audio" and base64_media:
                filename = f"user_{message.id}.webm"
                audio_path = save_base64_audio(base64_media, filename)
                message.media_url = audio_path
                message.save()

            return Response({
                'success': True,
                'message': 'Message sent successfully',
                'data': {
                    'id': message.id,
                    'type': message.type,
                    'body': message.body,
                    'media_url': message.media_url,
                    'sender_id': user.id,
                    'conversation_id': conversation.id,
                    'created_at': message.created_at
                }
            }, status=status.HTTP_201_CREATED)

        except Conversations.DoesNotExist:
            return Response(
                {'success': False, 'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )
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
