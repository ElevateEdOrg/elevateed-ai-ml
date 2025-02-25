import re
import logging
from datetime import datetime
from typing import Dict, List, Union

from groq import Groq
from config import Config

# class QuizParser:
#     """
#     Parses the plain-text MCQ output from Groq into a structured list.
#     """
#     def parse(self, quiz_text: str) -> List[Dict[str, Dict[str, any]]]:
#         question_blocks = re.split(r'\n*Question \d+:\n', quiz_text)[1:]
#         quiz_list = []
        
#         for idx, block in enumerate(question_blocks, start=1):
#             lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
#             if not lines:
#                 continue

#             # First line is assumed to be the question text.
#             question_text = lines[0]

#             # Extract options as an array.
#             options = []
#             option_pattern = re.compile(r'^\((.)\)\s*(.*)')
#             current_index = 1
#             correct_answer = ""
            
#             while current_index < len(lines):
#                 match = option_pattern.match(lines[current_index])
#                 if match:
#                     option_text = match.group(2)
#                     options.append(option_text)
#                     current_index += 1
#                 else:
#                     break

#             # Extract additional fields.
#             explanation = ""
#             difficulty = ""
#             for line in lines[current_index:]:
#                 if line.startswith("Correct Answer:"):
#                     correct_answer_part = line.split("Correct Answer:")[-1].strip()
#                     # Extract just the letter, handling both formats: "A" or "(A)"
#                     correct_answer_letter = re.search(r'[A-D]', correct_answer_part).group(0) if re.search(r'[A-D]', correct_answer_part) else ""
#                     # Find the full answer text from options
#                     answer_index = "ABCD".index(correct_answer_letter) if correct_answer_letter in "ABCD" else -1
#                     correct_answer = options[answer_index] if 0 <= answer_index < len(options) else ""
#                 elif line.startswith("Explanation:"):
#                     explanation = line.split("Explanation:")[-1].strip()
#                 elif line.startswith("Difficulty:"):
#                     difficulty = line.split("Difficulty:")[-1].strip()

#             quiz_list.append({
#                 f"q{idx}": {
#                     "q": question_text,
#                     "options": options,
#                     "ans": correct_answer,  # Store full answer for easy frontend matching
#                     "explaination": explanation,
#                     "difficulty": difficulty
#                 }
#             })
        
#         return quiz_list

# class MCQGenerator:
#     """
#     Generates MCQs using Groq based on provided content.
#     """
#     def __init__(self, api_key: str, logger: logging.Logger = None):
#         self.logger = logger or logging.getLogger(__name__)
#         self.groq_client = Groq(api_key=api_key)
#         self.quiz_parser = QuizParser()

#     def build_prompt(self, content: str, num_questions: int = 5) -> str:
#         self.logger.info("Building MCQ prompt")
#         return f"""
# Generate {num_questions} multiple-choice questions (MCQs) strictly based on the following content. Each question should be directly answerable solely from the information provided below and should not incorporate any external or inferred details.

# Content:
# {content}

# Ensure each question:
# - Is derived exclusively from the provided text.
# - Covers different aspects of the content.
# - Varies in difficulty (Easy, Medium, Hard).
# - Tests factual recall or understanding of details present in the content.

# Format each question as:
# Question:
# (A) Option 1
# (B) Option 2
# (C) Option 3
# (D) Option 4
# Correct Answer: (Letter)
# Explanation: Brief explanation of the correct answer
# Difficulty: [Easy/Medium/Hard]
#         """

#     def generate_mcqs(self, content: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict]]]:
#         if not content.strip():
#             self.logger.error("No content provided for quiz generation.")
#             return {"status": "error", "message": "No content provided for quiz generation."}

#         prompt = self.build_prompt(content, num_questions)
#         try:
#             response = self.groq_client.chat.completions.create(
#                 model="mixtral-8x7b-32768",
#                 messages=[{"role": "user", "content": prompt}]
#             )
#             if not response or not response.choices:
#                 self.logger.error("Failed to generate MCQs.")
#                 return {"status": "error", "message": "Failed to generate MCQs."}

#             quiz_text = response.choices[0].message.content
#             quiz_structured = self.quiz_parser.parse(quiz_text)
#             metadata = {
#                 "generated_at": datetime.now().isoformat(),
#                 "num_questions": num_questions
#             }
#             return {"status": "success", "quiz": quiz_structured, "metadata": metadata}
#         except Exception as e:
#             self.logger.error(f"Quiz generation failed: {str(e)}")
#             return {"status": "error", "message": f"Quiz generation failed: {str(e)}"}

# def generate_mcqs(content: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict]]]:
#     """
#     Convenience function to generate MCQs from the provided content.
    
#     Args:
#         content (str): Content to generate MCQs from.
#         num_questions (int): Number of questions to generate.
        
