# quiz/config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # FOR QUIZ GENERATION
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # DATABASE CONFIGURATION (PostgreSQL)
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT", "5432")  # Default port for PostgreSQL
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # Construct the SQLAlchemy Database URI
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # IF GROQ IS NOT WORKING, WE WILL USE GEMINI (OPTIONAL)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # QDRANT
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

