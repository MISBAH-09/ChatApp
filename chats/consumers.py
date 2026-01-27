import json
import base64
import os
import uuid

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from ChatApp.models import Conversations, Conversations_Users, Message
from ChatApp import settings

# =============================
# DEV PRESENCE STORE
# =============================
CONNECTED_USERS = {}        # { user_id: set(channel_names) }
USER_CONVERSATIONS = {}     # { user_id: set(conversation_ids) }

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

@database_sync_to_async
def get_conversation_participants(conversation_id):
    conv = Conversations_Users.objects.filter(conversation_id=conversation_id).first()
    if not conv:
        return set()
    return set(int(uid) for uid in conv.user_ids.strip(',').split(',') if uid)

@database_sync_to_async
def get_user_conversations(user_id):
    convs = Conversations_Users.objects.filter(user_ids__contains=f"{user_id},")
    return [c.conversation_id.id for c in convs]

# =============================
# GLOBAL CONSUMER
# =============================
class GlobalConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user:
            await self.close(code=4001)
            return

        user_id = self.user.id

        # Track connected users
        if user_id not in CONNECTED_USERS:
            CONNECTED_USERS[user_id] = set()
        CONNECTED_USERS[user_id].add(self.channel_name)

        # Track user conversations
        if user_id not in USER_CONVERSATIONS:
            USER_CONVERSATIONS[user_id] = set()

        # Auto-join user to all their conversations
        conversation_ids = await get_user_conversations(user_id)
        for conv_id in conversation_ids:
            USER_CONVERSATIONS[user_id].add(conv_id)
            await self.channel_layer.group_add(f"chat_{conv_id}", self.channel_name)

        # Add user to global notifications group
        await self.channel_layer.group_add("global_notifications", self.channel_name)
        await self.accept()

        # Broadcast updated connected users
        await self.broadcast_connected_users()

    async def disconnect(self, close_code):
        user_id = self.user.id

        # Remove channel
        if user_id in CONNECTED_USERS:
            CONNECTED_USERS[user_id].discard(self.channel_name)
            if not CONNECTED_USERS[user_id]:
                del CONNECTED_USERS[user_id]

        # Remove conversation tracking
        USER_CONVERSATIONS.pop(user_id, None)

        # Remove from global notifications group
        await self.channel_layer.group_discard("global_notifications", self.channel_name)

        # Broadcast updated connected users
        await self.broadcast_connected_users()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            # --------------------
            # JOIN / LEAVE conversation
            # --------------------
            if msg_type == "join_conversation":
                conv_id = data.get("conversation_id")
                USER_CONVERSATIONS[self.user.id].add(conv_id)
                await self.channel_layer.group_add(f"chat_{conv_id}", self.channel_name)

            elif msg_type == "leave_conversation":
                conv_id = data.get("conversation_id")
                USER_CONVERSATIONS[self.user.id].discard(conv_id)
                await self.channel_layer.group_discard(f"chat_{conv_id}", self.channel_name)

            # --------------------
            # CHAT MESSAGE
            # --------------------
            elif msg_type == "chat_message":
                conversation_id = data.get("conversation_id")
                conversation = await get_conversation(conversation_id)

                message = Message(
                    conversation_id=conversation,
                    sender_id=self.user,
                    type=data.get("msg_type", "text").lower(),
                    body=data.get("body", ""),
                    status="active"
                )

                media = data.get("media")
                if message.type == "image" and media:
                    message.media_url = await save_base64_image(media)
                elif message.type == "audio" and media:
                    message.media_url = await save_base64_audio(media)

                message = await save_message(message)

                broadcast_data = {
                    "id": message.id,
                    "type": message.type,
                    "body": message.body,
                    "status": message.status,
                    "media_url": f"{settings.MEDIA_URL}{message.media_url}" if message.media_url else None,
                    "conversation_id": conversation_id,
                    "sender_id": self.user.id,
                    "sender_first_name": self.user.first_name,
                    "sender_last_name": self.user.last_name,
                    "sender_profile": self.user.profile,
                    "created_at": message.created_at.isoformat()
                }

                # --------------------
                # 1️⃣ Send to conversation group (everyone joined)
                # --------------------
                await self.channel_layer.group_send(
                    f"chat_{conversation_id}",
                    {"type": "chat_message_event", "message": broadcast_data}
                )

                # --------------------
                # 2️⃣ Send global notification ONLY to relevant participants NOT in chat
                # --------------------
                participants = await get_conversation_participants(conversation_id)
                for user_id, channels in CONNECTED_USERS.items():
                    if user_id == self.user.id:  # skip sender
                        continue
                    if user_id not in participants:  # skip non-participants
                        continue
                    if conversation_id in USER_CONVERSATIONS.get(user_id, set()):  # skip users already in chat
                        continue

                    for channel in channels:
                        await self.channel_layer.send(channel, {
                            "type": "global_message_event",
                            "message": broadcast_data
                        })

        except Exception as e:
            await self.send(text_data=json.dumps({"error": str(e)}))

    # --------------------
    # Event handlers
    # --------------------
    async def chat_message_event(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def global_message_event(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def broadcast_connected_users(self):
        users_list = list(CONNECTED_USERS.keys())
        await self.channel_layer.group_send(
            "global_notifications",
            {
                "type": "connected_users_event",
                "users": users_list
            }
        )

    async def connected_users_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "connected_users",
            "users": event["users"]
        }))
