# quiz/__init__.py

from flask import Flask
from flasgger import Swagger
from quiz.config import Config
from quiz.routes import quiz_blueprint

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(Config)
    
    # Initialize Flasgger (Swagger UI)
    Swagger(app)

    # Register Blueprint
    app.register_blueprint(quiz_blueprint, url_prefix='/api/quiz')

    return app
