from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, Conversations, Conversations_Users ,Message
from ..middleware.auth import require_token
from ChatApp import settings
import base64
import os
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


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
	@swagger_auto_schema(
			tags=["Messages"],
			operation_summary="Send message",
			operation_description=(
					"Send a text, image, or audio message in a conversation. "
					"For image/audio, provide Base64 encoded media."
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
					required=['conversation_id', 'type'],
					properties={
							'conversation_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
							'type': openapi.Schema(
									type=openapi.TYPE_STRING,
									enum=['text', 'image', 'audio'],
									example='text'
							),
							'body': openapi.Schema(type=openapi.TYPE_STRING, example="Hello 👋"),
							'status': openapi.Schema(type=openapi.TYPE_STRING, example="active"),
							'media': openapi.Schema(
									type=openapi.TYPE_STRING,
									description="Base64 encoded image/audio"
							),
					}
			),
			responses={
					201: "Message sent successfully",
					400: "Validation error",
					401: "Unauthorized",
					404: "Conversation not found"
			}
	)
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

class deleteMessageAPI(APIView):
	@swagger_auto_schema(
			tags=["Messages"],
			operation_summary="Delete message",
			operation_description="Soft delete a message. Only sender can delete.",
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
					required=['message_id'],
					properties={
							'message_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
					}
			),
			responses={
					200: "Message deleted successfully",
					400: "Already deleted / invalid request",
					403: "Not authorized",
					404: "Message not found"
			}
	)
	@require_token
	def post(self, request):
		try:
			user = request.auth_user  # Authenticated user
			message_id = request.data.get('message_id')

			if not message_id:
				return Response(
					{'success': False, 'error': 'message_id is required'},
					status=status.HTTP_400_BAD_REQUEST
				)
			message = Message.objects.get(id=message_id)

			#  authenticated user
			if message.sender_id != user:
				return Response(
					{ 'success': False,'error': 'Sender not authorized',},
					status=status.HTTP_403_FORBIDDEN
				)

			# already deleted
			if message.status == 'delete':
				return Response(
					{'success': False, 'error': 'Message already deleted'},
					status=status.HTTP_400_BAD_REQUEST
				)

			Message.objects.filter(id=message_id, sender_id=user).update(status='delete')
			
			return Response({
				'success': True,
				'message': 'Message deleted successfully',
				'data': {
					'id': message.id,
					'type': message.type,
					'body': message.body,
					'status': message.status,
					'media_url': message.media_url,
					'sender_id': message.sender_id.id,
				}
			}, status=status.HTTP_200_OK)

		except Message.DoesNotExist:
			return Response(
				{'success': False, 'error': 'Message not found'},
				status=status.HTTP_404_NOT_FOUND
			)
		except Exception as e:
			return Response(
				{'success': False, 'error': str(e)},
				status=status.HTTP_400_BAD_REQUEST
			)

class UpdateMessageAPI(APIView):
	@swagger_auto_schema(
			tags=["Messages"],
			operation_summary="Update message",
			operation_description="Update text of an existing message. Only sender can update.",
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
					required=['message_id', 'message_body'],
					properties={
							'message_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=5),
							'message_body': openapi.Schema(type=openapi.TYPE_STRING, example="Updated message"),
					}
			),
			responses={
					200: "Message updated successfully",
					400: "Invalid request",
					403: "Not authorized",
					404: "Message not found"
			}
	)
	@require_token
	def put(self, request):
		response_data = {
			'success': False,
			'message': '',
			'data': None
		}

		user = request.auth_user
		message_id = request.data.get('message_id')
		message_body = request.data.get('message_body')
		print(message_body)

		# Validate input
		if not message_id or message_body is None:
			response_data['message'] = "message_id and message_body are required."
			return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

		try:
			message = Message.objects.get(id=message_id)

			#  user is the sender
			if message.sender_id != user:
				response_data['message'] = "You are not allowed to update this message."
				return Response(response_data, status=status.HTTP_403_FORBIDDEN)

			# Check if the message is already deleted
			if message.status == 'delete':
				response_data['message'] = "Deleted messages cannot be updated."
				return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

			# Update the message body
			message.body = message_body
			message.is_edited = True
			message.save()

			response_data['success'] = True
			response_data['message'] = "Message updated successfully"
			response_data['data'] = {
				'id': message.id,
				'body': message.body,
				'status': message.status,
				'is_edited' : message.is_edited,
				'updated_at': message.updated_at.isoformat() if hasattr(message, 'updated_at') else None,
			}

			return Response(response_data, status=status.HTTP_200_OK)

		except Message.DoesNotExist:
			response_data['message'] = "Message not found."
			return Response(response_data, status=status.HTTP_404_NOT_FOUND)

		except Exception as e:
			response_data['message'] = str(e)
			return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class getConversationMessages(APIView):

	@swagger_auto_schema(
		tags=["Messages"],
		operation_summary="Get conversation messages",
		operation_description="Fetch all messages of a conversation ordered by time.",
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
				required=['conversation_id'],
				properties={
						'conversation_id': openapi.Schema(type=openapi.TYPE_INTEGER, example=2),
				}
		),
		responses={
				200: "Messages fetched successfully",
				400: "Validation error",
				404: "Conversation not found"
		}
	)
	@require_token
	def post(self, request):
		try:
			user = request.auth_user
			conversation_id = request.data.get('conversation_id')

			if not conversation_id:
					return Response(
							{'success': False, 'error': 'conversation_id is required'},
							status=status.HTTP_400_BAD_REQUEST
					)

			conversation = Conversations.objects.get(id=conversation_id)
			messages = Message.objects.filter(
					conversation_id=conversation
			).order_by('created_at')

			messages_data = []
			for m in messages:
					senderdata = User.objects.get(id=m.sender_id.id)

					messages_data.append({
							'id': m.id,
							'type': m.type,
							'body': m.body,
							'media_url': m.media_url,
							'status': m.status,
							'is_edited': m.is_edited,
							'created_at': m.created_at,
							'updated_at': m.updated_at,
							'user_id': user.id,
							'sender_id': m.sender_id.id,
							'conversation_id': m.conversation_id.id,
							'sender_first_name': senderdata.first_name,
							'sender_last_name': senderdata.last_name,
							'sender_profile': senderdata.profile,
							'sender_username': senderdata.username
					})

			return Response({
					'success': True,
					'message': 'Messages fetched successfully',
					'data': messages_data
			}, status=status.HTTP_200_OK)

		except Conversations.DoesNotExist:
			return Response(
					{'success': False, 'error': 'Conversation not found'},
					status=status.HTTP_404_NOT_FOUND
			)

		except Exception as e:
			return Response(
					{'success': False, 'error': str(e)},
					status=status.HTTP_400_BAD_REQUEST
			)  # debug error