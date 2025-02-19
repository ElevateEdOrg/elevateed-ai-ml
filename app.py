from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import os
from file_processor import FileProcessor
from flasgger import Swagger, swag_from

app = Flask(__name__)

# Set upload folder
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Allowed file types
ALLOWED_EXTENSIONS = {"pdf", "ppt", "pptx", "mp3", "wav", "mp4", "avi"}

# Initialize file processor
processor = FileProcessor()

# Swagger Configuration
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "File Upload & Processing API",
        "description": "API to upload and process PDF, PPT, audio, and video files, storing embeddings in Qdrant.",
        "version": "1.0.0"
    },
    "host": "127.0.0.1:5000",
    "schemes": ["http"]
}
swagger = Swagger(app, template=swagger_template)

def allowed_file(filename):
    """Check if the file type is allowed"""
    return filename.split(".")[-1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["POST"])
@swag_from({
    "tags": ["File Upload"],
    "summary": "Upload and process a file",
    "description": "Upload a file (PDF, PPT, MP3, WAV, MP4, AVI) and store it in Qdrant",
    "consumes": ["multipart/form-data"],
    "parameters": [
        {
            "name": "file",
            "in": "formData",
            "type": "file",
            "required": True,
            "description": "The file to be uploaded"
        }
    ],
    "responses": {
        "200": {
            "description": "File stored successfully",
            "examples": {"message": "File stored successfully"}
        },
        "400": {
            "description": "Invalid file or missing file",
            "examples": {"error": "No file part"}
        },
        "500": {
            "description": "Internal server error",
            "examples": {"error": "Failed to store file"}
        }
    }
})
def upload_file():
    """API to upload and process files"""
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type"}), 400

    # Save file to upload folder
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # Process and store the file
    try:
        success = processor.store_file(file_path)
        if success:
            return jsonify({"message": "File stored successfully"}), 200
        else:
            return jsonify({"error": "Failed to store file"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
