from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Personal comment notifications channel
    re_path(r'ws/comments/$', consumers.CommentConsumer.as_asgi()),
    
    # Content-specific comment thread channels
    re_path(r'ws/comments/(?P<content_type>\w+)/(?P<content_id>[^/]+)/$', 
            consumers.CommentThreadConsumer.as_asgi()),
]
