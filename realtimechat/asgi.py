import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realtimechat.settings')
django.setup()

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from chat.routing import websocket_urlpatterns
from chat.rabbitmq import rabbitmq_manager

class CustomProtocolTypeRouter(ProtocolTypeRouter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rabbitmq_started = False
    
    async def __call__(self, scope, receive, send):
        if not self._rabbitmq_started:
            self._rabbitmq_started = True
            import asyncio
            await rabbitmq_manager.connect()
            asyncio.create_task(rabbitmq_manager.start_consuming())
        
        return await super().__call__(scope, receive, send)

application = CustomProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})