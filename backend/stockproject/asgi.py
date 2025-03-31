import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from mainapp.routing import websocket_urlpatterns
import asyncio
from functools import wraps

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockproject.settings')

def handle_shutdown(app):
    @wraps(app)
    async def wrapped_app(scope, receive, send):
        try:
            return await app(scope, receive, send)
        except asyncio.CancelledError:
            # Give extra time for cleanup
            await asyncio.sleep(1)
            raise
    return wrapped_app

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    )
})

# Apply shutdown handler in production
if not os.getenv('DJANGO_DEBUG', 'True') == 'True':
    application = handle_shutdown(application)