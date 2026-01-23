import json
import base64
import os
import uuid

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from ChatApp.models import Conversations, Message
from ChatApp import settings


# -----------------------------
# SYNC HELPERS
# -----------------------------
def _save_base64_file(base64_data, folder, extension):
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]

    file_data = base64.b64decode(base64_data)
    filename = f"{uuid.uuid4()}.{extension}"

    folder_path = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(folder_path, exist_ok=True)

    file_path = os.path.join(folder_path, filename)
    with open(file_path, "wb") as f:
        f.write(file_data)

    return f"{folder}/{filename}"


@database_sync_to_async
def save_base64_image(base64_data):
    return _save_base64_file(base64_data, "ImgMessages", "jpg")


@database_sync_to_async
def save_base64_audio(base64_data):
    return _save_base64_file(base64_data, "AudioMessages", "webm")


@database_sync_to_async
def get_conversation(conversation_id):
    return Conversations.objects.get(id=conversation_id)


@database_sync_to_async
def save_message(message):
    message.save()
    return message


# -----------------------------
# WEBSOCKET CONSUMER
# -----------------------------
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        self.user = self.scope.get("user")
        if not self.user:
            await self.close(code=4001)
            return

        # Join the room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type", "text").lower()
            body = data.get("body", "")
            base64_media = data.get("media")

            conversation = await get_conversation(self.conversation_id)

            message = Message(
                conversation_id=conversation,
                sender_id=self.user,
                type=msg_type,
                body=body,
                status="active"
            )

            # Media handling
            if msg_type == "image" and base64_media:
                message.media_url = await save_base64_image(base64_media)
            elif msg_type == "audio" and base64_media:
                message.media_url = await save_base64_audio(base64_media)

            message = await save_message(message)

            # Broadcast message to group
            broadcast_data = {
                "id": message.id,
                "type": message.type,
                "body": message.body,
                "status" :message.status,
                "media_url": f"{settings.MEDIA_URL}{message.media_url}" if message.media_url else None,
                "sender_id": self.user.id,
                "conversation_id": self.conversation_id,
                "created_at": message.created_at.isoformat(),
                "sender_id": self.user.id,
                "sender_first_name": self.user.first_name,
                "sender_last_name": self.user.last_name,
                "sender_profile": self.user.profile,

            }

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": broadcast_data
                }
            )



#             await self.channel_layer.group_send(
#     self.room_group_name,
#     {
#         "type": "chat_message",
#         "message": {
#             "id": message.id,
#             "type": message.type,
#             "body": message.body,
#             "media_url": f"{settings.MEDIA_URL}{message.media_url}" if message.media_url else None,
#             "sender_id": self.user.id,
#             "sender_first_name": self.user.first_name,
#             "sender_last_name": self.user.last_name,
#             "sender_profile": f"{settings.MEDIA_URL}{self.user.profile}" if getattr(self.user, "profile", None) else None,
#             "conversation_id": self.conversation_id,
#             "created_at": message.created_at.isoformat(),
#         }
#     }
# )


        except Exception as e:
            await self.send(text_data=json.dumps({
                "error": str(e)
            }))

    async def chat_message(self, event):
        message = event.get("message")
        await self.send(text_data=json.dumps(message))
