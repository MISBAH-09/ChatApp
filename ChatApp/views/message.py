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
            body = request.data.get('message', "")
            media_url = request.data.get('media_url', "")
            message_status = request.data.get('status', "active")

            if not conversation_id:
                return Response(
                    {'success': False, 'error': 'conversation_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            message = Message.objects.create(
                type=type,
                body=body,
                status=message_status,
                media_url=media_url,
                sender=user,
                conversation_id=conversation_id
            )

            return Response({
                'success': True,
                'message': 'Message sent successfully',
                'data': {
                    'id': message.id,
                    'body': message.body,
                    'sender_id': user.id,
                    'conversation_id': conversation_id
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
