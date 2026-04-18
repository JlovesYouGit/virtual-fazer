from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Django allauth URLs
    path('accounts/', include('allauth.urls')),
    path('api/auth/', include('users.urls')),
    path('api/auth/', include('users.urls_social')),
    # path('api/neural/', include('neural.urls')),  # Temporarily disabled due to TensorFlow issues
    # path('api/connections/', include('connections.urls')),  # Temporarily disabled due to neural dependencies
    path('api/social/', include('social.urls')),
    # path('api/chat/', include('chat.urls')),  # Temporarily disabled due to neural dependencies
    # path('api/reels/', include('reels.urls')),  # Temporarily disabled due to neural dependencies
    # path('api/comments/', include('comments.urls')),  # Temporarily disabled due to neural dependencies
    path('api/upload/', include('upload.urls')),
    path('api/stories/', include('stories.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
