# import os
# import uuid
# import json
# from celery import Celery
# from quiz.config import Config
# from quiz.video_download import download_video_from_url
# from quiz.transcription import transcribe_video
# from quiz.qdrant_ops import store_transcript_in_qdrant
# from quiz.quiz import MCQGenerator
# from quiz.sql_ops import SqlOps

# # Configure Celery using your broker URL from the configuration.
# celery_app = Celery('quiz_tasks', broker='redis://localhost:6379/0')

# @celery_app.task
# def generate_quiz_task(course_id, lecture_id, video_path):
#     local_dir = "/home/ubuntu/quiz_data"  # Adjust based on your environment
#     local_video_path = video_path

#     # Download the video if the path is a remote URL.
#     if video_path.startswith("http"):
#         local_video_path = download_video_from_url(video_path, local_dir)
#         if not local_video_path:
#             # Log error or notify failure as needed.
#             return False

#     # Transcribe the video.
#     transcript_filename = f"{uuid.uuid4()}.txt"
#     transcript_path = os.path.join(local_dir, transcript_filename)
#     if not transcribe_video(local_video_path, transcript_path):
#         return False

#     # Store the transcript and its embeddings in Qdrant.
#     store_transcript_in_qdrant(lecture_id=lecture_id, transcript_path=transcript_path)

#     # Generate MCQs using the MCQGenerator.
#     mcq_gen = MCQGenerator(
#         api_key=Config.GROQ_API_KEY,
#         qdrant_url=Config.QDRANT_URL,
#         qdrant_collection=f"lecture_{lecture_id}"
#     )
#     prompt_topic = "Generate a comprehensive quiz covering the lecture content."
#     generation_result = mcq_gen.generate_mcqs(prompt_topic, num_questions=5)
#     if generation_result.get("status") == "error":
#         return False

#     quiz_json = generation_result.get("quiz")

#     # Save the quiz JSON to a temporary file.
#     temp_quiz_file = f"/home/ubuntu/quiz_data{uuid.uuid4()}.json"
#     with open(temp_quiz_file, "w", encoding="utf-8") as f:
#         f.write(json.dumps(quiz_json, indent=2))

#     # Insert the quiz record into PostgreSQL.
#     try:
#         sql_ops = SqlOps()
#         sql_ops.insert_quiz(
#             course_id=course_id,
#             lecture_id=lecture_id,
#             file_path=temp_quiz_file
#         )
#         sql_ops.close()
#     except Exception as e:
#         # Optionally log the error.
#         return False

#     return True


import os
import uuid
import json
from celery import Celery
from quiz.config import Config
from quiz.video_download import download_video_from_url
from quiz.transcription import transcribe_video
from quiz.qdrant_ops import store_transcript_in_qdrant
from quiz.quiz import MCQGenerator
from quiz.sql_ops import SqlOps

from dotenv import load_dotenv
load_dotenv()
# Configure Celery using your broker URL.
celery_app = Celery('quiz_tasks', broker='redis://localhost:6379/0')

@celery_app.task
def generate_quiz_task(course_id, lecture_id, video_path):
    local_dir = os.getenv("OUTPUT_DIRECTORY")  # Adjust based on your environment
    os.makedirs(local_dir, exist_ok=True)
    local_video_path = video_path

    # 1. Download the video if the path is a remote URL.
    if video_path.startswith("http"):
        local_video_path = download_video_from_url(video_path, local_dir)
        if not local_video_path:
            # Log error or notify failure as needed.
            return False

    # 2. Transcription:
    # Name transcript file based on lecture_id.
    transcript_filename = f"transcript_{lecture_id}.txt"
    transcript_path = os.path.join(local_dir, transcript_filename)
    if not os.path.exists(transcript_path):
        # Only transcribe if transcript file doesn't exist.
        if not transcribe_video(local_video_path, transcript_path):
            return False

    # 3. Qdrant embeddings:
    # Use a marker file to indicate that the transcript (and embeddings) have been stored.
    qdrant_marker = os.path.join(local_dir, f"qdrant_{lecture_id}.done")
    if not os.path.exists(qdrant_marker):
        store_transcript_in_qdrant(lecture_id=lecture_id, transcript_path=transcript_path)
        # Create marker file.
        with open(qdrant_marker, "w") as marker:
            marker.write("done")

    # 4. Generate MCQs using the MCQGenerator.
    mcq_gen = MCQGenerator(
        api_key=Config.GROQ_API_KEY,
        qdrant_url=Config.QDRANT_URL,
        qdrant_collection=f"lecture_{lecture_id}"
    )
    prompt_topic = "Generate a comprehensive quiz covering the lecture content."
    generation_result = mcq_gen.generate_mcqs(prompt_topic, num_questions=5)
    if generation_result.get("status") == "error":
        return False

    quiz_json = generation_result.get("quiz")

    # 5. Save the quiz JSON to a file.
    local_dir = os.getenv("OUTPUT_DIRECTORY")
    quiz_filename = f"quiz_{lecture_id}_{uuid.uuid4()}.json"
    quiz_path = os.path.join(local_dir, quiz_filename)
    with open(quiz_path, "w", encoding="utf-8") as quiz_file:
        quiz_file.write(json.dumps(quiz_json, indent=2))


    # 6. Insert the quiz record into PostgreSQL.
    try:
        sql_ops = SqlOps()
        sql_ops.insert_quiz(
            course_id=course_id,
            lecture_id=lecture_id,
            file_path=quiz_path
        )
        sql_ops.close()
    except Exception as e:
        return False

    # 7. Cleanup: delete all files in local_dir except the quiz JSON file.
    for filename in os.listdir(local_dir):
        file_path = os.path.join(local_dir, filename)
        # Keep the quiz JSON file; delete all others.
        if file_path != quiz_path and os.path.isfile(file_path):
            os.remove(file_path)

    return True

