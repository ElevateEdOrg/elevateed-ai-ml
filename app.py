from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from file_processor import FileProcessor
from quiz_generator import generate_mcqs
from flasgger import Swagger, swag_from

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

swagger = Swagger(app)

processor = FileProcessor()

@app.route("/upload", methods=["POST"])
@swag_from({
    "tags": ["File Upload"],
    "summary": "Upload and process a file",
    "description": "Store PDF, PPT, MP3, WAV, MP4, AVI in Qdrant",
})
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    if processor.store_file(file_path):
        return jsonify({"message": "File stored successfully"}), 200
    return jsonify({"error": "Failed to store file"}), 500

@app.route("/generate_quiz", methods=["POST"])
def generate_quiz():
    query = request.json.get("query")
    if not query:
        return jsonify({"error": "Missing query parameter"}), 400

    quiz = generate_mcqs(query)
    return jsonify({"quiz": quiz})

if __name__ == "__main__":
    app.run(debug=True)
