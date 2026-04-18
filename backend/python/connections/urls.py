from django.urls import path
from . import views

urlpatterns = [
    path('', views.ConnectionListView.as_view(), name='connections'),
    path('suggestions/', views.SuggestedConnectionListView.as_view(), name='suggested-connections'),
    path('follow/', views.follow_user, name='follow-user'),
    path('unfollow/', views.unfollow_user, name='unfollow-user'),
    path('block/', views.block_user, name='block-user'),
    path('mute/', views.mute_user, name='mute-user'),
    path('network/', views.get_user_network, name='user-network'),
    path('analytics/', views.get_connection_analytics, name='connection-analytics'),
    path('generate-suggestions/', views.generate_suggestions, name='generate-suggestions'),
    path('dismiss-suggestion/', views.dismiss_suggestion, name='dismiss-suggestion'),
]
