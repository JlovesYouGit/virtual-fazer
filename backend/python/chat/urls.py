from django.urls import path
from . import views, inbox_views

urlpatterns = [
    # Basic chat functionality
    path('rooms/', views.ChatRoomListView.as_view(), name='chat-rooms'),
    path('rooms/<uuid:room_id>/messages/', views.MessageListView.as_view(), name='room-messages'),
    path('rooms/<uuid:room_id>/', inbox_views.get_chat_room, name='chat-room-detail'),
    path('create-room/', views.create_room, name='create-room'),
    path('send-message/', views.send_message, name='send-message'),
    path('mark-read/', views.mark_as_read, name='mark-read'),
    path('react/', views.react_to_message, name='react-to-message'),
    path('start-typing/', views.start_typing, name='start-typing'),
    path('stop-typing/', views.stop_typing, name='stop-typing'),
    path('unread-count/', views.get_unread_count, name='unread-count'),
    path('analytics/', views.get_chat_analytics, name='chat-analytics'),
    
    # Inbox and DM functionality
    path('inbox/', inbox_views.InboxListView.as_view(), name='inbox'),
    path('inbox/summary/', inbox_views.get_inbox_summary, name='inbox-summary'),
    path('inbox/direct-message/', inbox_views.create_direct_message, name='create-direct-message'),
    path('inbox/rooms/<uuid:room_id>/read/', inbox_views.mark_room_as_read, name='mark-room-read'),
    path('inbox/rooms/<uuid:room_id>/archive/', inbox_views.archive_room, name='archive-room'),
    path('inbox/rooms/<uuid:room_id>/mute/', inbox_views.mute_room, name='mute-room'),
    path('inbox/rooms/<uuid:room_id>/delete/', inbox_views.delete_room, name='delete-room'),
    path('inbox/search/', inbox_views.search_conversations, name='search-conversations'),
    path('inbox/rooms/<uuid:room_id>/history/', inbox_views.get_message_history, name='message-history'),
]
