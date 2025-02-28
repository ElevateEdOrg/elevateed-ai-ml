from flask import Flask
from config import Config
from database import db
from routes import routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()  # Ensure tables exist

    app.register_blueprint(routes)
    return app
