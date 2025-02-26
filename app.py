INPUT_DIRECTORY = r'D:\\Wappnet\\repo\\videos'
OUTPUT_DIRECTORY = r'D:\\Wappnet\\repo\\transcription'

import whisper
import os
from config import Config
from quiz import generate_quiz
from sql_ops import SqlOps  # Import your SQL operations module

def transcribe_videos(video_path: str) -> str:
    """Transcribes a video file using Whisper and saves the transcript as a .txt file."""
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    text = result.get("text", "")

    base_name = os.path.splitext(os.path.basename(video_path))[0]
    transcript_path = os.path.join(OUTPUT_DIRECTORY, f"{base_name}.txt")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"Transcription has been saved: {transcript_path}")
    return transcript_path 

def process_transcript(api_key: str = Config.GROQ_API_KEY, folder: str = OUTPUT_DIRECTORY):
    """Processes all transcript .txt files in the output directory to generate quiz JSON files."""
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            transcript_path = os.path.join(folder, file)
            json_path = transcript_path.replace(".txt", ".json")
            if os.path.exists(json_path):
                continue
            generate_quiz(transcript_path, api_key)

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
    transcribe_videos(r"D:\\Wappnet\\repo\\videos\\Gradient descent for multiple linear regression.webm")
    
    # Process transcripts to generate quizzes.
    process_transcript()
    
    # Insert the generated quiz JSON files into PostgreSQL.
    course_id = "08c82434-5790-4162-8409-ef5c662b6d75"  # Replace with your actual course ID
    insert_quizzes(course_id)

if __name__ == '__main__':
    main()
