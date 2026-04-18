from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('me/', views.UserDetailView.as_view(), name='user-detail'),
    path('activity/', views.user_activity_view, name='user-activity'),
    path('track-activity/', views.track_activity, name='track-activity'),
]
