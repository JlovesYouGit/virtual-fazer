from django.urls import path, include
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(), name='profile-update'),
    path('activity/', views.UserActivityView.as_view(), name='activity'),
    path('social/', include('users.urls_social')),
    path('email/', include('users.urls_email')),
    path('track-activity/', views.track_activity, name='track-activity'),
]
