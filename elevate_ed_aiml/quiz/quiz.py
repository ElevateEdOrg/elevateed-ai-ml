# quiz/quiz.py

import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Union
from quiz.qdrant_ops import search_transcript_in_qdrant
from groq import Groq

logging.basicConfig(
    filename="quiz_generation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class QuizParser:
    """Parses raw quiz text into structured JSON format."""
    def parse_quiz_text(self, quiz_text: str) -> List[Dict[str, Any]]:
        questions = []
        blocks = quiz_text.strip().split('---')
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            question_data = {
                "question": "",
                "options": [],
                "correct_answer": "",
                "explanation": ""
            }
            lines = block.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if line_stripped.lower().startswith("question:"):
                    question_data["question"] = re.sub(r'(?i)question:\s*', '', line_stripped).strip()
                elif re.match(r'^\([A-D]\)', line_stripped, re.IGNORECASE):
                    question_data["options"].append(line_stripped)
                elif line_stripped.lower().startswith("correct answer:"):
                    match = re.search(r'([A-D])', line_stripped, re.IGNORECASE)
                    if match:
                        question_data["correct_answer"] = match.group(1).upper()
                elif line_stripped.lower().startswith("explanation:"):
                    explanation_text = re.sub(r'(?i)explanation:\s*', '', line_stripped).strip()
                    question_data["explanation"] = explanation_text
            while len(question_data["options"]) < 4:
                question_data["options"].append("(X) ")
            questions.append(question_data)
        return questions

class MCQGenerator:
    def __init__(self, api_key: str, qdrant_url: str, collection_name: str):
        self.api_key = api_key
        self.qdrant_url = qdrant_url
        self.collection_name = collection_name
        self.parser = QuizParser()
        self.groq_client = Groq(api_key=api_key)
    
    def search_transcript_in_qdrant(self, query: str, top_k: int = 3) -> str:
        return search_transcript_in_qdrant(self.collection_name, query, top_k)
    
    def build_prompt(self, content: str, topic: str, num_questions: int = 10) -> str:
        prompt = f"""
Generate {num_questions} multiple-choice questions (MCQs) strictly based on the following content. Each question should be directly answerable solely from the information provided below and should not incorporate any external or inferred details.

Content:
{content}

Ensure each question:
- Is derived exclusively from the provided text.
- Covers different aspects of the content.
- Varies in difficulty (Easy, Medium, Hard).
- Tests factual recall or understanding of details present in the content.

Format each question as:
Question:
[Question text]
(A) Option 1
(B) Option 2
(C) Option 3
(D) Option 4
Correct Answer: (Whole option, e.g., (A))
Explanation: Brief explanation of the correct answer
Difficulty: [Easy/Medium/Hard]

Separate each question with a line containing exactly '---'
        """
        return prompt.strip()
    
    def generate_mcqs(self, topic: str, num_questions: int = 10, top_k: int = 3) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
        relevant_content = self.search_transcript_in_qdrant(topic, top_k)
        # Convert list to string before calling .strip()
        if isinstance(relevant_content, list):
            relevant_content = " ".join(relevant_content).strip()
        else:
            relevant_content = relevant_content.strip()

        if not relevant_content:
            logging.error("No relevant content found for quiz generation.")
            return {"status": "error", "message": "No relevant content found for quiz generation."}
        # if not relevant_content.strip():
        #     logging.error("No relevant content found for quiz generation.")
        #     return {"status": "error", "message": "No relevant content found for quiz generation."}
        prompt = self.build_prompt(relevant_content, topic, num_questions)
        try:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}]
            )
            if not response or not response.choices:
                logging.error("Failed to generate MCQs.")
                return {"status": "error", "message": "Failed to generate MCQs."}
            quiz_text = response.choices[0].message.content
            quiz_structured = self.parser.parse_quiz_text(quiz_text)
            quiz_data = {
                "generated_at": datetime.utcnow().isoformat(),
                "num_questions": len(quiz_structured),
                "questions": quiz_structured
            }
            return {"status": "success", "quiz": quiz_data}
        except Exception as e:
            logging.error(f"Quiz generation failed: {e}")
            return {"status": "error", "message": f"Quiz generation failed: {e}"}
