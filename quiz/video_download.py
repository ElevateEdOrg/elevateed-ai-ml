# quiz/video_download.py

import os
import requests
import logging

logging.basicConfig(
    filename="video_download.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def download_video_from_url(video_url: str, local_dir: str) -> str:
    """
    Downloads the video from a remote URL to a local directory.
    Returns the local file path, or empty string if failure.
    """
    if not os.path.exists(local_dir):
        os.makedirs(local_dir, exist_ok=True)

    filename = os.path.basename(video_url)
    local_path = os.path.join(local_dir, filename)

    try:
        r = requests.get(video_url, stream=True)
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info(f"Downloaded video from {video_url} to {local_path}")
        return local_path
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return ""
