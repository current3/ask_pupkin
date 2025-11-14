from django.urls import path
from . import views

urlpatterns = [
    path('', views.new_questions, name='new_questions'),
    path('hot/', views.hot_questions, name='hot_questions'),
    path('tag/<str:tag>/', views.tag_questions, name='tag_questions'),
    path('question/<int:qid>/', views.question, name='question'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('ask/', views.ask_view, name='ask'),
    path('profile/', views.profile_view, name='profile'),
]
