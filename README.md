# AI-Powered EdTech Platform - AI/ML Services

## Project Overview
The **AI-Powered EdTech Platform** is a microservices-based learning system designed to enhance student learning through AI-driven assessments and personalized learning recommendations. This repository focuses on the **AI/ML services** within the platform, responsible for generating AI-based quiz questions, evaluating student performance, and recommending personalized learning paths.

## Key Features of AI/ML Services
1. **AI-Driven Assessments**
   - Generate multiple-choice questions (MCQs) dynamically from course content (PDFs, PPTs, audio, video).
   - Use **Gemini AI** to analyze content and create contextual quiz questions.
   - Store and retrieve embedded content using **Qdrant Vector Database**.

2. **Student Performance Evaluation**
   - Analyze quiz responses to determine student strengths and weaknesses.
   - Generate detailed assessment reports.

3. **Personalized Learning Paths**
   - Recommend learning materials based on quiz performance.
   - Suggest additional resources to improve weak areas.

4. **Microservices Architecture**
   - AI/ML services are built using **Flask**.
   - Expose RESTful APIs documented with **Swagger**.
   - Ensure seamless communication with other microservices via **API Gateway**.

## Tech Stack
- **Backend Framework**: Flask
- **Vector Database**: Qdrant
- **AI Model**: Gemini AI
- **API Documentation**: Swagger
- **Storage**: Local file storage (for content processing)
- **Containerization & Deployment**: Docker, AWS

## API Endpoints
| Endpoint                  | Method | Description |
|---------------------------|--------|-------------|
| `/generate-mcq`           | POST   | Generate AI-based quiz questions from course content. |
| `/evaluate-assessment`    | POST   | Analyze student quiz responses and provide feedback. |
| `/get-learning-path`      | GET    | Retrieve personalized learning recommendations. |

## Setup Instructions
1. **Clone the Repository**
   ```bash
   git clone <repo_url>
   cd ai-edtech-ml-services
   ```

2. **Create a Virtual Environment & Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the Flask Server**
   ```bash
   flask run
   ```

4. **Access API Documentation**
   - Open `http://127.0.0.1:5000/swagger/#/` in your browser.

## Success Criteria
- AI-powered quiz generation is functional and accurate.
- Student performance evaluations provide meaningful insights.
- Personalized learning recommendations improve engagement.
- APIs integrate seamlessly with other microservices.

## Contribution Guidelines
- Follow best practices for Flask API development.
- Ensure proper logging and error handling.
- Submit feature updates via pull requests.

## License
This project is licensed under the **MIT License**.

---

**Author**: Harsh Dadiya  
**Role**: AI/ML Developer