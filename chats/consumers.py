import json
import base64
import os
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from ChatApp.models import Conversations, Conversations_Users, Message, User
from ChatApp import settings

# =============================
# DEV PRESENCE STORE
# =============================
CONNECTED_USERS = {}
USER_CONVERSATIONS = {}

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


@database_sync_to_async
def fetch_all_users(user_id):
    users = User.objects.exclude(id=user_id)
    return [
        {
            'id': u.id,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'profile': u.profile if u.profile else None,
            'email': u.email,
        }
        for u in users
    ]


@database_sync_to_async
def get_all_conversations(user_id):
    my_id = str(user_id)
    conversations = Conversations_Users.objects.filter(user_ids__icontains=my_id)
    data = []

    for cu in conversations:
        if not cu.conversation_id:
            continue
        conversation = cu.conversation_id

        # Split user_ids and get other users
        user_ids_list = [uid.strip() for uid in cu.user_ids.split(",") if uid.strip()]
        other_user_ids = [uid for uid in user_ids_list if uid != my_id]

        other_users_data = []
        for uid in other_user_ids:
            try:
                other_user = User.objects.get(id=int(uid))
                other_users_data.append({
                    'user_id': other_user.id,
                    'username': other_user.username,
                    'profile': other_user.profile if other_user.profile else None,
                    'first_name': other_user.first_name,
                    'last_name': other_user.last_name,
                    'email': other_user.email
                })
            except (User.DoesNotExist, ValueError):
                continue

        # Get the latest message
        latest_message = Message.objects.filter(conversation_id=conversation.id).order_by('-created_at').first()

        message = None
        latest_message_time = None
        if latest_message:
            latest_message_time = latest_message.created_at
            if latest_message.type == 'audio':
                message = 'audio..'
            elif latest_message.type == 'image':
                message = 'image..'
            else:
                message = latest_message.body

        # Append conversation data
        data.append({
            'conversation_user_ids': cu.user_ids,
            'conversation_id': conversation.id,
            'is_group': cu.is_group,
            'title': conversation.title,
            'latest_message_id': latest_message.id if latest_message else None,
            'latest_message_body': message,
            'latest_message_time': latest_message_time.isoformat() if latest_message_time else None,
            'participants': other_users_data  # <-- updated to array
        })

    return sorted(data, key=lambda x: x['latest_message_time'] or "", reverse=True)

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
        CONNECTED_USERS.setdefault(user_id, set()).add(self.channel_name)
        USER_CONVERSATIONS.setdefault(user_id, set())

        conversation_ids = await get_user_conversations(user_id)
        for conv_id in conversation_ids:
            USER_CONVERSATIONS[user_id].add(conv_id)
            await self.channel_layer.group_add(f"chat_{conv_id}", self.channel_name)

        await self.channel_layer.group_add("global_notifications", self.channel_name)
        await self.accept()
        await self.broadcast_connected_users()

    async def disconnect(self, close_code):
        user_id = self.user.id
        if user_id in CONNECTED_USERS:
            CONNECTED_USERS[user_id].discard(self.channel_name)
            if not CONNECTED_USERS[user_id]:
                del CONNECTED_USERS[user_id]
        USER_CONVERSATIONS.pop(user_id, None)
        await self.channel_layer.group_discard("global_notifications", self.channel_name)
        await self.broadcast_connected_users()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get("type")

            if msg_type == "join_conversation":
                conv_id = data.get("conversation_id")
                USER_CONVERSATIONS[self.user.id].add(conv_id)
                await self.channel_layer.group_add(f"chat_{conv_id}", self.channel_name)

            elif msg_type == "leave_conversation":
                conv_id = data.get("conversation_id")
                USER_CONVERSATIONS[self.user.id].discard(conv_id)
                await self.channel_layer.group_discard(f"chat_{conv_id}", self.channel_name)

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
                    "is_edited": message.is_edited,
                    "title" : conversation.title,
                    "status": message.status,
                    "media_url": message.media_url if message.media_url else None,
                    "conversation_id": conversation_id,
                    "sender_id": self.user.id,
                    "sender_first_name": self.user.first_name,
                    "sender_last_name": self.user.last_name,
                    "sender_profile": self.user.profile if self.user.profile else None,
                    "created_at": message.created_at.isoformat()
                }

                # Send to conversation group (chat window)
                await self.channel_layer.group_send(
                    f"chat_{conversation_id}",
                    {"type": "chat_message_event", "message": broadcast_data}
                )

            elif msg_type == "fetch_all_users":
                users_data = await fetch_all_users(self.user.id)
                await self.send(text_data=json.dumps({"type": "fetch_all_users", "data": users_data}))

            elif msg_type == "get_all_conversations":
                conv_data = await get_all_conversations(self.user.id)
                await self.send(text_data=json.dumps({"type": "get_all_conversations", "data": conv_data}))

        except Exception as e:
            print(f"[ERROR] Exception in receive: {e}")
            await self.send(text_data=json.dumps({"error": str(e)}))

    async def chat_message_event(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def broadcast_connected_users(self):
        users_list = list(CONNECTED_USERS.keys())
        await self.channel_layer.group_send(
            "global_notifications",
            {"type": "connected_users_event", "users": users_list}
        )

    async def connected_users_event(self, event):
        await self.send(text_data=json.dumps({
            "type": "connected_users",
            "users": event["users"]
        }))