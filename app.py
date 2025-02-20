from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.utils import secure_filename
import os
from config import Config
from vector_db import QdrantClient
from quiz_generator import generate_mcqs

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = Config.UPLOAD_FOLDER

# Serve openapi.json from the docs/ folder
@app.route("/openapi.json")
def openapi_json():
    docs_path = os.path.join(os.path.dirname(__file__), "docs")
    return send_from_directory(docs_path, "openapi.json")

# Swagger UI setup
SWAGGER_URL = "/swagger"
API_URL = "/openapi.json"
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "File Upload, Processing, and Quiz Generation API"}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

# Root route: redirect to Swagger UI
@app.route("/")
def home():
    return redirect(SWAGGER_URL)

# Initialize Qdrant Client
qdrant_client = QdrantClient()

# File upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)
    if qdrant_client.store_file(file_path):
        return jsonify({"message": "File stored successfully"}), 200
    return jsonify({"error": "Failed to store file"}), 500

# Quiz generation route
@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"quiz": "I cannot generate MCQs without the text content. Please provide the text content."}), 400
    text = data["text"]
    num_questions = data.get("num_questions", 5)
    quiz = generate_mcqs(text, num_questions)
    return jsonify({"quiz": quiz})

if __name__ == "__main__":
    app.run(debug=True)
