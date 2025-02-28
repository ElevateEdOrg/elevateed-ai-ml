# quiz/routes.py

import os
import uuid
from flask import Blueprint, jsonify
from flasgger import swag_from

from quiz.config import Config
from quiz.sql_ops import SqlOps
from quiz.video_download import download_video_from_url
from quiz.transcription import transcribe_video
from quiz.qdrant_ops import store_transcript_in_qdrant
from quiz.quiz import MCQGenerator

quiz_blueprint = Blueprint('quiz', __name__)

@quiz_blueprint.route('/generate_quiz_for_course/<uuid:course_id>', methods=['POST'])
@swag_from({
    'tags': ['Quiz Generation'],
    'parameters': [
        {
            'name': 'course_id',
            'in': 'path',
            'type': 'string',
            'format': 'uuid',
            'required': True,
            'description': 'UUID of the course'
        }
    ],
    'responses': {
        200: {
            'description': 'Quiz generated successfully',
            'examples': {
                'application/json': {
                    'status': 'success',
                    'message': 'Quiz generated and stored in DB'
                }
            }
        },
        400: {
            'description': 'Bad Request'
        },
        500: {
            'description': 'Internal Server Error'
        }
    }
})
def generate_quiz_for_course(course_id):
    """
    Generates a quiz for the given course by:
    1) Finding all lectures for that course in DB.
    2) Downloading each video locally (if it's a remote URL).
    3) Transcribing each lecture.
    4) Storing transcripts & embeddings in Qdrant.
    5) Generating MCQs for the entire course using Groq + Qdrant retrieval.
    6) Storing the quiz JSON in PostgreSQL.

    ---
    produces:
      - application/json
    """
    str_course_id = str(course_id)

    sql_ops = SqlOps()
    lecture_rows = sql_ops.fetch_lecture_paths_for_course(str_course_id)
    if not lecture_rows:
        sql_ops.close()
        return jsonify({
            "status": "error",
            "message": f"No lectures found for course {course_id}"
        }), 400

    local_dir = "E:\\Wappnet internship\\ElevateEdOrg"
    for (lecture_id, video_path) in lecture_rows:
        # Download if it's a remote URL (e.g., S3, HTTP)
        local_video_path = video_path
        if video_path.startswith("http"):
            local_video_path = download_video_from_url(video_path, local_dir)
            if not local_video_path:
                print(f"Failed to download {video_path}")
                continue

        # Transcribe
        transcript_filename = f"{uuid.uuid4()}.txt"
        transcript_path = os.path.join("E:\\Wappnet internship\\ElevateEdOrg", transcript_filename)
        success = transcribe_video(local_video_path, transcript_path)
        if not success:
            print(f"Transcription failed for lecture {lecture_id}")
            continue

        # Store transcript in Qdrant
        store_transcript_in_qdrant(
            course_id=str_course_id,
            lecture_id=str(lecture_id),
            transcript_path=transcript_path
        )

        # Cleanup transcript
        try:
            os.remove(transcript_path)
        except:
            pass

    # Now generate MCQs for the entire course
    mcq_gen = MCQGenerator(
        api_key = Config.GROQ_API_KEY,
        qdrant_url = Config.QDRANT_URL,
        qdrant_collection = f"course_{str_course_id}"
    )

    prompt_topic = "Generate a comprehensive quiz covering all lectures in this course."
    generation_result = mcq_gen.generate_mcqs(prompt_topic,num_questions =5)
    if generation_result.get("status") == "error":
        sql_ops.close()
        return jsonify({"status": "error", "message": "MCQ generation failed"}), 500
    
    quiz_json = generation_result.get("quiz")

    # Store quiz JSON in PostgreSQL
    import json
    temp_quiz_file = f"E:\\Wappnet internship\\ElevateEdOrg{uuid.uuid4()}.json"
    with open(temp_quiz_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(quiz_json, indent=2))

    try:
        sql_ops.insert_quiz(
            course_id=str_course_id,
            file_path=temp_quiz_file
        )
    except Exception as e:
        sql_ops.close()
        return jsonify({"status": "error", "message": f"DB Insert failed: {e}"}), 500

    sql_ops.close()

    # Cleanup quiz file
    try:
        os.remove(temp_quiz_file)
    except:
        pass

    return jsonify({
        "status": "success",
        "message": f"Quiz generated for course {course_id} and stored in DB"
    }), 200
