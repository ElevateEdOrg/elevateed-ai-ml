from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_swagger_ui import get_swaggerui_blueprint
from werkzeug.utils import secure_filename
import os
import json
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

# Initialize Qdrant Client (file storage remains available)
qdrant_client = QdrantClient()

# Unified endpoint: Accept file upload or JSON payload to generate quiz.
@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    data = None

    # Check if a file was uploaded.
    if "file" in request.files:
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400
        try:
            # Read the file's content and decode as UTF-8.
            file_content = file.read()
            file_text = file_content.decode("utf-8")
            data = json.loads(file_text)
        except Exception as e:
            return jsonify({"error": f"Failed to process file: {str(e)}"}), 400
    else:
        # If no file, try to get JSON payload directly.
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON content provided."}), 400

    # Ensure the JSON data includes the "content" key.
    if "content" not in data:
        return jsonify({"error": "JSON must contain 'content' key."}), 400

    content = data["content"]
    num_questions = data.get("num_questions", 5)
    
    # Optionally, you could store the file content using QdrantClient if needed.
    # (Uncomment if file upload storage is still desired.)
    # if "file" in request.files:
    #     filename = secure_filename(file.filename)
    #     file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    #     with open(file_path, "wb") as f:
    #         f.write(file_content)
    #     qdrant_client.store_file(file_path)

    quiz = generate_mcqs(content, num_questions)
    return jsonify(quiz)

if __name__ == "__main__":
    app.run(debug=True)
