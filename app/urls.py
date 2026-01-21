from django.urls import path
from . import views

urlpatterns = [
    path('', views.new_questions, name='new_questions'),
    path('hot/', views.hot_questions, name='hot_questions'),
    path('tag/<str:tag>/', views.tag_questions, name='tag_questions'),
    path("question/<int:id>/", views.question_view, name="question"),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('ask/', views.ask_view, name='ask'),
    path("logout/", views.logout_view, name="logout"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
]
