# import google.generativeai as genai
# from config import Config
# from vector_db import QdrantClient
# from typing import Dict, List, Union
# import random
# import json
# import time
# from datetime import datetime

# class AutomatedMCQGenerator:
#     def __init__(self, api_key: str, collection_name: str):
#         """
#         Initialize the Automated MCQ Generator.
        
#         Args:
#             api_key (str): Gemini API key for authentication.
#             collection_name (str): Name of the Qdrant collection to use.
#         """
#         self.configure_gemini(api_key)
#         self.qdrant_client = QdrantClient()
#         self.collection_name = collection_name  # used if needed by new methods in QdrantClient
        
#     @staticmethod
#     def configure_gemini(api_key: str) -> None:
#         """Configure Gemini AI with the provided API key."""
#         genai.configure(api_key=api_key)
    
#     def get_random_documents(self, num_docs: int = 3) -> List[Dict]:
#         """
#         Retrieve random documents from the collection.
        
#         Returns:
#             List[Dict]: List of document payloads.
#         """
#         try:
#             # list_documents() should return a list of document payloads from Qdrant.
#             all_docs = self.qdrant_client.list_documents(self.collection_name)
#             if not all_docs:
#                 return []
#             selected_docs = random.sample(all_docs, min(num_docs, len(all_docs)))
#             return selected_docs
#         except Exception as e:
#             print(f"Error retrieving documents: {str(e)}")
#             return []

#     def get_topic_based_documents(self, topic: str, num_docs: int = 3) -> List[Dict]:
#         """
#         Retrieve documents related to a specific topic.
        
#         Args:
#             topic (str): Topic to filter documents by.
            
#         Returns:
#             List[Dict]: List of relevant document payloads.
#         """
#         try:
#             # search_by_topic() should be implemented in your Qdrant client.
#             return self.qdrant_client.search_by_topic(
#                 self.collection_name, 
#                 topic=topic, 
#                 limit=num_docs
#             )
#         except Exception as e:
#             print(f"Error retrieving topic-based documents: {str(e)}")
#             return []

#     def build_mcq_prompt(self, content: str, num_questions: int = 5) -> str:
#         """Build prompt for MCQ generation."""
#         return f"""
# Generate {num_questions} diverse multiple-choice questions (MCQs) based on the following content.
# Ensure questions:
# - Cover different aspects of the content.
# - Vary in difficulty (easy, medium, hard).
# - Test both factual recall and conceptual understanding.

# Content:
# {content}

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

#     def generate_automated_quiz(
#         self,
#         topic: str = None,
#         num_questions: int = 5,
#         num_docs: int = 3
#     ) -> Dict[str, Union[str, List[Dict]]]:
#         """
#         Generate MCQs automatically from collection content.
        
#         Args:
#             topic (str, optional): Specific topic to generate questions for.
#             num_questions (int): Number of questions to generate.
#             num_docs (int): Number of documents to use.
            
#         Returns:
#             dict: Generated quiz with metadata.
#         """
#         try:
#             # Get documents either by topic or randomly.
#             if topic:
#                 documents = self.get_topic_based_documents(topic, num_docs)
#             else:
#                 documents = self.get_random_documents(num_docs)
            
#             if not documents:
#                 return {"status": "error", "message": "No documents found in collection."}
            
#             # Combine content from documents.
#             combined_content = " ".join(
#                 doc["metadata"].get("text", "") for doc in documents
#             ).strip()
            
#             if not combined_content:
#                 return {"status": "error", "message": "Retrieved documents contain no valid content."}
            
#             # Build the prompt for Gemini AI.
#             prompt = self.build_mcq_prompt(combined_content, num_questions)
#             response = genai.generate_text(model="models/gemini-pro", content = prompt)
            
#             if not response or not response.text:
#                 return {"status": "error", "message": "Failed to generate MCQs."}
            
#             # Create quiz metadata.
#             quiz_metadata = {
#                 "generated_at": datetime.now().isoformat(),
#                 "topic": topic if topic else "Random Selection",
#                 "num_documents_used": len(documents),
#                 "document_ids": [doc.get("id") for doc in documents if doc.get("id")]
#             }
            
#             return {"status": "success", "quiz": response.text, "metadata": quiz_metadata}
            
#         except Exception as e:
#             return {"status": "error", "message": f"Quiz generation failed: {str(e)}"}

#     def schedule_quiz_generation(
#         self,
#         interval_hours: int = 24,
#         topics: List[str] = None,
#         num_questions: int = 5
#     ) -> None:
#         """
#         Schedule automatic quiz generation at specified intervals.
        
