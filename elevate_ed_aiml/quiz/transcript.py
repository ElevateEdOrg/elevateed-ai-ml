# quiz/transcription.py

import os
import whisper
import logging
from quiz.config import Config

logging.basicConfig(
    filename="transcription.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

OUTPUT_DIRECTORY = Config.TRANSCRIPT_OUTPUT_DIR
if not os.path.exists(OUTPUT_DIRECTORY):
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

def transcribe_video(video_path: str, output_txt_path: str) -> bool:
    if os.path.exists(output_txt_path):
        logging.info(f"Transcript already exists: {output_txt_path}")
        return True
    try:
        model = whisper.load_model("base")
        result = model.transcribe(video_path)
        text = result.get("text", "")
        with open(output_txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        logging.info(f"Transcribed {video_path} -> {output_txt_path}")
        return True
    except Exception as e:
        logging.error(f"Error transcribing {video_path}: {e}")
        return False
