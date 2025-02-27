INPUT_DIRECTORY = r'D:\\Wappnet\\repo\\videos'
OUTPUT_DIRECTORY = r'D:\\Wappnet\\repo\\transcription'

import os
import json
import whisper
from config import Config
from sql_ops import SqlOps
# Import the updated MCQGenerator from quiz.py and the Qdrant ops function.
from quiz import MCQGenerator  
from qdrant_ops import store_transcript_in_qdrant

def transcribe_videos(video_path: str) -> str:
    """
    Transcribes a video file using Whisper and saves the transcript as a .txt file.
    """
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    text = result.get("text", "")

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    transcript_path = os.path.join(OUTPUT_DIRECTORY, f"{base_name}.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Transcription has been saved: {transcript_path}")
    return transcript_path 

def process_transcript(api_key: str = Config.GROQ_API_KEY, folder: str = OUTPUT_DIRECTORY, course_id: str = "default_course"):
    """
    Processes all transcript .txt files in the output directory to store transcript embeddings in Qdrant
    and generate quiz JSON files using the stored embeddings.
    """
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            transcript_path = os.path.join(folder, file)
            json_path = transcript_path.replace(".txt", ".json")
            if os.path.exists(json_path):
                continue

            # Derive a lecture_id from the transcript file name.
            lecture_id = os.path.splitext(file)[0]
            
            # Store transcript embeddings in Qdrant.
            store_transcript_in_qdrant(course_id, lecture_id, transcript_path)
            
            # Read transcript content.
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()
            # Use the first 500 characters as the query to retrieve relevant transcript segments.
            query_text = transcript_text[:500]
            
            # Initialize the MCQGenerator with Qdrant details.
            qdrant_url = Config.QDRANT_URL  # Ensure this is defined in your Config.
            qdrant_collection = f"course_{course_id}"
            mcq_gen = MCQGenerator(api_key, qdrant_url, qdrant_collection)
            
            # Generate quiz data based on the query.
            quiz_data = mcq_gen.generate_mcqs(query_text)
            
            # Save the generated quiz JSON file.
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(quiz_data, f, indent=4)
            
            print(f"Quiz saved: {json_path}")

def insert_quizzes(course_id: str, folder: str = OUTPUT_DIRECTORY):
    """
    Inserts all generated quiz JSON files from the output directory into the PostgreSQL database.
    
    Args:
        course_id (str): The ID of the course to associate with the quiz.
        folder (str): The folder where quiz JSON files are stored.
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
    # Transcribe a specific video file.
    transcribe_videos(r"D:\\Wappnet\\repo\\videos\\1.webm")
    
    # Define your course_id.
    course_id = "0348bcc2-af96-4bbc-9c24-3d80d161927a"  # Replace with your actual course ID
    
    # Process transcripts: store embeddings in Qdrant and generate quizzes.
    process_transcript(api_key=Config.GROQ_API_KEY, folder=OUTPUT_DIRECTORY, course_id=course_id)
    
    # Insert the generated quiz JSON files into PostgreSQL.
    insert_quizzes(course_id, folder=OUTPUT_DIRECTORY)

if __name__ == '__main__':
    main()
