# quiz/config.py

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # FOR QUIZ GENERATION
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # DATABASE CONFIGURATION (PostgreSQL)
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    # IF GROQ IS NOT WORKING, WE WILL USE GEMINI (OPTIONAL)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    # QDRANT
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
