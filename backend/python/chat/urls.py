from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.ChatRoomListView.as_view(), name='chat-rooms'),
    path('rooms/<uuid:room_id>/messages/', views.MessageListView.as_view(), name='room-messages'),
    path('create-room/', views.create_room, name='create-room'),
    path('send-message/', views.send_message, name='send-message'),
    path('mark-read/', views.mark_as_read, name='mark-read'),
    path('react/', views.react_to_message, name='react-to-message'),
    path('start-typing/', views.start_typing, name='start-typing'),
    path('stop-typing/', views.stop_typing, name='stop-typing'),
    path('unread-count/', views.get_unread_count, name='unread-count'),
    path('analytics/', views.get_chat_analytics, name='chat-analytics'),
]
