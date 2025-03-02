from django.http import JsonResponse
from django.shortcuts import render
from recommendation.services import get_recommendations_for_user

# Create your views here.
def recommenadtions(request, user_id):
    result = get_recommendations_for_user(user_id)
    return JsonResponse(result)