import os
import logging
import whisper

logging.basicConfig(
    filename='transcription.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def transcribe_video(file_path: str, output_path: str) -> bool:
    """
    Transcribes a video file using Whisper and saves the transcript as a .txt file.
    If the transcript already exists, it returns the existing file path.

    :param video_path: Path to the video file.
    :return: Path to the transcript text file.
    """

    if os.path.exists(output_path):
        logging.info(f"Transcript already exists: {output_path}")
        return True
    
    try:
        # Load the video file using Whisper
        model = whisper.load_model("base", device="cuda")
        result = model.transcribe(file_path)
        text  = result.get("text","")

        with open(output_path,"w", encoding="utf-8") as f:
            f.write(text)

        logging.info(f"Transcribed file: {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error transcribing file: {e}")
        return False
    

    

    