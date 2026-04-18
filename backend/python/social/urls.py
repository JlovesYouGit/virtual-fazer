from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # User profile and stats
    path('profile/<uuid:user_id>/', views.get_user_profile, name='get_user_profile'),
    path('profile/<uuid:user_id>/followers/', views.get_followers, name='get_followers'),
    path('profile/<uuid:user_id>/following/', views.get_following, name='get_following'),
    path('profile/<uuid:user_id>/activity/', views.get_user_activity, name='get_user_activity'),
    
    # Follow/unfollow
    path('follow/<uuid:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<uuid:user_id>/', views.unfollow_user, name='unfollow_user'),
    
    # Content interactions
    path('like/', views.like_content, name='like_content'),
    path('unlike/', views.unlike_content, name='unlike_content'),
    
    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    
    # Follow requests
    path('follow-requests/', views.get_follow_requests, name='get_follow_requests'),
    path('follow-requests/<uuid:request_id>/', views.respond_follow_request, name='respond_follow_request'),
]
