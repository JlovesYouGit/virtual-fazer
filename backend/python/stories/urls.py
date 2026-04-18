from django.urls import path
from . import views

urlpatterns = [
    # Story listing and viewing
    path('', views.StoryListView.as_view(), name='story-list'),
    path('user/<uuid:user_id>/', views.UserStoryListView.as_view(), name='user-stories'),
    path('<uuid:story_id>/', views.StoryDetailView.as_view(), name='story-detail'),
    
    # Story creation and management
    path('create/', views.create_story, name='create-story'),
    path('<uuid:story_id>/view/', views.view_story, name='view-story'),
    path('<uuid:story_id>/like/', views.like_story, name='like-story'),
    path('<uuid:story_id>/delete/', views.delete_story, name='delete-story'),
    
    # Story interactions
    path('<uuid:story_id>/viewers/', views.get_story_viewers, name='story-viewers'),
    path('<uuid:story_id>/replies/', views.get_story_replies, name='story-replies'),
    path('<uuid:story_id>/reply/', views.reply_to_story, name='reply-story'),
    path('<uuid:story_id>/share/', views.share_story, name='share-story'),
    
    # Story highlights
    path('highlights/user/<uuid:user_id>/', views.get_user_highlights, name='user-highlights'),
    path('highlights/create/', views.create_highlight, name='create-highlight'),
    
    # Story analytics
    path('<uuid:story_id>/analytics/', views.get_story_analytics, name='story-analytics'),
]
