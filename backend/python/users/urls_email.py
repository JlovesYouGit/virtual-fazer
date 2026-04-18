from django.urls import path
from . import views_email

app_name = 'email_auth'

urlpatterns = [
    path('verify/', views_email.send_email_verification, name='send-email-verification'),
    path('verify/<str:uidb64>/<str:token>/', views_email.verify_email, name='verify-email'),
    path('reset/', views_email.send_password_reset, name='send-password-reset'),
    path('reset/<str:uidb64>/<str:token>/', views_email.reset_password, name='reset-password'),
    path('change/', views_email.change_password, name='change-password'),
    path('check/', views_email.check_email_exists, name='check-email-exists'),
]
