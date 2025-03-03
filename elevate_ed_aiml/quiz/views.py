from django.shortcuts import render

# Create your views here.
# quiz/views.py

from django.http import JsonResponse
from .quiz import MCQGenerator
from .config import Config as QuizConfig

def generate_quiz_for_course(request, course_id):
    collection_name = f"course_{course_id}"
    mcq_gen = MCQGenerator(api_key=QuizConfig.GROQ_API_KEY, qdrant_url=QuizConfig.QDRANT_URL, collection_name=collection_name)
    result = mcq_gen.generate_mcqs(topic="Generate a comprehensive quiz for the course", num_questions=10)
    return JsonResponse(result)
