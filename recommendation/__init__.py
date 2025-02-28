# recommendation/__init__.py

from flask import Flask
from flasgger import Swagger
from recommendation.config import Config
from recommendation.database import db
from recommendation.routes import recommendation_blueprint

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load config
    app.config.from_object(Config)
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flasgger (Swagger UI)
    swagger = Swagger(app)

    # Register Blueprints
    app.register_blueprint(recommendation_blueprint, url_prefix='/api')
    
    return app
