from flask import Flask
from flasgger import Swagger
from recommendation.config import Config as RecommendationConfig
from recommendation.database import db
from recommendation.routes import recommendation_blueprint
from quiz.config import Config as QuizConfig
from quiz.routes import quiz_blueprint

def create_app():
    """Create and configure the unified Flask application."""
    app = Flask(__name__)

    # Load configuration (can be merged if necessary)
    app.config.from_object(RecommendationConfig)

    # Initialize shared extensions
    db.init_app(app)  # Initialize SQLAlchemy for recommendation
    Swagger(app)  # Initialize Flasgger (Swagger UI)

    # Register Blueprints to keep routes organized
    app.register_blueprint(recommendation_blueprint, url_prefix='/recommendation')
    app.register_blueprint(quiz_blueprint, url_prefix='/quiz')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False, host="0.0.0.0",port="8000")
