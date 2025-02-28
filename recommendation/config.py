# recommendation/config.py

class Config:
    """Configuration for the Flask app and database."""
    # Example:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:300282@192.168.10.49:5432/Elevatedb"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #SECRET_KEY = "some-secret-key"  # Replace with a real secret in production
