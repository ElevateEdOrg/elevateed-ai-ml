# recommendation/config.py
import os

class Config:
    """Configuration for the Flask app and database."""
    # Example:
   
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:6YZizt9aFFj2@elevate.cidgqgeogv4w.us-east-1.rds.amazonaws.com:5432/elevatedb"
    #SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #SQLALCHEMY_TRACK_MODIFICATIONS = False
    #SECRET_KEY = "some-secret-key"  # Replace with a real secret in production
