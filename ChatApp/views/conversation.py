from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, Conversations, Conversations_Users ,Message
from ..middleware.auth import require_token
import datetime
from django.utils import timezone

max_dt = timezone.make_aware(datetime.datetime.max)

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

      other_user_data = User.objects.get(id=other_user_id)


      # Wrap IDs with commas 
      search_my_id = f"{my_id},"
      search_other_id = f"{other_user_id},"

      # does exsists
      common_conversation = Conversations_Users.objects.filter(
          user_ids__contains=search_my_id
      ).filter(
          user_ids__contains=search_other_id
      ).values_list('conversation_id', flat=True).first()

      if common_conversation:
        return Response({
          'success': True,
          'message': 'Conversation already exists',
          'data': {
            'conversation_id': common_conversation,
            'user_id' : other_user_data.id,
            'username' : other_user_data.username,
            'email'   : other_user_data.email,
            'profile' : other_user_data.profile,
            'first_name' : other_user_data.first_name,
            'last_name' :other_user_data.last_name,
            'title' : title       
          }
        }, status=status.HTTP_200_OK)

      conversation = Conversations.objects.create(
        title=title
      )

      # Store IDs as comma-separated string
      all_user_ids = f"{my_id},{other_user_id},"

      Conversations_Users.objects.create(
          conversation_id=conversation,
          user_ids=all_user_ids
      )

      return Response({
          'success': True,
          'message': 'New conversation created',
          'data': {
            'conversation_id': conversation.id,
            'user_id' : other_user_data.id,
            'username' : other_user_data.username,
            'profile' : other_user_data.profile,
            'email' : other_user_data.email,
            'first_name' : other_user_data.first_name,
            'last_name' :other_user_data.last_name       
          }
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
            if not user:
                return Response({'success': False, 'error': 'User not authenticated'}, status=400)

            my_id = str(user.id)

            # Fetch all conversations containing my_id
            conversations = Conversations_Users.objects.filter(user_ids__icontains=my_id)

            data = []
            for cu in conversations:
                if not cu.conversation_id:
                    continue  # skip if conversation is None

                # Split user_ids and get other users
                user_ids_list = [uid.strip() for uid in cu.user_ids.split(",") if uid.strip()]
                other_user_ids = [uid for uid in user_ids_list if uid != my_id]

                other_user_data = None
                if other_user_ids:
                    try:
                        other_user_id = int(other_user_ids[0])
                        other_user_data = User.objects.get(id=other_user_id)
                    except (User.DoesNotExist, ValueError):
                        other_user_data = None

                # Get the latest message in this conversation
                latest_message = (
                    Message.objects.filter(conversation_id=cu.conversation_id.id)
                    .order_by('-created_at')
                    .first()
                )

                # Determine what to show for message
                message = None
                latest_message_time = None
                if latest_message:
                    latest_message_time = latest_message.created_at
                    if latest_message.type == 'audio':
                        message = 'audio..'
                    elif latest_message.type == 'image':
                        message = 'image..'
                    elif latest_message.type == 'text':
                        message = latest_message.body

                # Append conversation safely
                data.append({
                    'conversation_user_ids': cu.user_ids,
                    'conversation_id': cu.conversation_id.id,
                    'created_at': cu.created_at,
                    'updated_at': cu.updated_at,
                    'latest_message_id': latest_message.id if latest_message else None,
                    'latest_message_body': message,
                    'latest_message_time': latest_message_time,
                    'user_id': other_user_data.id if other_user_data else None,
                    'username': other_user_data.username if other_user_data else None,
                    'profile': other_user_data.profile if other_user_data else None,
                    'first_name': other_user_data.first_name if other_user_data else None,
                    'last_name': other_user_data.last_name if other_user_data else None,
                    'email' :other_user_data.email
                })

            # Sort the data by latest_message_time ascending (None values go last)
            data_sorted = sorted(
                data,
                key=lambda x: x['latest_message_time'] or max_dt,
                reverse=True
            )
            return Response({
                'success': True,
                'message': 'Conversations fetched',
                'data': data_sorted
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
