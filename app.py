INPUT_DIRECTORY = r'D:\\Wappnet\\repo\\videos'
OUTPUT_DIRECTORY = r'D:\\Wappnet\\repo\\transcription'

import os
import json
import whisper
from config import Config
from sql_ops import SqlOps
from quiz import MCQGenerator  
from qdrant_ops import store_transcript_in_qdrant, check_transcript_embeddings_exist

def transcribe_video(video_path: str) -> str:
    """
    Transcribes a video file using Whisper and saves the transcript as a .txt file.
    If the transcript already exists, it returns the existing file path.
    """
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    transcript_path = os.path.join(OUTPUT_DIRECTORY, f"{base_name}.txt")
    
    if os.path.exists(transcript_path):
        print(f"Transcript already exists: {transcript_path}")
        return transcript_path

    try:
        model = whisper.load_model("base")
        result = model.transcribe(video_path)
        text = result.get("text", "")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Transcription has been saved: {transcript_path}")
    except Exception as e:
        print(f"Error transcribing {video_path}: {e}")
    
    return transcript_path

def process_transcripts(api_key: str = Config.GROQ_API_KEY, folder: str = OUTPUT_DIRECTORY, course_id: str = "default_course"):
    """
    Processes all transcript (.txt) files in the output directory.
    For each transcript:
      - Checks if transcript embeddings exist in Qdrant; if not, stores them.
      - Generates a quiz JSON file using the stored embeddings (if not already generated).
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            transcript_path = os.path.join(folder, file)
            json_path = transcript_path.replace(".txt", ".json")
            if os.path.exists(json_path):
                print(f"Quiz JSON already exists: {json_path}")
                continue

            # Derive lecture_id from the transcript file name.
            lecture_id = os.path.splitext(file)[0]
            
            try:
                # Check if embeddings for this lecture already exist in Qdrant.
                qdrant_url = Config.QDRANT_URL  # e.g., "http://localhost:6333"
                qdrant_collection = f"course_{course_id}"
                if not check_transcript_embeddings_exist(qdrant_url, qdrant_collection, lecture_id):
                    store_transcript_in_qdrant(course_id, lecture_id, transcript_path)
                else:
                    print(f"Embeddings for {lecture_id} already exist in Qdrant.")
            except Exception as e:
                print(f"Error storing transcript in Qdrant for {lecture_id}: {e}")
                continue

            try:
                # Read transcript content.
                with open(transcript_path, "r", encoding="utf-8") as f:
                    transcript_text = f.read()
                # Use the first 500 characters as the query to retrieve relevant segments.
                query_text = transcript_text[:500]
                
                # Initialize the MCQGenerator with Qdrant details.
                mcq_gen = MCQGenerator(api_key, qdrant_url, qdrant_collection)
                
                # Generate quiz data based on the query.
                quiz_data = mcq_gen.generate_mcqs(query_text)
                
                # Save the generated quiz JSON file.
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(quiz_data, f, indent=4)
                print(f"Quiz saved: {json_path}")
            except Exception as e:
                print(f"Error generating quiz for {lecture_id}: {e}")

def insert_quizzes(course_id: str, folder: str = OUTPUT_DIRECTORY):
    """
    Inserts all generated quiz JSON files from the output directory into the PostgreSQL database.
    """
    sql = SqlOps()
    for file in os.listdir(folder):
        if file.endswith(".json"):
            json_path = os.path.join(folder, file)
            try:
                sql.insert_quiz(course_id=course_id, file_path=json_path)
                print(f"Inserted quiz from {json_path}")
            except Exception as e:
                print(f"Error inserting quiz from {json_path}: {e}")
    sql.close()

def main():
    # Process all video files in the INPUT_DIRECTORY.
    video_extensions = ['.webm', '.mp4', '.mkv']  # Extend this list as needed.
    for file in os.listdir(INPUT_DIRECTORY):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            video_path = os.path.join(INPUT_DIRECTORY, file)
            try:
                transcribe_video(video_path)
            except Exception as e:
                print(f"Error processing video {video_path}: {e}")
    
    # Define your course ID.
    course_id = "0348bcc2-af96-4bbc-9c24-3d80d161927a"  # Replace with your actual course ID
    
    # Process transcripts: store embeddings and generate quizzes.
    process_transcripts(api_key=Config.GROQ_API_KEY, folder=OUTPUT_DIRECTORY, course_id=course_id)
    
    # Insert generated quizzes into PostgreSQL.
    insert_quizzes(course_id, folder=OUTPUT_DIRECTORY)

if __name__ == '__main__':
    main()

# app.py

# from flask import Flask, jsonify
# from recommendation.routes import recommendation_blueprint
# from quiz.routes import quiz_blueprint
# from recommendation.config import Config as RecConfig
# from quiz.config import Config as QuizConfig
# import os

# def create_app():
#     app = Flask(__name__)
    
#     # Load configuration (if both APIs share similar config, you can unify this)
#     # For demonstration, we're just setting a simple secret key.
#     #app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "your-secret-key")
    
#     # Register the blueprints for both APIs.
#     # The Recommendation API endpoints will be available under /api/recommendations
#     app.register_blueprint(recommendation_blueprint, url_prefix='/api/recommendations')
    
#     # The Quiz API endpoints will be available under /api/quiz
#     app.register_blueprint(quiz_blueprint, url_prefix='/api/quiz')
    
#     return app


# app = create_app()

# @app.route("/")
# def index():
#     return "Welcome to the Elevate Ed API. Use /api/recommendations or /api/quiz."


# if __name__ == "__main__":
#     app.run(debug=True)



# # INPUT_DIRECTORY = os.getenv("INPUT_DIRECTORY", r'D:\\Wappnet\\repo\\videos')
# # OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY", r'D:\\Wappnet\\repo\\transcription')

# import os
# import json
# import whisper
# from config import Config
# from sql_ops import SqlOps
# from quiz import MCQGenerator  
# from qdrant_ops import store_transcript_in_qdrant, check_transcript_embeddings_exist

# def transcribe_video(video_path: str) -> str:
#     """
#     Transcribes a video file using Whisper and saves the transcript as a .txt file.
#     If the transcript already exists, it returns the existing file path.
#     """
#     base_name = os.path.splitext(os.path.basename(video_path))[0]
#     transcript_path = os.path.join(OUTPUT_DIRECTORY, f"{base_name}.txt")
    
