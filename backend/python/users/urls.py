from django.urls import path, include
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/update/', views.UserDetailView.as_view(), name='profile-update'),
    path('activity/', views.user_activity_view, name='activity'),
    path('track-activity/', views.track_activity, name='track-activity'),
    path('auth/callback/google/', views.google_oauth_callback, name='google_oauth_callback'),
]
