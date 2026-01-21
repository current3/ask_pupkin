from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

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
    path("ajax/question/vote/", views.ajax_question_vote, name="ajax_question_vote"),
    path("ajax/answer/vote/", views.ajax_answer_vote, name="ajax_answer_vote"),
    path("ajax/answer/correct/", views.ajax_set_correct, name="ajax_set_correct"),
]