#     if os.path.exists(transcript_path):
#         print(f"Transcript already exists: {transcript_path}")
#         return transcript_path

#     try:
#         model = whisper.load_model("base")
#         result = model.transcribe(video_path)
#         text = result.get("text", "")
#         with open(transcript_path, "w", encoding="utf-8") as f:
#             f.write(text)
#         print(f"Transcription has been saved: {transcript_path}")
#     except Exception as e:
#         print(f"Error transcribing {video_path}: {e}")
    
#     return transcript_path

# def process_transcripts(api_key: str = Config.GROQ_API_KEY, folder: str = OUTPUT_DIRECTORY, course_id: str = "default_course"):
#     """
#     Processes all transcript (.txt) files in the output directory.
#     For each transcript:
#       - Checks if transcript embeddings exist in Qdrant; if not, stores them.
#       - Generates a quiz JSON file using the stored embeddings (if not already generated).
#     """
#     if not os.path.exists(folder):
#         os.makedirs(folder)
    
#     for file in os.listdir(folder):
#         if file.endswith(".txt"):
#             transcript_path = os.path.join(folder, file)
#             json_path = transcript_path.replace(".txt", ".json")
#             if os.path.exists(json_path):
#                 print(f"Quiz JSON already exists: {json_path}")
#                 continue

#             # Derive lecture_id from the transcript file name.
#             lecture_id = os.path.splitext(file)[0]
            
