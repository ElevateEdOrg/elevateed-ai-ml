INPUT_DIRECTORY = r'D:\\Wappnet\\repo\\videos'
OUTPUT_DIRECTORY = r'D:\\Wappnet\\repo\\transcription'

from datetime import datetime
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
    Processes all transcript (.txt) files in the output directory:
      - Checks if transcript embeddings exist in Qdrant; if not, stores them.
      - Generates quiz questions from each transcript and aggregates all questions into a single JSON file.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    all_quiz_questions = []
    qdrant_url = Config.QDRANT_URL  # e.g., "http://localhost:6333"
    qdrant_collection = f"course_{course_id}"
    
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            transcript_path = os.path.join(folder, file)
            # Derive lecture_id from transcript file name.
            lecture_id = os.path.splitext(file)[0]
            
            try:
                if not check_transcript_embeddings_exist(qdrant_url, qdrant_collection, lecture_id):
                    store_transcript_in_qdrant(course_id, lecture_id, transcript_path)
                else:
                    print(f"Embeddings for {lecture_id} already exist in Qdrant.")
            except Exception as e:
                print(f"Error storing transcript in Qdrant for {lecture_id}: {e}")
                continue

            try:
                with open(transcript_path, "r", encoding="utf-8") as f:
                    transcript_text = f.read()
                # Use the first 500 characters as a query to retrieve relevant segments.
                query_text = transcript_text[:500]
                
                # Initialize the MCQGenerator with Qdrant details.
                mcq_gen = MCQGenerator(api_key, qdrant_url, qdrant_collection)
                quiz_data = mcq_gen.generate_mcqs(query_text)
                
                if quiz_data.get("status") == "success":
                    all_quiz_questions.extend(quiz_data.get("quiz", []))
                    print(f"Quiz questions generated for {lecture_id}.")
                else:
                    print(f"Quiz generation failed for {lecture_id}: {quiz_data.get('message')}")
            except Exception as e:
                print(f"Error generating quiz for {lecture_id}: {e}")
    
    # Aggregate all quiz questions into a single JSON file.
    aggregated_quiz_path = os.path.join(folder, f"course_{course_id}_quiz.json")
    aggregated_data = {
        "status": "success",
        "quiz": all_quiz_questions,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "num_videos_processed": len(all_quiz_questions)
        }
    }
    with open(aggregated_quiz_path, "w", encoding="utf-8") as f:
        json.dump(aggregated_data, f, indent=4)
    print(f"Aggregated quiz saved: {aggregated_quiz_path}")


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
