# mysite/asgi.py
import os
import django # <-- ADD THIS IMPORT

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Set the Django settings module environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

# <-- ADD THIS LINE: Explicitly set up Django
django.setup()

# Now import your app's WebSocket routing
import chat.routing

# This is the standard Django HTTP application (for your regular views, admin, DRF)
http_application = get_asgi_application()

application = ProtocolTypeRouter({
    # Handle traditional HTTP requests
    "http": http_application,

    # Handle WebSocket connections
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})