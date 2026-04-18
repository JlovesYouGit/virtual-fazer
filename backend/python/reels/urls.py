from django.urls import path
from . import views

urlpatterns = [
    path('', views.ReelListView.as_view(), name='reel-list'),
    path('<uuid:pk>/', views.ReelDetailView.as_view(), name='reel-detail'),
    path('interact/', views.interact_with_reel, name='reel-interact'),
    path('<uuid:reel_id>/comments/', views.get_reel_comments, name='reel-comments'),
    path('comments/create/', views.create_reel_comment, name='create-reel-comment'),
    path('search/', views.search_reels, name='search-reels'),
    path('trending/', views.get_trending_reels, name='trending-reels'),
    path('recommendations/', views.get_reel_recommendations, name='reel-recommendations'),
    path('analytics/', views.get_reel_analytics, name='reel-analytics'),
    path('hashtags/trending/', views.get_trending_hashtags, name='trending-hashtags'),
    path('challenges/', views.get_challenges, name='reel-challenges'),
    path('challenges/<uuid:challenge_id>/enter/', views.enter_challenge, name='enter-challenge'),
    # Reel forwarding endpoints
    path('forward/', views.forward_reel, name='forward-reel'),
    path('forward/users/', views.get_forwardable_users, name='forwardable-users'),
    path('forwards/received/', views.get_received_forwards, name='received-forwards'),
    path('forwards/saved/', views.get_saved_forwards, name='saved-forwards'),
    path('forwards/<uuid:forward_id>/save/', views.save_forwarded_reel, name='save-forwarded-reel'),
    path('forwards/<uuid:forward_id>/unsave/', views.unsave_forwarded_reel, name='unsave-forwarded-reel'),
]
