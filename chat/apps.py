import os
import asyncio
import threading
from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        if os.environ.get('RUN_MAIN'):
            from .rabbitmq import start_rabbitmq_consumer
            
            def run_async_consumer():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(start_rabbitmq_consumer())
            
            thread = threading.Thread(target=run_async_consumer, daemon=True)
            thread.start()