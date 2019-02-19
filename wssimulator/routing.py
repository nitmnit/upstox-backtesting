from django.conf.urls import url

from wssimulator import consumers

websocket_urlpatterns = [
    url(r'^ws/chat/$', consumers.ZWSSimulator),
]
