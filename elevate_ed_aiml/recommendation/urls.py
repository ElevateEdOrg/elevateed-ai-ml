from django.urls import path
from recommendation import views

urlpatterns = [
    path('<str:user_id>/', views.recommendations, name='recommendations'),
]