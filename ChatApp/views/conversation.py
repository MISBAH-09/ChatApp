from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, Conversations, Conversations_Users ,Message
from ..middleware.auth import require_token
import datetime
from django.utils import timezone

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

max_dt = timezone.make_aware(datetime.datetime.max)

class getConversationAPI(APIView):
    @swagger_auto_schema(
        tags=["Conversations"],
        operation_summary="Create or get conversation",
        operation_description=(
            "Create a new conversation with another user, "
            "or return existing conversation if already created."
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer your_token_here",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id'],
            properties={
                'user_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    example=5,
                    description="Other user's ID"
                ),
                'title': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="New Chat",
                    description="Optional conversation title"
                ),
                'is_group': openapi.Schema(
                    type=openapi.TYPE_BOOLEAN,
                    example=False,
                    description="Set True for group creation"
                ),
                'user_ids': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    example="2,3,",
                    description="Comma-separated IDs for group users"
                )
            }
        ),
        responses={
            200: "Conversation already exists",
            201: "New conversation created",
            400: "Validation error",
            401: "Unauthorized"
        }
    )
    @require_token
    def post(self, request):
        try:
            user = request.auth_user
            my_id = str(user.id)
            is_group = request.data.get("is_group", False)
            title = request.data.get("title", "New Chat")

            if is_group:
                user_ids_str = request.data.get("user_ids", "")
                if not user_ids_str:
                    return Response({"success": False, "message": "No users selected"}, status=400)

                # Append current user if not included
                all_user_ids = user_ids_str.strip(",").split(",")
                if my_id not in all_user_ids:
                    all_user_ids.append(my_id)

                final_user_ids = ",".join(all_user_ids) + ","

                # Create group conversation
                conversation = Conversations.objects.create(title=title)
                Conversations_Users.objects.create(
                    conversation_id=conversation,
                    is_group=True,
                    user_ids=final_user_ids
                )

                # Fetch detailed user info
                users = User.objects.filter(id__in=all_user_ids)
                users_data = [
                    {
                        "user_id": u.id,
                        "username": u.username,
                        "email": u.email,
                        "first_name": u.first_name,
                        "last_name": u.last_name,
                        "profile": u.profile.url if u.profile else None
                    }
                    for u in users
                ]

                return Response({
                    "success": True,
                    "message": "Group created",
                    "data": {
                        "conversation_id": conversation.id,
                        "title": title,
                        "is_group": True,
                        "users": users_data
                    }
                }, status=201)

            else:
                other_user_id = str(request.data.get("user_id"))
                if not other_user_id:
                    return Response({"success": False, "message": "user_id is required"}, status=400)

                # Check existing single conversation
                search_my_id = f"{my_id},"
                search_other_id = f"{other_user_id},"

                common_conversation = Conversations_Users.objects.filter(
                    user_ids__contains=search_my_id
                ).filter(
                    user_ids__contains=search_other_id,
                    is_group=False
                ).values_list('conversation_id', flat=True).first()

                if common_conversation:
                    other_user = User.objects.get(id=other_user_id)
                    return Response({
                        "success": True,
                        "message": "Conversation already exists",
                        "data": {
                            "conversation_id": common_conversation,
                            "user_id": other_user.id,
                            "username": other_user.username,
                            "email": other_user.email,
                            "profile": other_user.profile.url if other_user.profile else None,
                            "first_name": other_user.first_name,
                            "last_name": other_user.last_name,
                            "title": title
                        }
                    }, status=200)

                # Create new single conversation
                conversation = Conversations.objects.create(title=title)
                all_user_ids = f"{my_id},{other_user_id},"
                Conversations_Users.objects.create(
                    conversation_id=conversation,
                    is_group=False,
                    user_ids=all_user_ids
                )

                other_user = User.objects.get(id=other_user_id)
                return Response({
                    "success": True,
                    "message": "New conversation created",
                    "data": {
                        "conversation_id": conversation.id,
                        "user_id": other_user.id,
                        "username": other_user.username,
                        "profile": other_user.profile.url if other_user.profile else None,
                        "email": other_user.email,
                        "first_name": other_user.first_name,
                        "last_name": other_user.last_name
                    }
                }, status=201)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


class getAllConversationsAPI(APIView):
    @swagger_auto_schema(
        tags=["Conversations"],
        operation_summary="Get all conversations",
        operation_description=(
            "Fetch all conversations of the authenticated user, "
            "including latest message preview."
        ),
        manual_parameters=[
            openapi.Parameter(
                'Authorization',
                openapi.IN_HEADER,
                description="Bearer your_token_here",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: "Conversations fetched successfully",
            400: "Error occurred",
            401: "Unauthorized"
        }
    )
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
            max_dt = None  # For sorting fallback if no messages

            for cu in conversations:
                if not cu.conversation_id:
                    continue  # skip if conversation is None

                conversation = cu.conversation_id  # Already a Conversations instance

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
                    Message.objects.filter(conversation_id=conversation.id)
                    .order_by('-created_at')
                    .first()
                )

                # Determine what to show for message
                message = None
                latest_message_time = None
                if latest_message:
                    latest_message_time = latest_message.created_at
                    max_dt = max_dt or latest_message_time  # fallback for sorting
                    if latest_message.type == 'audio':
                        message = 'audio..'
                    elif latest_message.type == 'image':
                        message = 'image..'
                    elif latest_message.type == 'text':
                        message = latest_message.body

                # Append conversation safely
                data.append({
                    'conversation_user_ids': cu.user_ids,
                    'conversation_id': conversation.id,
                    'is_group' : cu.is_group,
                    'title': conversation.title,
                    # 'created_at': cu.created_at,
                    # 'updated_at': cu.updated_at,
                    'latest_message_id': latest_message.id if latest_message else None,
                    'latest_message_body': message,
                    'latest_message_time': latest_message_time,
                    'user_id': other_user_data.id if other_user_data else None,
                    'username': other_user_data.username if other_user_data else None,
                    'profile': other_user_data.profile if other_user_data else None,
                    'first_name': other_user_data.first_name if other_user_data else None,
                    'last_name': other_user_data.last_name if other_user_data else None,
                    'email': other_user_data.email if other_user_data else None
                })

            # Sort the data by latest_message_time descending (latest first)
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