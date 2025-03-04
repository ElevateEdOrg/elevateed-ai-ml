# quiz/urls.py

from django.urls import path
from quiz import views

urlpatterns = [
    path("generate_quiz_for_course/<str:course_id>/", views.generate_quiz_for_course, name="generate_quiz_for_course"),
]
