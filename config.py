import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBjSM4OWbQpmS3yOQ7Ucjh8merjU8KCRR4")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # Qdrant configuration
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "file_collection")

    #PostGreSQl configuration
    PG_HOST = "localhost"
    PG_PORT = 5432
    PG_DBNAME = "your_database_name"      # Replace with your database name
    PG_USER = "your_database_user"        # Replace with your PostgreSQL username
    PG_PASSWORD = "your_database_password"  # Replace with your PostgreSQL password
