from django.http import JsonResponse
from .quiz import MCQGenerator
from .config import Config as QuizConfig# Import SQLAlchemy db session
from recommendation.models import Assessment  # Import Assessment model
from datetime import datetime

def generate_quiz_for_course(request, course_id, lecture_id):
    collection_name = f"course_{course_id}"
    mcq_gen = MCQGenerator(api_key=QuizConfig.GROQ_API_KEY, qdrant_url=QuizConfig.QDRANT_URL, collection_name=collection_name)
    result = mcq_gen.generate_mcqs(topic="Generate a comprehensive quiz for the course", num_questions=10)

    if result["status"] == "success":
        try:
            # Store the generated quiz in the `assessments` table
            new_assessment = Assessment(
                course_id=course_id,
                lecture_id=lecture_id,  # Store the related lecture ID
                assessment_data=result["quiz"],  # Store entire quiz data as JSON
                created_at=datetime.utcnow()
            )
            db.session.add(new_assessment)
            db.session.commit()

            return JsonResponse({"status": "success", "message": "Quiz is stored in the assessments table."})
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            return JsonResponse({"status": "error", "message": f"Error storing quiz: {e}"})
    
    return JsonResponse({"status": "error", "message": "Quiz generation failed."})
