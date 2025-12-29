import os
import aio_pika
import json
from channels.layers import get_channel_layer

class RabbitMQManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.exchange = None
        
    async def connect(self):
        url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
        self.connection = await aio_pika.connect_robust(url)
        self.channel = await self.connection.channel()
        self.exchange = await self.channel.declare_exchange(
            "chat_messages",
            aio_pika.ExchangeType.FANOUT,
            durable=True
        )
        
    async def publish_message(self, room, message, sender):
        if not self.exchange:
            await self.connect()
        data = {
            "room": room,
            "message": message,
            "sender": sender,
            "type": "chat_message"
        }
        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=""
        )
    
    async def start_consuming(self):
        if not self.channel:
            await self.connect()
        queue = await self.channel.declare_queue("", exclusive=True)
        await queue.bind(self.exchange)
     
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    await self.handle_message(message.body)
    
    async def handle_message(self, body):
        data = json.loads(body.decode())
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"room_{data['room']}",
            {
                "type": "chat_message",
                "message": data["message"],
                "sender": data["sender"]
            }
        )
    
    async def close(self):
        if self.connection:
            await self.connection.close()

rabbitmq_manager = RabbitMQManager()