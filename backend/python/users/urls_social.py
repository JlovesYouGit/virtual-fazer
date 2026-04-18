from django.urls import path
from . import views_social

app_name = 'social_auth'

urlpatterns = [
    path('google/login/', views_social.google_login, name='google-login'),
    path('google/register/', views_social.google_register, name='google-register'),
    path('google/link/', views_social.link_google_account, name='link-google-account'),
    path('google/unlink/', views_social.unlink_google_account, name='unlink-google-account'),
    path('accounts/', views_social.get_social_accounts, name='social-accounts'),
    path('profile/', views_social.user_profile_with_social, name='profile-with-social'),
]
