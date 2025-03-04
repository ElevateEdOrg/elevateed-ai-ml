from django.http import JsonResponse
from django.shortcuts import render
from recommendation.services import get_recommendations_for_user

# Create your views here.
# recommendation/views.py

from django.http import JsonResponse
from recommendation.services import get_recommendations_for_user

def recommendations(request, user_id):
    """
    Get course recommendations for a user.
    ---
    parameters:
      - name: user_id
        in: path
        type: string
        required: true
        description: The user UUID.
    responses:
      200:
        description: Returns a list of recommended course IDs.
        schema:
          type: object
          properties:
            user_id:
              type: string
            recommendations:
              type: array
              items:
                type: string
    """
    # Get recommendations using the service function.
    recommended_courses = get_recommendations_for_user(user_id)
    # Return a JSON response with the user_id and recommended course IDs.
    return JsonResponse({
        "user_id": str(user_id),
        "recommendations": recommended_courses
    })
