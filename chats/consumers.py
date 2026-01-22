# import json
# from channels.generic.websocket import AsyncWebsocketConsumer
# from ChatApp.models import User, Conversations, Message
# from channels.db import database_sync_to_async

# class ChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
#         self.room_group_name = f"chat_{self.conversation_id}"

#         # Accept all connections without auth
#         await self.accept()

#         # Join the room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def disconnect(self, close_code):
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         try:
#             data = json.loads(text_data)
#             msg_type = data.get('type', 'text').lower()
#             body = data.get('body', '')
#             media_url = data.get('media', None)
#             sender_id = data.get('sender_id')  # Must be provided in message body

#             if not sender_id:
#                 await self.send(json.dumps({'error': 'sender_id is required'}))
#                 return

#             # Fetch sender from DB
#             sender = await database_sync_to_async(User.objects.get)(id=sender_id)

#             # Save message
#             conversation = await database_sync_to_async(Conversations.objects.get)(id=self.conversation_id)
#             message = Message(
#                 type=msg_type,
#                 body=body,
#                 sender_id=sender,
#                 conversation_id=conversation,
#                 status='active'
#             )
#             if media_url:
#                 message.media_url = media_url

#             await database_sync_to_async(message.save)()

#             # Broadcast to group
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     'type': 'chat_message',
#                     'message': {
#                         'id': message.id,
#                         'type': message.type,
#                         'body': message.body,
#                         'media_url': message.media_url,
#                         'sender_id': sender.id,
#                         'conversation_id': self.conversation_id,
#                         'created_at': str(message.created_at)
#                     }
#                 }
#             )

#         except Exception as e:
#             await self.send(json.dumps({'error': str(e)}))

#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps(event['message']))


import json
from channels.generic.websocket import AsyncWebsocketConsumer
from ChatApp.models import Conversations, Message
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"chat_{self.conversation_id}"

        # Use user from scope (set by middleware)
        self.user = self.scope.get('user')
        if not self.user:
            await self.close(code=4001)  # Unauthorized
            return

        # Join the room group
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
            msg_type = data.get('type', 'text').lower()
            body = data.get('body', '')
            media_url = data.get('media', None)

            # Save message in DB
            conversation = await database_sync_to_async(Conversations.objects.get)(id=self.conversation_id)
            message = Message(
                type=msg_type,
                body=body,
                sender_id=self.user,
                conversation_id=conversation,
                status='active'
            )
            if media_url:
                message.media_url = media_url

            await database_sync_to_async(message.save)()

            # Broadcast to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'type': message.type,
                        'body': message.body,
                        'media_url': message.media_url,
                        'sender_id': self.user.id,
                        'conversation_id': self.conversation_id,
                        'created_at': str(message.created_at)
                    }
                }
            )

        except Exception as e:
            await self.send(json.dumps({'error': str(e)}))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
