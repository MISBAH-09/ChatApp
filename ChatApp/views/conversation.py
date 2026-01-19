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

      other_user_data = User.objects.get(id=other_user_id)
      # print("fghjd",other_user_data.username)

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
            my_id = str(user.id)

            # Fetch all conversations containing my_id anywhere
            conversations = Conversations_Users.objects.filter(
                user_ids__icontains=my_id
            )

            data = []
            for cu in conversations:

                user_ids_list = [uid.strip() for uid in cu.user_ids.split(",") if uid.strip()]

                other_user_ids = [uid for uid in user_ids_list if uid != my_id]

                other_user_id = int(other_user_ids[0])
                other_user_data = User.objects.get(id=other_user_id)

                # Append conversation data
                data.append({
                    'conversation_user_ids': cu.user_ids,
                    'conversation_id': cu.conversation_id.id,
                    # 'title': cu.title,
                    'created_at': cu.created_at,
                    'updated_at': cu.updated_at,
                    'user_id': other_user_data.id,
                    'username': other_user_data.username,
                    'profile': other_user_data.profile,
                    'first_name': other_user_data.first_name,
                    'last_name': other_user_data.last_name     
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