#     Returns:
#         dict: Generated quiz with metadata.
#     """
#     generator = MCQGenerator(api_key=Config.GROQ_API_KEY)
#     return generator.generate_mcqs(content, num_questions)

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
        # Log the raw input to help with debugging
        logging.debug(f"Raw quiz text to parse: {quiz_text}")
        
        # More flexible pattern to match different question formats
        question_blocks = re.split(r'\n*(?:Question|Q\.?)\s*\d+\s*[:.]?\s*', quiz_text, flags=re.IGNORECASE)
        
        # Remove any empty blocks at the beginning
        if question_blocks and not question_blocks[0].strip():
            question_blocks = question_blocks[1:]
            
        if not question_blocks:
            logging.warning("No question blocks identified in the text")
            return []
            
        quiz_list = []
        
        for idx, block in enumerate(question_blocks, start=1):
            logging.debug(f"Processing block {idx}: {block[:100]}...")  # Log first 100 chars of each block
            
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if not lines:
                logging.warning(f"Empty block found at index {idx}")
                continue

            # First line is assumed to be the question text
            question_text = lines[0]
            logging.debug(f"Question text: {question_text}")

            # Extract options as an array
            options = []
            option_indices = []
            
            # More flexible option pattern
            option_pattern = re.compile(r'^(?:\(([A-D])\)|([A-D])[\.\):])\s*(.*)', re.IGNORECASE)
            current_index = 1
            
            while current_index < len(lines):
                line = lines[current_index]
                match = option_pattern.match(line)
                if match:
                    # Get the letter from either group 1 or 2
                    letter = (match.group(1) or match.group(2)).upper()
                    option_text = match.group(3)
                    options.append(option_text)
                    option_indices.append(letter)
                    logging.debug(f"Found option {letter}: {option_text}")
                    current_index += 1
                else:
                    break

            # Extract additional fields
            explanation = ""
            difficulty = ""
            correct_answer = ""
            correct_letter = ""
            
            for line in lines[current_index:]:
                # More flexible matching for the Correct Answer field
                if re.search(r'correct\s+answer', line, re.IGNORECASE):
                    # Extract letter only using regex
                    letter_match = re.search(r'([A-D])', line, re.IGNORECASE)
                    if letter_match:
                        correct_letter = letter_match.group(1).upper()
                        logging.debug(f"Found correct answer letter: {correct_letter}")
                        
                        # Find the index of this letter in our options
                        try:
                            if correct_letter in option_indices:
                                letter_index = option_indices.index(correct_letter)
                                correct_answer = options[letter_index]
                                logging.debug(f"Mapped to answer: {correct_answer}")
                        except Exception as e:
                            logging.error(f"Error mapping answer letter to option: {e}")
                
                # Match explanation
                elif re.search(r'explanation', line, re.IGNORECASE):
                    explanation = re.split(r'explanation\s*:\s*', line, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
                    logging.debug(f"Found explanation: {explanation}")
                
                # Match difficulty
                elif re.search(r'difficulty', line, re.IGNORECASE):
                    difficulty = re.split(r'difficulty\s*:\s*', line, maxsplit=1, flags=re.IGNORECASE)[-1].strip()
                    logging.debug(f"Found difficulty: {difficulty}")

            # If we couldn't find the correct answer by letter, check if there's a line with "Correct:" or similar
            if not correct_answer:
                for line in lines[current_index:]:
                    if re.search(r'\bcorrect\b', line, re.IGNORECASE) and not re.search(r'correct\s+answer', line, re.IGNORECASE):
                        correct_parts = re.split(r'correct\s*:\s*', line, maxsplit=1, flags=re.IGNORECASE)
                        if len(correct_parts) > 1:
                            correct_answer = correct_parts[-1].strip()
                            logging.debug(f"Found correct answer from alternative format: {correct_answer}")

            quiz_list.append({
                f"q{idx}": {
                    "q": question_text,
                    "options": options,
                    "ans": correct_answer,
                    "explaination": explanation,
                    "difficulty": difficulty
                }
            })
            
        logging.info(f"Successfully parsed {len(quiz_list)} questions")
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

Format each question EXACTLY as follows:

Question 1: [Question text here]
(A) Option 1
(B) Option 2
(C) Option 3
(D) Option 4
Correct Answer: [Letter]
Explanation: [Brief explanation of the correct answer]
Difficulty: [Easy/Medium/Hard]

Question 2: [Second question text]
...and so on.

IMPORTANT: Follow this exact format for each question, with 'Question N:' at the start of each question, options labeled (A) through (D), and always include the Correct Answer, Explanation, and Difficulty sections.
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
            # Log the raw response for debugging
            self.logger.info(f"Raw quiz text from Groq: {quiz_text}")
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

def test_parser(sample_text):
    """
    Test the parser with a sample text to debug issues.
    """
    parser = QuizParser()
    print(f"Testing parser with sample text:\n{sample_text}\n")
    
    result = parser.parse(sample_text)
    print(f"Parser output: {result}")
    
    return result

# Uncomment to test the parser with a sample quiz
"""
sample_quiz = \"""
Question 1: What is Python?
(A) A programming language
(B) A snake
(C) A database
(D) A web browser
Correct Answer: A
Explanation: Python is a programming language.
Difficulty: Easy

Question 2: What does SQL stand for?
(A) Structured Query Language
(B) Simple Query Language
(C) System Question Language
(D) Standard Query Logic
Correct Answer: A
Explanation: SQL stands for Structured Query Language.
Difficulty: Medium
\"""

test_parser(sample_quiz)
"""
