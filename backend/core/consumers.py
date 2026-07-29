from .models import Messages
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Chat
from django.utils import timezone
import base64
from django.core.files.base import ContentFile


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
        
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']

        self.room_name = f"chat_{self.chat_id}"

        await self.channel_layer.group_add(
            self.room_name,self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name, self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)


        msg_type = data.get("type", "message")
        if msg_type == "message":
            await self.handle_chat_message(data)
        elif msg_type == "typing":
            await self.handle_typing(data)
        elif msg_type == "screenshot":
            await self.handle_screenshot()

    async def handle_screenshot(self):
        await self._save_ss_notification()

        await self.channel_layer.group_send(
            self.room_name, {
                "type": "screenshot_taken",
                "sender": self.user.username
            }
        )

    @database_sync_to_async
    def _save_ss_notification(self):
        chat = Chat.objects.get(pk=self.chat_id)
        receiver = chat.user2 if chat.user1 == self.user else chat.user1
        Messages.objects.create(
            sender=self.user,
            receiver=receiver,
            text="",
            chat=chat,
            is_system=True
        )

    async def screenshot_taken(self, event):
        await self.send(text_data=json.dumps({
            "type": "screenshot",
            "sender": event["sender"]
        }))



    async def handle_typing(self,data):
        typer = data.get("typer")
        print(typer)

        await self.channel_layer.group_send(self.room_name, {
            "type": "typing",
            "typer":typer
        })

    async def typing(self, event):
        if event["typer"] == self.user.username:
            return 

        await self.send(text_data=json.dumps({
            "type":"typing",
            "typer": event["typer"]
        }))

    async def handle_chat_message(self, data):
        text = data.get("message", "")
        image_data = data.get("image")
        msg = await self._save_message(text, image_data)

        await self.channel_layer.group_send(
            self.room_name,
            {
                "type":"chat_message",
                "message":text,
                "sender_id": self.user.id,
                "sender_username": self.user.username,
                "created_at": str(msg.created_at),
                "image" : msg.image.url if msg.image else None,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "sender_id": event["sender_id"],
            "sender_username": event["sender_username"],
            "created_at" : event["created_at"], 
            "image" : event["image"]
        }))

    @database_sync_to_async
    def _save_message(self, text, image_data):
        chat = Chat.objects.get(pk=self.chat_id)
        image_url = None

        if image_data and ';base64,' in image_data:
            format, imgstr = image_data.split(';base64,')
            extension = format.split('/')[-1]
            image_url = ContentFile(
                base64.b64decode(imgstr),
                name=f'snap_{timezone.now()}.{extension}'
            )

        msg = Messages.objects.create(
            sender=self.user,
            receiver=chat.user2 if chat.user1 == self.user else chat.user1,
            text=text,
            chat=chat,
            image=image_url,  
        )

        chat.last_message = timezone.now()
        chat.save(update_fields=["last_message"])

        return msg


