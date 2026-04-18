from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    # Comment CRUD operations
    path('<str:content_type>/<uuid:content_id>/', views.get_comments, name='get_comments'),
    path('<str:content_type>/<uuid:content_id>/create/', views.create_comment, name='create_comment'),
    path('comment/<uuid:comment_id>/', views.update_comment, name='update_comment'),
    path('comment/<uuid:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    
    # Comment interactions
    path('comment/<uuid:comment_id>/like/', views.like_comment, name='like_comment'),
    path('comment/<uuid:comment_id>/unlike/', views.unlike_comment, name='unlike_comment'),
    
    # Thread information
    path('<str:content_type>/<uuid:content_id>/thread/', views.get_comment_thread, name='get_comment_thread'),
    
    # Moderation and reporting
    path('comment/<uuid:comment_id>/report/', views.report_comment, name='report_comment'),
    path('moderation/queue/', views.get_moderation_queue, name='get_moderation_queue'),
    path('moderation/comment/<uuid:comment_id>/', views.moderate_comment, name='moderate_comment'),
    
    # Notifications
    path('notifications/', views.get_user_notifications, name='get_user_notifications'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
]
