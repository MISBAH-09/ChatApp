from django.urls import re_path
from .consumers import  GlobalConsumer

websocket_urlpatterns = [
    # re_path(r"ws/chat/(?P<conversation_id>\d+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/global/$", GlobalConsumer.as_asgi()), 
]