#             try:
#                 # Check if embeddings for this lecture already exist in Qdrant.
#                 qdrant_url = Config.QDRANT_URL  # e.g., "http://localhost:6333"
#                 qdrant_collection = f"course_{course_id}"
#                 if not check_transcript_embeddings_exist(qdrant_url, qdrant_collection, lecture_id):
#                     store_transcript_in_qdrant(course_id, lecture_id, transcript_path)
#                 else:
#                     print(f"Embeddings for {lecture_id} already exist in Qdrant.")
#             except Exception as e:
#                 print(f"Error storing transcript in Qdrant for {lecture_id}: {e}")
#                 continue

#             try:
#                 # Read transcript content.
#                 with open(transcript_path, "r", encoding="utf-8") as f:
#                     transcript_text = f.read()
#                 # Use the first 500 characters as the query to retrieve relevant segments.
#                 query_text = transcript_text[:500]
                
#                 # Initialize the MCQGenerator with Qdrant details.
#                 mcq_gen = MCQGenerator(api_key, qdrant_url, qdrant_collection)
                
#                 # Generate quiz data based on the query.
#                 quiz_data = mcq_gen.generate_mcqs(query_text)
                
#                 # Save the generated quiz JSON file.
#                 with open(json_path, "w", encoding="utf-8") as f:
#                     json.dump(quiz_data, f, indent=4)
#                 print(f"Quiz saved: {json_path}")
#             except Exception as e:
#                 print(f"Error generating quiz for {lecture_id}: {e}")

# def insert_quizzes(course_id: str, folder: str = OUTPUT_DIRECTORY):
#     """
#     Inserts all generated quiz JSON files from the output directory into the PostgreSQL database.
#     """
#     sql = SqlOps()
#     for file in os.listdir(folder):
#         if file.endswith(".json"):
#             json_path = os.path.join(folder, file)
#             try:
#                 sql.insert_quiz(course_id=course_id, file_path=json_path)
#                 print(f"Inserted quiz from {json_path}")
#             except Exception as e:
#                 print(f"Error inserting quiz from {json_path}: {e}")
#     sql.close()

# def main():
#     # Process all video files in the INPUT_DIRECTORY.
#     video_extensions = ['.webm', '.mp4', '.mkv']  # Extend this list as needed.
#     for file in os.listdir(INPUT_DIRECTORY):
#         if any(file.lower().endswith(ext) for ext in video_extensions):
#             video_path = os.path.join(INPUT_DIRECTORY, file)
#             try:
#                 transcribe_video(video_path)
#             except Exception as e:
#                 print(f"Error processing video {video_path}: {e}")
    
#     # Define your course ID.
#     course_id = "0348bcc2-af96-4bbc-9c24-3d80d161927a"  # Replace with your actual course ID
    
#     # Process transcripts: store embeddings and generate quizzes.
#     process_transcripts(api_key=Config.GROQ_API_KEY, folder=OUTPUT_DIRECTORY, course_id=course_id)
    
#     # Insert generated quizzes into PostgreSQL.
#     insert_quizzes(course_id, folder=OUTPUT_DIRECTORY)

# if __name__ == '__main__':
#     main()

# from flask import Flask, jsonify
# from recommendation.routes import recommendation_blueprint
# from quiz.routes import quiz_blueprint
# from recommendation.config import Config as RecConfig
# from quiz.config import Config as QuizConfig
# import os

# def create_app():
#     app = Flask(__name__)
    
#     # Load configuration (if both APIs share similar config, you can unify this)
#     # For demonstration, we're just setting a simple secret key.
#     #app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "your-secret-key")
    
#     # Register the blueprints for both APIs.
#     # The Recommendation API endpoints will be available under /api/recommendations
#     app.register_blueprint(recommendation_blueprint, url_prefix='/api/recommendations')
    
#     # The Quiz API endpoints will be available under /api/quiz
#     app.register_blueprint(quiz_blueprint, url_prefix='/api/quiz')
    
#     return app

# app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True)