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
]
