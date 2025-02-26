import os
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Union
from groq import Groq
import re

class QuizParser:
    """Parses raw quiz text into structured JSON format."""
    
    def parse(self, quiz_text: str) -> List[Dict[str, Any]]:
        """
        Parse quiz text into a structured format with questions, options, correct answers, and explanations.
        
        Args:
            quiz_text (str): Raw quiz text with questions, options, correct answers, explanations, and difficulty.
            
        Returns:
            List[Dict[str, Any]]: List of question dictionaries.
        """
        questions: List[Dict[str, Any]] = []
        # Split on '---' since that's what separates question blocks
        raw_questions = [q.strip() for q in quiz_text.split('---') if q.strip()]
        
        for q in raw_questions:
            # Split into lines and filter out empty lines.
            lines = [line.strip() for line in q.splitlines() if line.strip()]
            if len(lines) < 3:  # Require at least a question, one option, and an answer/explanation.
                continue
            
            question_text = ""
            options: Dict[str, str] = {}
            correct_answer = ""
            explanation = ""
            
            # Find the question text (search for a line starting with "Question:")
            question_index = -1
            for i, line in enumerate(lines):
                if line.lower().startswith("question:"):
                    question_index = i
                    break
                    
            if question_index != -1:
                # Remove "Question:" and any extra numbering
                question_text = re.sub(r'(?i)^question\s*\d*\s*:\s*', '', lines[question_index]).strip()
                # If the line is empty after removal, check the next line
                if not question_text and question_index + 1 < len(lines):
                    question_text = lines[question_index + 1]
            else:
                continue  # Skip if no question is found
            
            # Extract options by checking for lines that start with a parenthesized letter.
            seen_options = set()
            for i, line in enumerate(lines):
                if i > question_index and line.startswith("(") and ")" in line:
                    # Extract the label and text
                    option_letter = line[1:line.index(")")].strip().upper()
                    option_text = line[line.index(")") + 1:].strip()
                    if option_letter in seen_options:
                        continue
                    seen_options.add(option_letter)
                    options[option_letter] = option_text
            
            # Extract correct answer using regex (looking for a pattern like (A))
            for line in lines:
                if line.lower().startswith("correct answer:"):
                    answer_match = re.search(r'\(([A-D])\)', line, re.IGNORECASE)
                    if answer_match:
                        correct_answer = f"({answer_match.group(1).upper()})"
                    break
                    
            # Extract explanation.
            for line in lines:
                if line.lower().startswith("explanation:"):
                    explanation = line.replace("Explanation:", "").strip()
                    break
            
            # Ensure options for A, B, C, and D exist (use empty string if missing)
            for letter in "ABCD":
                if letter not in options:
                    options[letter] = ""
            
            # Build question dictionary if question text exists.
            if question_text:
                question_dict = {
                    "question": question_text,
                    "options": options,
                    "correct_answer": correct_answer,
                    "explanation": explanation
                }
                questions.append(question_dict)
                
        return questions

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

    def generate_mcqs(self, content: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
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
            # Debug: Print the raw quiz text
            #print("Raw quiz text received:\n", quiz_text)

            quiz_structured = self.quiz_parser.parse(quiz_text)
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "num_questions": num_questions
            }
            return {"status": "success", "quiz": quiz_structured, "metadata": metadata}
        except Exception as e:
            self.logger.error(f"Quiz generation failed: {str(e)}")
            return {"status": "error", "message": f"Quiz generation failed: {str(e)}"}

def generate_quiz(transcript_path: str, api_key: str):
    """
    Generates a quiz from a given transcript file.
    
    Reads the transcript, generates MCQs via Groq, and writes the output to a JSON file.
    """
    print(f"Generating quiz for: {transcript_path}")
    
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            text_content = f.read()
        
        if not text_content.strip():
            print("Error: Transcript is empty.")
            return

        mcq_generator = MCQGenerator(api_key=api_key)
        quiz_data = mcq_generator.generate_mcqs(text_content)

        quiz_path = transcript_path.replace(".txt", ".json")
        with open(quiz_path, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, indent=4)

        print(f"Quiz saved: {quiz_path}")
    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