#         Args:
#             interval_hours (int): Hours between quiz generations.
#             topics (List[str], optional): List of topics to cycle through.
#             num_questions (int): Number of questions per quiz.
#         """
#         while True:
#             try:
#                 if topics:
#                     for topic in topics:
#                         quiz = self.generate_automated_quiz(topic=topic, num_questions=num_questions)
#                         self.save_quiz(quiz)
#                 else:
#                     quiz = self.generate_automated_quiz(num_questions=num_questions)
#                     self.save_quiz(quiz)
                    
#                 # Wait for the next interval.
#                 time.sleep(interval_hours * 3600)
#             except Exception as e:
#                 print(f"Error in scheduled quiz generation: {str(e)}")
#                 time.sleep(300)  # Wait 5 minutes before retrying.
    
#     def save_quiz(self, quiz: Dict) -> None:
#         """
#         Save generated quiz to storage.
#         Implement according to your storage needs (database, file, etc.).
#         """
#         if quiz.get("status") == "success":
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             filename = f"quiz_{timestamp}.json"
#             with open(filename, 'w', encoding='utf-8') as f:
#                 json.dump(quiz, f, indent=4)
#         else:
#             print("Quiz not generated successfully. Nothing to save.")

# # Example usage (for testing purposes)
# if __name__ == "__main__":
#     # Initialize with your Gemini API key and the collection name (as set in your Qdrant config)
#     quiz_generator = AutomatedMCQGenerator(
#         api_key=Config.GEMINI_API_KEY,
#         collection_name=Config.COLLECTION_NAME
#     )
    
#     # Generate a single quiz based on a topic (or leave topic as None for random documents)
#     quiz = quiz_generator.generate_automated_quiz(topic="Machine Learning", num_questions=5)
#     print(quiz)
    
#     # To schedule regular quiz generation (this is a blocking call):
#     # topics = ["Python", "JavaScript", "Data Structures"]
#     # quiz_generator.schedule_quiz_generation(interval_hours=24, topics=topics, num_questions=5)


"""Default implementation of the AutomatedMCQGenerator class."""
# def generate_mcqs(text: str, num_questions: int = 5):
#     """
#     Generate sample multiple-choice questions (MCQs) based on input text.
#     This dummy implementation simply returns sample questions.
#     Replace this with your actual integration with Gemini AI if needed.
#     """
#     questions = []
#     for i in range(num_questions):
#         question = f"Sample Question {i+1} based on: {text[:50]}..."
#         options = [f"Option {opt}" for opt in ["A", "B", "C", "D"]]
#         answer = options[0]  # Dummy correct answer
#         questions.append({
#             "question": question,
#             "options": options,
#             "answer": answer
#         })
#     return questions


# import re
# import json
# import logging
# from datetime import datetime
# from typing import Dict, List, Union

# from groq import Groq
# from config import Config

# class QuizParser:
#     """
#     Parses the plain-text MCQ output from Groq into a structured dictionary.
#     """
#     def parse(self, quiz_text: str) -> Dict[str, any]:
#         question_blocks = re.split(r'\n*Question \d+:\n', quiz_text)[1:]
#         quiz_dict = {}
#         for idx, block in enumerate(question_blocks, start=1):
#             lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
#             if not lines:
#                 continue

#             # First line is assumed to be the question text.
#             question_text = lines[0]

#             # Extract options that start with (A), (B), etc.
#             options = {}
#             option_pattern = re.compile(r'^\((.)\)\s*(.*)')
#             current_index = 1
#             while current_index < len(lines):
#                 match = option_pattern.match(lines[current_index])
#                 if match:
#                     letter = match.group(1)
#                     option_text = match.group(2)
#                     options[letter] = option_text
#                     current_index += 1
#                 else:
#                     break

#             # Extract remaining fields.
#             correct_answer = ""
#             explanation = ""
#             difficulty = ""
#             for line in lines[current_index:]:
#                 if line.startswith("Correct Answer:"):
#                     correct_answer = line.split("Correct Answer:")[-1].strip()
#                 elif line.startswith("Explanation:"):
#                     explanation = line.split("Explanation:")[-1].strip()
#                 elif line.startswith("Difficulty:"):
#                     difficulty = line.split("Difficulty:")[-1].strip()

#             quiz_dict[f"Q{idx}"] = {
#                 "q": question_text,
#                 "options": options,
#                 "ans": correct_answer,
#                 "explanation": explanation,
#                 "difficulty": difficulty
#             }
#         return quiz_dict

# class MCQGenerator:
#     """
#     Generates MCQs using Groq based on provided text content.
#     """
#     def __init__(self, api_key: str, logger: logging.Logger = None):
#         self.logger = logger or logging.getLogger(__name__)
#         self.groq_client = Groq(api_key=api_key)
#         self.quiz_parser = QuizParser()

