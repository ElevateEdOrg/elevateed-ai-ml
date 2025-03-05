# Elevate Ed APIs (Flask Version)

This project provides two primary APIs for the Elevate Ed platform built with Flask:

1. **Recommendation API**  
   Returns course recommendations based on user data.

2. **Quiz API**  
   Generates multiple-choice quizzes for courses by aggregating lecture transcript content, searching transcript embeddings in Qdrant, and using the Groq API to generate MCQs. It also supports video transcription using Whisper and video downloading if needed.

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
- Groq API access (or an alternative)
- Whisper for transcription (if using video transcription)
- Required Python packages:
  - Flask
  - Flask-RESTful
  - psycopg2-binary
  - requests
  - sentence-transformers
  - qdrant-client
  - groq
  - whisper
  - python-dotenv
  - flasgger (for Swagger documentation, optional)

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ElevateEdOrg/elevateed-ai-ml.git
   cd elevate_ed_flask
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

4. **Configure Environment Variables:** Create a `.env` file in the project root with:
   ```env
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
- `GET /api/recommendations/<user_id>/`
  Returns course recommendations for the specified user.

### Quiz API:
- `POST /api/quiz/generate_quiz_for_course/<course_id>/`
  Generates a quiz for the specified course by aggregating lecture transcripts, performing Qdrant searches, and using Groq to generate MCQs.

## Testing with Swagger

To test your APIs with Swagger UI using flasgger:

1. **Ensure flasgger is installed:**
   ```bash
   pip install flasgger
   ```

2. **Swagger UI is available at:**
   ```
   http://127.0.0.1:5000/apidocs/
   ```

## Future Enhancements

* Advanced recommendation algorithms using collaborative filtering and content-based methods
* Multi-format content support (PDFs, interactive slides, audio files)
* Performance optimization for large video libraries
* Integration with learning analytics dashboard
* Mobile-friendly API endpoints

## Contribution Guidelines

* Follow best practices for Flask development
* Ensure proper logging and error handling
* Write tests for new features
* Document all APIs using docstrings and update Swagger
* Submit feature updates via pull requests
* Follow PEP 8 style guidelines

## Contact

For questions or contributions, please contact the project team or create an issue in the repository.

## License

This project is licensed under the **MIT License**.

**Author**: Harsh Dadiya  
**Role**: AI/ML Developer

---

## Final Notes

- The Quiz API uses your existing quiz generation logic (Groq, Qdrant, Whisper, etc.) with the same endpoints and response format.
- Use Flasgger for interactive testing and Swagger documentation.
- Start the server with `python app.py` and test endpoints at:
  - `http://127.0.0.1:5000/api/recommendations/<user_id>/`
  - `http://127.0.0.1:5000/api/quiz/generate_quiz_for_course/<course_id>/`
  - Swagger UI at `http://127.0.0.1:5000/apidocs/` (if configured).

