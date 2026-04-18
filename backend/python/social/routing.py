from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Personal social notifications channel
    re_path(r'ws/social/$', consumers.SocialConsumer.as_asgi()),
    
    # Content-specific social channels
    re_path(r'ws/social/(?P<content_type>\w+)/(?P<content_id>[^/]+)/$', 
            consumers.ContentSocialConsumer.as_asgi()),
    
    # User-specific social channels
    re_path(r'ws/social/user/(?P<user_id>[^/]+)/$', 
            consumers.UserSocialConsumer.as_asgi()),
]
