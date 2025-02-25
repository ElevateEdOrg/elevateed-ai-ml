import re
import logging
from datetime import datetime
from typing import Dict, List, Union

from groq import Groq
from config import Config

class QuizParser:
    """
    Parses the plain-text MCQ output from Groq into a structured list.
    """
    def parse(self, quiz_text: str) -> List[Dict[str, Dict[str, any]]]:
        question_blocks = re.split(r'\n*Question \d+:\n', quiz_text)[1:]
        quiz_list = []
        
        for idx, block in enumerate(question_blocks, start=1):
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if not lines:
                continue

            # First line is assumed to be the question text.
            question_text = lines[0]

            # Extract options as an array.
            options = []
            option_pattern = re.compile(r'^\((.)\)\s*(.*)')
            current_index = 1
            correct_answer = ""
            
            while current_index < len(lines):
                match = option_pattern.match(lines[current_index])
                if match:
                    option_text = match.group(2)
                    options.append(option_text)
                    current_index += 1
                else:
                    break

            # Extract additional fields.
            explanation = ""
            difficulty = ""
            for line in lines[current_index:]:
                if line.startswith("Correct Answer:"):
                    correct_answer_letter = line.split("Correct Answer:")[-1].strip()
                    # Find the full answer text from options
                    answer_index = "ABCD".index(correct_answer_letter) if correct_answer_letter in "ABCD" else -1
                    correct_answer = options[answer_index] if 0 <= answer_index < len(options) else ""
                elif line.startswith("Explanation:"):
                    explanation = line.split("Explanation:")[-1].strip()
                elif line.startswith("Difficulty:"):
                    difficulty = line.split("Difficulty:")[-1].strip()

            quiz_list.append({
                f"q{idx}": {
                    "q": question_text,
                    "options": options,
                    "ans": correct_answer,  # Store full answer for easy frontend matching
                    "explaination": explanation,
                    "difficulty": difficulty
                }
            })
        
        return quiz_list

class MCQGenerator:
    """
    Generates MCQs using Groq based on provided content.
    """
    def __init__(self, api_key: str, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        self.groq_client = Groq(api_key=api_key)
        self.quiz_parser = QuizParser()

    def build_prompt(self, content: str, num_questions: int = 5) -> str:
        self.logger.info("Building MCQ prompt")
        return f"""
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
(A) Option 1
(B) Option 2
(C) Option 3
(D) Option 4
Correct Answer: (Letter)
Explanation: Brief explanation of the correct answer
Difficulty: [Easy/Medium/Hard]
        """

    def generate_mcqs(self, content: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict]]]:
        if not content.strip():
            self.logger.error("No content provided for quiz generation.")
            return {"status": "error", "message": "No content provided for quiz generation."}

        prompt = self.build_prompt(content, num_questions)
        try:
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}]
            )
            if not response or not response.choices:
                self.logger.error("Failed to generate MCQs.")
                return {"status": "error", "message": "Failed to generate MCQs."}

            quiz_text = response.choices[0].message.content
            quiz_structured = self.quiz_parser.parse(quiz_text)
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "num_questions": num_questions
            }
            return {"status": "success", "quiz": quiz_structured, "metadata": metadata}
        except Exception as e:
            self.logger.error(f"Quiz generation failed: {str(e)}")
            return {"status": "error", "message": f"Quiz generation failed: {str(e)}"}

def generate_mcqs(content: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict]]]:
    """
    Convenience function to generate MCQs from the provided content.
    
    Args:
        content (str): Content to generate MCQs from.
        num_questions (int): Number of questions to generate.
        
    Returns:
        dict: Generated quiz with metadata.
    """
    generator = MCQGenerator(api_key=Config.GROQ_API_KEY)
    return generator.generate_mcqs(content, num_questions)
