from django.urls import path
from . import views

urlpatterns = [
    path('models/', views.NeuralModelListCreateView.as_view(), name='neural-models'),
    path('patterns/', views.CategoryPatternListCreateView.as_view(), name='category-patterns'),
    path('analyze/', views.analyze_user_behavior, name='analyze-user-behavior'),
    path('match/', views.find_matching_users, name='find-matching-users'),
    path('auto-follow/', views.auto_follow_users, name='auto-follow-users'),
    path('profile/', views.get_user_neural_profile, name='user-neural-profile'),
    path('interactions/', views.get_user_interactions, name='user-interactions'),
]
