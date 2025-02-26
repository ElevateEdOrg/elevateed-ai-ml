# Quiz & Recommendation Cron Job Service

## Overview
This microservice is part of an AI-powered EdTech platform that automates the generation of quiz assessments and personalized learning recommendations from course videos. It operates as a scheduled cron job that:
- Transcribes course videos using OpenAI Whisper
- Generates quizzes from transcripts using Groq LLM
- Updates personalized learning recommendations based on content analysis

## Key Features
- **Automated Video Transcription**: Converts course videos to text using Whisper
- **AI-Driven Quiz Generation**: Creates multiple-choice questions from transcript content
- **Recommendation Updates**: Processes quiz data to update personalized learning paths
- **Scheduled Execution**: Runs periodically to process the latest course content

## Tech Stack
- **Language**: Python 3.x
- **Core Libraries**:
  - Whisper - Video transcription
  - Groq API - LLM-based quiz generation
  - psycopg2 - PostgreSQL database integration
  - schedule - Cron-like job scheduling
- **Database**: PostgreSQL

## Directory Structure
```
your_project/
├── repo/
│   ├── videos/            # Course video storage
│   ├── transcription/     # Transcript and quiz JSON files
│   ├── sql_ops.py         # Database operations
│   ├── quiz.py            # Quiz generation using Groq LLM
│   ├── cron_job.py        # Main service file
│   ├── requirements.txt   # Dependencies
│   ├── config.py          # Configuration settings
│   └── README.md          # Project documentation
```

## Setup & Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ElevateEdOrg/elevateed-ai-ml.git
   cd your_project
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Settings**:
   Update `config.py` with required credentials:
   - Database connection details
   - Groq API key
   - File paths and other settings

## How It Works

1. **Transcription Process**:
   - Service scans the videos directory for new content
   - Each video is transcribed and saved as a text file

2. **Quiz Generation**:
   - For each transcript, the service generates a quiz in JSON format
   - Questions are tailored to the educational content

3. **Database Operations**:
   - Quiz data is inserted into PostgreSQL
   - Recommendation algorithms process content relationships

4. **Scheduling**:
   - The entire workflow runs on a configurable schedule

## Running the Service

**Manual Execution**:
```bash
python cron_job.py
```

**System Scheduler**:
Configure your system's task scheduler to execute the script at desired intervals:
- Linux: Use crontab
- Windows: Use Task Scheduler

## Logging & Monitoring
Operations are logged to `cron_job.log` for debugging and monitoring purposes.

## Future Enhancements
- Advanced recommendation algorithms
- Multi-format content support
- Performance optimization for large video libraries

## Contact
For questions or contributions, please contact the project team or create an issue in the repository.

## Contribution Guidelines
- Follow best practices for Flask API development.
- Ensure proper logging and error handling.
- Submit feature updates via pull requests.

## License
This project is licensed under the **MIT License**.

---

**Author**: Harsh Dadiya  
**Role**: AI/ML Developer