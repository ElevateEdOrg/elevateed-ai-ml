# recommendation/config.py
import os
from dotenv import load_dotenv

load_dotenv()
class Config:
    """Configuration for the Flask app and database."""
    # Example:
   
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    #SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #SQLALCHEMY_TRACK_MODIFICATIONS = False
    #SECRET_KEY = "some-secret-key"  # Replace with a real secret in production
