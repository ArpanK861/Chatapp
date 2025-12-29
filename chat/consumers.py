import json
import redis.asyncio as redis
import aio_pika
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .jwt_utils import decode_jwt
from .models import Message
from .presence import set_online, set_offline, typing_start, typing_end, get_online_count, get_redis_client
from .rabbitmq import rabbitmq_manager

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        token = self.scope['query_string'].decode().replace("token=", "")
        user = await sync_to_async(decode_jwt)(token)
        if not user:
            await self.close()
            return  
        self.user = user
        self.room_name = self.scope['url_route']['kwargs']['room']
        self.room_group_name = f"room_{self.room_name}"
        await set_online(user)
        online_count = await get_online_count()
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "user_count_update",
                "count": online_count
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'user'):
            await set_offline(self.user)
            online_count = await get_online_count()
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "user_count_update",
                    "count": online_count
                }
            )
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @sync_to_async
    def save_message(self, text):
        return Message.objects.create(
            room=self.room_name, 
            sender=self.user, 
            text=text, 
            delivered=True
        ).id
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        if "typing" in data:
            is_typing = data.get("typing")
            if is_typing:
                await typing_start(self.room_name, self.user)
            else:
                await typing_end(self.room_name, self.user)
            
            await self.channel_layer.group_send(self.room_group_name, {
                "type": "typing_notification", 
                "user": self.user.username, 
                "is_typing": is_typing
            })
            return

        if await self.check_rate_limit():
            await self.send(json.dumps({"error": "Rate limit exceeded"}))
            return
                
        msg_id = await self.save_message(data["message"])

        if rabbitmq_manager.exchange:
            message_body = json.dumps({
                "room": self.room_name,
                "message": data["message"],
                "sender": self.user.username,
                "message_id": msg_id
            })
            await rabbitmq_manager.exchange.publish(
                aio_pika.Message(
                    body=message_body.encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=""
            )

    async def chat_message(self, event):
        await self.send(json.dumps({
            "type": "message",
            "message": event["message"],
            "sender": event["sender"]
        }))

    async def typing_notification(self, event):
        await self.send(json.dumps(event))
    
    async def user_count_update(self, event):
        await self.send(json.dumps({
            "type": "user_count",
            "count": event["count"]
        }))

    async def check_rate_limit(self):  
        r = get_redis_client()
        key = f"rate_limit:{self.user.username}"
        try:
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, 3)
            return count > 5
        finally:
            await r.close()