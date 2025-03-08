# Elevate Ed APIs (Flask Version)

This project provides two primary APIs for the Elevate Ed platform built with Flask:

1. **Recommendation API**  
   Returns personalized course recommendations based on user data.

2. **Quiz API**  
   Generates multiple-choice quizzes for courses by aggregating lecture transcript content, searching transcript embeddings in Qdrant, and using the Groq API to generate MCQs. Supports video transcription using Whisper and video downloading.

## Project Structure

```
ELEVATEED-AI-ML/
├── app.py
├── config.py
├── requirements.txt
├── recommendation/
│   ├── __init__.py
│   ├── routes.py
│   ├── services.py
├── quiz/
│   ├── __init__.py
│   ├── routes.py
│   ├── quiz.py
│   ├── qdrant_ops.py
│   ├── transcription.py
│   ├── video_download.py
│   ├── sql_ops.py
├── test_files/
├── research/
└── README.md
```

## Prerequisites

- Python 3.8+
- PostgreSQL database (with tables for lectures, assessments, etc.)
- Qdrant server running (default: http://localhost:6333)
- Groq API access
- Whisper for transcription
- Required Python packages (see `requirements.txt`):
  - Flask
  - Flask-RESTful
  - psycopg2-binary
  - requests
  - sentence-transformers
  - qdrant-client
  - groq
  - whisper
  - python-dotenv
  - flasgger (for Swagger documentation)

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ElevateEdOrg/elevateed-ai-ml.git
   cd elevateed-ai-ml
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   
   # On Linux/MacOS:
   source venv/bin/activate
   
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the project root with:
   ```
   SECRET_KEY=your_secret_key

   # Recommendation API config
   DB_HOST=your_db_host
   DB_PORT=your_db_port
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password

   # Quiz API config
   GROQ_API_KEY=your_groq_api_key
   QDRANT_URL=http://localhost:6333
   TRANSCRIPT_OUTPUT_DIR=/tmp/transcripts
   ```

5. **Run the Server:**
   ```bash
   python app.py
   ```

## API Endpoints

### Recommendation API:
- **GET** `/api/recommendations/<user_id>/`
  - Returns course recommendations for the specified user.

### Quiz API:
- **POST** `/quiz/generate_quiz_for_lecture`
  - Initiates a background job to generate a quiz for the specified lecture
  - Requires a JSON body with the following parameters:
    ```json
    {
      "course_id": "4d4050f3-1501-452d-95fe-01407e5e5ff9",
      "lecture_id": "4d2c60fb-3791-4b99-80ce-0b8ae2222762",
      "video_path": "https://elevateed.s3.us-east-1.amazonaws.com/uploads/videos/1741168608518-Learn-Python.mp4"
    }
    ```
  - Returns a success response indicating the job has been created:
    ```json
    { 
      "message": "Quiz generation job created for lecture 4d2c60fb-3791-4b99-80ce-0b8ae2222762. It will be processed in the background.", 
      "status": "success" 
    }
    ```

## Quiz Generation Background Job

The quiz generation process runs as a background job and performs the following steps:

1. **Download Video**: If the provided `video_path` is a remote URL, the system downloads the video locally.
2. **Transcribe Lecture**: Uses Whisper to transcribe the video content.
3. **Store Embeddings**: Generates and stores transcript embeddings in Qdrant for semantic search.
4. **Generate MCQs**: Uses Groq API to generate multiple-choice questions based on the lecture content and Qdrant retrieval.
5. **Store Results**: Saves the generated quiz JSON in PostgreSQL.

The job is designed to handle long-running operations without blocking the API response, making it suitable for processing large video files. The client can check for quiz completion through a separate endpoint or notification system.

## Setting Up Qdrant for Automatic Startup

To ensure Qdrant service runs automatically on server restart:

### Using systemd (Recommended for Linux servers)

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/qdrant.service
   ```

2. Add the following content (adjust paths as needed):
   ```
   [Unit]
   Description=Qdrant Vector Database Service
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   ExecStart=/path/to/qdrant
   Restart=always
   RestartSec=3
   
   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable qdrant.service
   sudo systemctl start qdrant.service
   ```

4. Verify the service status:
   ```bash
   sudo systemctl status qdrant.service
   ```

## Testing with Swagger

To test your APIs with Swagger UI using flasgger:

1. **Ensure flasgger is installed:**
   ```bash
   pip install flasgger
   ```

2. **Access Swagger UI at:**
   ```
   http://127.0.0.1:5000/apidocs/
   ```

## Production Deployment with PM2

To run your Flask app in production using PM2 with your virtual environment:

1. **Install PM2 globally:**
   ```bash
   npm install -g pm2
   ```

2. **Start your app with PM2:**
   ```bash
   pm2 start app.py --interpreter /home/ubuntu/venv/bin/python
   ```

3. **PM2 Process Management:**
   ```bash
   # List processes
   pm2 list
   
   # View logs
   pm2 logs
   
   # Restart your app
   pm2 restart <app_name>
   
   # Stop your app
   pm2 stop <app_name>
   ```

4. **Configure PM2 to start on system boot:**
   ```bash
   pm2 startup
   # Follow the instructions provided by the command
   pm2 save
   ```

### Optional: Use an Ecosystem File for Advanced Configuration

Create an `ecosystem.config.js` file in your project directory:

```javascript
module.exports = {
  apps: [
    {
      name: 'elevateed-flask-app',
      script: 'app.py',
      interpreter: '/home/ubuntu/venv/bin/python',
      env: {
        NODE_ENV: 'production'
      },
      out_file: './logs/out.log',
      error_file: './logs/error.log',
      autorestart: true
    }
  ]
};
```

Then start your app with:
```bash
pm2 start ecosystem.config.js
```

## Future Enhancements

- Advanced recommendation algorithms using collaborative filtering and content-based methods
- Multi-format content support (PDFs, interactive slides, audio files)
- Performance optimization for large video libraries
- Integration with learning analytics dashboard
- Mobile-friendly API endpoints

## Contribution Guidelines

- Follow best practices for Flask development
- Ensure proper logging and error handling
- Write tests for new features
- Document all APIs using docstrings and update Swagger
- Submit feature updates via pull requests
- Follow PEP 8 style guidelines

## Contact

For questions or contributions, please contact the project team or create an issue in the repository.

## License

This project is licensed under the MIT License.

---

**Author:** Harsh Dadiya  
**Role:** AI/ML Developer