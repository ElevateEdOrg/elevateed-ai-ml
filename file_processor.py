import os
from pathlib import Path
import fitz  # PyMuPDF for PDF processing
from pptx import Presentation
import speech_recognition as sr
from moviepy.editor import AudioFileClip
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

class FileProcessor:
    def __init__(self, collection_name: str = "file_collection_1"):
        # Initialize Qdrant client
        self.client = QdrantClient("localhost", port=6333)
        self.collection_name = collection_name
        
        # Initialize the embedding model
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create collection if it doesn't exist
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=384,  # Vector size for all-MiniLM-L6-v2
                distance=models.Distance.COSINE
            )
        )

    def process_pdf(self, file_path: str) -> str:
        """Extract text from PDF files"""
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def process_ppt(self, file_path: str) -> str:
        """Extract text from PowerPoint files"""
        text = ""
        prs = Presentation(file_path)
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text

    def process_audio(self, file_path: str) -> str:
        """Convert audio to text using speech recognition"""
        recognizer = sr.Recognizer()
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio)
            except sr.UnknownValueError:
                text = "[Unrecognized Audio]"
            except sr.RequestError:
                text = "[Error: Could not request results]"
        return text

    def process_video(self, file_path: str) -> str:
        """Extract audio from video and convert to text"""
        audio_path = "temp_audio.wav"
        video = AudioFileClip(file_path)
        video.write_audiofile(audio_path, codec="pcm_s16le")
        
        text = self.process_audio(audio_path)
        os.remove(audio_path)  # Clean up temporary audio file
        return text

    def store_file(self, file_path: str, metadata: dict = None) -> bool:
        """Store file content in Qdrant"""
        file_path = Path(file_path)
        
        # Process different file types
        if file_path.suffix.lower() == '.pdf':
            text = self.process_pdf(str(file_path))
        elif file_path.suffix.lower() in ['.ppt', '.pptx']:
            text = self.process_ppt(str(file_path))
        elif file_path.suffix.lower() in ['.mp3', '.wav']:
            text = self.process_audio(str(file_path))
        elif file_path.suffix.lower() in ['.mp4', '.avi']:
            text = self.process_video(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")

        # Generate embedding
        embedding = self.model.encode(text).tolist()

        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata.update({
            "filename": file_path.name,
            "file_type": file_path.suffix,
            "file_path": str(file_path)
        })

        # Store in Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=abs(hash(str(file_path))) % (10**12),  # Ensure positive integer ID  
                    vector=embedding,
                    payload=metadata
                )
            ]
        )
        return True  # Assume success if no exception occurs

    def search_similar_files(self, query: str, limit: int = 5):
        """Search for similar files based on text query"""
        query_vector = self.model.encode(query).tolist()
        
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query_vector=query_vector,
            with_payload=True,
            limit=limit
        )
        
        return [{"score": hit.score, "metadata": hit.payload} for hit in search_result]
