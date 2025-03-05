# # quiz/quiz.py

# import re
# import logging
# from datetime import datetime
# from typing import Any, Dict, List, Union
# from groq import Groq
# import qdrant_client
# from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
# from sentence_transformers import SentenceTransformer

# class QuizParser:
#     """Parses raw quiz text into structured JSON format."""
    
#     def parse(self, quiz_text: str) -> List[Dict[str, Any]]:
#         questions: List[Dict[str, Any]] = []
#         raw_questions = [q.strip() for q in quiz_text.split('---') if q.strip()]
        
#         for q in raw_questions:
#             lines = [line.strip() for line in q.splitlines() if line.strip()]
#             if len(lines) < 3:
#                 continue
            
#             question_text = ""
#             options: Dict[str, str] = {}
#             correct_answer = ""
#             explanation = ""
            
#             question_index = -1
#             for i, line in enumerate(lines):
#                 if line.lower().startswith("question:"):
#                     question_index = i
#                     break
                    
#             if question_index != -1:
#                 question_text = re.sub(r'(?i)^question\s*\d*\s*:\s*', '', lines[question_index]).strip()
#                 if not question_text and question_index + 1 < len(lines):
#                     question_text = lines[question_index + 1]
#             else:
#                 continue
            
#             seen_options = set()
#             for i, line in enumerate(lines):
#                 if i > question_index and line.startswith("(") and ")" in line:
#                     option_letter = line[1:line.index(")")].strip().upper()
#                     option_text = line[line.index(")") + 1:].strip()
#                     if option_letter in seen_options:
#                         continue
#                     seen_options.add(option_letter)
#                     options[option_letter] = option_text
            
#             for line in lines:
#                 if line.lower().startswith("correct answer:"):
#                     answer_match = re.search(r'\(([A-D])\)', line, re.IGNORECASE)
#                     if answer_match:
#                         correct_answer = f"({answer_match.group(1).upper()})"
#                     break
                    
#             for line in lines:
#                 if line.lower().startswith("explanation:"):
#                     explanation = line.replace("Explanation:", "").strip()
#                     break
            
#             for letter in "ABCD":
#                 if letter not in options:
#                     options[letter] = ""
            
#             if question_text:
#                 question_dict = {
#                     "question": question_text,
#                     "options": options,
#                     "correct_answer": correct_answer,
#                     "explanation": explanation
#                 }
#                 questions.append(question_dict)
                
#         return questions

# class MCQGenerator:
#     def __init__(self, api_key: str, qdrant_url: str, qdrant_collection: str, logger: logging.Logger = None) -> None:
#         """
#         Initializes the MCQGenerator.

#         :param api_key: The API key for Groq.
#         :param qdrant_url: URL for the Qdrant service.
#         :param qdrant_collection: Name of the Qdrant collection (e.g., "course_<course_id>").
#         :param logger: Optional logger instance.
#         """
#         self.logger = logger or logging.getLogger(__name__)
#         self.groq_client = Groq(api_key=api_key)
#         self.qdrant_client = qdrant_client.QdrantClient(qdrant_url)
#         self.qdrant_collection = qdrant_collection
#         self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
#         self.quiz_parser = QuizParser()
    
#     def search_transcript_in_qdrant(self, query: str, top_k: int = 3) -> str:
#         """
#         Searches Qdrant for transcript chunks matching the query.

#         :param query: Query text to search transcripts.
#         :param top_k: Number of transcript chunks to retrieve.
#         :return: Combined transcript content as a single string.
#         """
#         query_embedding = self.embedding_model.encode(query).tolist()
#         search_results = self.qdrant_client.search(
#             collection_name=self.qdrant_collection,
#             query_vector=query_embedding,
#             limit=top_k
#         )
        
#         retrieved_texts = [hit.payload["text"] for hit in search_results]
#         return " ".join(retrieved_texts)
    
#     def build_prompt(self, content: str, num_questions: int = 5) -> str:
#         """
#         Builds a prompt for Groq to generate MCQs.

#         :param content: Aggregated transcript content.
#         :param num_questions: The exact number of questions to generate.
#         :return: The prompt string.
#         """
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
# [Question text]
# (A) Option 1
# (B) Option 2
# (C) Option 3
# (D) Option 4
# Correct Answer: (Whole option, e.g., (A))
# Explanation: Brief explanation of the correct answer
# Difficulty: [Easy/Medium/Hard]

# Separate each question with a line containing exactly '---'
#         """
    
#     def generate_mcqs(self, query: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
#         """
#         Generates MCQs by:
#          1) Retrieving relevant transcript content from Qdrant.
#          2) Building a prompt with that content.
#          3) Calling Groq via groq_client.chat() to generate quiz text.
#          4) Parsing the generated text into structured JSON.
#          5) Returning quiz metadata and questions.

#         :param query: The query/topic to retrieve relevant transcript content.
#         :param num_questions: The exact number of MCQs to generate.
#         :return: A dictionary with status and quiz JSON on success.
#         """
#         relevant_content = self.search_transcript_in_qdrant(query)
#         if not relevant_content.strip():
#             self.logger.error("No relevant content found for quiz generation.")
#             return {"status": "error", "message": "No relevant content found for quiz generation."}
        
