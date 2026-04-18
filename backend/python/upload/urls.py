from django.urls import path
from . import views

app_name = 'upload'

urlpatterns = [
    # Upload endpoints
    path('init/', views.initialize_upload, name='initialize_upload'),
    path('confirm/<str:file_id>/', views.confirm_upload, name='confirm_upload'),
    path('status/<str:file_id>/', views.get_upload_status, name='get_upload_status'),
    path('file/<str:file_id>/', views.get_file_info, name='get_file_info'),
    path('file/<str:file_id>/delete/', views.delete_file, name='delete_file'),
    path('file/<str:file_id>/process/', views.process_file, name='process_file'),
    
    # User management
    path('user-files/', views.get_user_uploads, name='get_user_uploads'),
    path('analytics/', views.get_upload_analytics, name='get_upload_analytics'),
    
    # Webhooks
    path('webhook/upload-complete/', views.webhook_upload_complete, name='webhook_upload_complete'),
]