#     def build_prompt(self, content: str, num_questions: int = 5) -> str:
#         self.logger.info("Building MCQ prompt")
#         return f"""
# Generate {num_questions} diverse multiple-choice questions (MCQs) based on the following content.
# Ensure questions:
# - Cover different aspects of the content.
# - Vary in difficulty (easy, medium, hard).
# - Test both factual recall and conceptual understanding.

# Content:
# {content}

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
#         """
#         Generate MCQs based on the provided text content.
        
#         Args:
#             content (str): The text content to base the quiz on.
#             num_questions (int): Number of MCQs to generate.
        
#         Returns:
#             dict: A dictionary containing the generated quiz and metadata.
#         """
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

# # Module-level helper function for convenience.
# def generate_mcqs(content: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict]]]:
#     """
#     Convenience function to generate MCQs.
    
#     Args:
#         content (str): Text content to generate MCQs from.
#         num_questions (int): Number of questions to generate.
        
#     Returns:
#         dict: Generated quiz with metadata.
#     """
#     generator = MCQGenerator(api_key=Config.GROQ_API_KEY)
#     return generator.generate_mcqs(content, num_questions)



# import re
# import logging
# from datetime import datetime
# from typing import Dict, List, Union

# from groq import Groq
# from config import Config

# class QuizParser:
#     """
#     Parses the plain-text MCQ output from Groq into a structured dictionary.
#     """
#     def parse(self, quiz_text: str) -> Dict[str, any]:
#         question_blocks = re.split(r'\n*Question \d+:\n', quiz_text)[1:]
#         quiz_dict = {}
#         for idx, block in enumerate(question_blocks, start=1):
#             lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
#             if not lines:
#                 continue

#             # First line is assumed to be the question text.
#             question_text = lines[0]

#             # Extract options that start with (A), (B), etc.
#             options = {}
#             option_pattern = re.compile(r'^\((.)\)\s*(.*)')
#             current_index = 1
#             while current_index < len(lines):
#                 match = option_pattern.match(lines[current_index])
#                 if match:
#                     letter = match.group(1)
#                     option_text = match.group(2)
#                     options[letter] = option_text
#                     current_index += 1
#                 else:
#                     break

#             # Extract additional fields.
#             correct_answer = ""
#             explanation = ""
#             difficulty = ""
#             for line in lines[current_index:]:
#                 if line.startswith("Correct Answer:"):
#                     correct_answer = line.split("Correct Answer:")[-1].strip()
#                 elif line.startswith("Explanation:"):
#                     explanation = line.split("Explanation:")[-1].strip()
#                 elif line.startswith("Difficulty:"):
#                     difficulty = line.split("Difficulty:")[-1].strip()

#             quiz_dict[f"Q{idx}"] = {
#                 "question": question_text,
#                 "options": options,
#                 "answer": correct_answer,
#                 "explanation": explanation,
#                 "difficulty": difficulty
#             }
#         return quiz_dict

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
# Generate {num_questions} diverse multiple-choice questions (MCQs) based on the following content.
# Ensure questions:
# - Cover different aspects of the content.
# - Vary in difficulty (easy, medium, hard).
# - Test both factual recall and conceptual understanding.

# Content:
# {content}

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
    Parses the plain-text MCQ output from Groq into a structured dictionary.
    """
    def parse(self, quiz_text: str) -> Dict[str, any]:
        question_blocks = re.split(r'\n*Question \d+:\n', quiz_text)[1:]
        quiz_dict = {}
        for idx, block in enumerate(question_blocks, start=1):
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if not lines:
                continue

            # First line is assumed to be the question text.
            question_text = lines[0]

            # Extract options that start with (A), (B), etc.
            options = {}
            option_pattern = re.compile(r'^\((.)\)\s*(.*)')
            current_index = 1
            while current_index < len(lines):
                match = option_pattern.match(lines[current_index])
                if match:
                    letter = match.group(1)
                    option_text = match.group(2)
                    options[letter] = option_text
                    current_index += 1
                else:
                    break

            # Extract additional fields.
            correct_answer = ""
            explanation = ""
            difficulty = ""
            for line in lines[current_index:]:
                if line.startswith("Correct Answer:"):
                    correct_answer = line.split("Correct Answer:")[-1].strip()
                elif line.startswith("Explanation:"):
                    explanation = line.split("Explanation:")[-1].strip()
                elif line.startswith("Difficulty:"):
                    difficulty = line.split("Difficulty:")[-1].strip()

            quiz_dict[f"Q{idx}"] = {
                "question": question_text,
                "options": options,
                "answer": correct_answer,
                "explanation": explanation,
                "difficulty": difficulty
            }
        return quiz_dict

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