#         prompt = self.build_prompt(relevant_content, num_questions)
#         try:
#             # Generate quiz using groq_client.chat() directly.
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


import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Union
from groq import Groq
import qdrant_client
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

class QuizParser:
    """Parses raw quiz text into structured JSON format."""
    
    def parse(self, quiz_text: str) -> List[Dict[str, Any]]:
        questions: List[Dict[str, Any]] = []
        raw_questions = [q.strip() for q in quiz_text.split('---') if q.strip()]
        
        for q in raw_questions:
            lines = [line.strip() for line in q.splitlines() if line.strip()]
            if len(lines) < 3:
                continue
            
            question_text = ""
            options: Dict[str, str] = {}
            correct_answer = ""
            explanation = ""
            
            question_index = -1
            for i, line in enumerate(lines):
                if line.lower().startswith("question:"):
                    question_index = i
                    break
                    
            if question_index != -1:
                question_text = re.sub(r'(?i)^question\s*\d*\s*:\s*', '', lines[question_index]).strip()
                if not question_text and question_index + 1 < len(lines):
                    question_text = lines[question_index + 1]
            else:
                continue
            
            seen_options = set()
            for i, line in enumerate(lines):
                if i > question_index and line.startswith("(") and ")" in line:
                    option_letter = line[1:line.index(")")].strip().upper()
                    option_text = line[line.index(")") + 1:].strip()
                    if option_letter in seen_options:
                        continue
                    seen_options.add(option_letter)
                    options[option_letter] = option_text
            
            for line in lines:
                if line.lower().startswith("correct answer:"):
                    answer_match = re.search(r'\(([A-D])\)', line, re.IGNORECASE)
                    if answer_match:
                        correct_answer = f"({answer_match.group(1).upper()})"
                    break
                    
            for line in lines:
                if line.lower().startswith("explanation:"):
                    explanation = line.replace("Explanation:", "").strip()
                    break
            
            for letter in "ABCD":
                if letter not in options:
                    options[letter] = ""
            
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
    def __init__(self, api_key: str, qdrant_url: str, qdrant_collection: str, logger: logging.Logger = None) -> None:
        """
        Initializes the MCQGenerator for lecture-wise quiz generation.

        :param api_key: The API key for Groq.
        :param qdrant_url: URL for the Qdrant service.
        :param qdrant_collection: Name of the Qdrant collection (e.g., "lecture_<lecture_id>").
        :param logger: Optional logger instance.
        """
        self.logger = logger or logging.getLogger(__name__)
        self.groq_client = Groq(api_key=api_key)
        self.qdrant_client = qdrant_client.QdrantClient(qdrant_url)
        self.qdrant_collection = qdrant_collection
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
        self.quiz_parser = QuizParser()
    
    def search_transcript_in_qdrant(self, query: str, top_k: int = 3) -> str:
        """
        Searches Qdrant for transcript chunks matching the query.

        :param query: Query text to search transcripts.
        :param top_k: Number of transcript chunks to retrieve.
        :return: Combined transcript content as a single string.
        """
        query_embedding = self.embedding_model.encode(query).tolist()
        search_results = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_embedding,
            limit=top_k
        )
        
        retrieved_texts = [hit.payload["text"] for hit in search_results]
        return " ".join(retrieved_texts)
    
    def build_prompt(self, content: str, num_questions: int = 5) -> str:
        """
        Builds a prompt for Groq to generate lecture MCQs based on the lecture transcript content.

        :param content: Aggregated transcript content from the lecture.
        :param num_questions: The exact number of questions to generate.
        :return: The prompt string.
        """
        self.logger.info("Building MCQ prompt for lecture content")
        return f"""
Generate {num_questions} multiple-choice questions (MCQs) strictly based on the following lecture content. Each question should be directly answerable solely from the information provided and should not incorporate any external or inferred details.

Lecture Content:
{content}

Ensure each question:
- Is derived exclusively from the provided lecture transcript.
- Covers different aspects of the lecture.
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
    
    def generate_mcqs(self, query: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
        """
        Generates lecture MCQs by:
         1) Retrieving relevant transcript content from Qdrant for the lecture.
         2) Building a prompt with that content.
         3) Calling Groq via groq_client.chat() to generate quiz text.
         4) Parsing the generated text into structured JSON.
         5) Returning quiz metadata and questions.

        :param query: The query/topic to retrieve relevant transcript content (e.g., lecture focus area).
        :param num_questions: The exact number of MCQs to generate.
        :return: A dictionary with status and quiz JSON on success.
        """
        relevant_content = self.search_transcript_in_qdrant(query)
        if not relevant_content.strip():
            self.logger.error("No relevant transcript content found for quiz generation.")
            return {"status": "error", "message": "No relevant transcript content found for quiz generation."}
        
        prompt = self.build_prompt(relevant_content, num_questions)
        try:
            # Generate quiz using groq_client.chat() directly.
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
