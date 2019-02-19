# mysite/routing.py
from channels.auth import AuthMiddlewareStack

from channels.routing import ProtocolTypeRouter, URLRouter
import wssimulator.routing

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            wssimulator.routing.websocket_urlpatterns
        )
    ),
})
