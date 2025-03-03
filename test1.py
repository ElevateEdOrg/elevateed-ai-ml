import os
import json
import logging
import time
import re
from datetime import datetime
from typing import Any, Dict, List, Union

import qdrant_client
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import spacy

# Load spaCy's small English model
nlp = spacy.load("en_core_web_sm")


class QuizParser:
    """Parses raw quiz text into structured JSON format."""
    def parse(self, quiz_text: str) -> List[Dict[str, Any]]:
        questions: List[Dict[str, Any]] = []
        # Split by '---' which separates questions
        raw_questions = [q.strip() for q in quiz_text.split('---') if q.strip()]
        
        for q in raw_questions:
            lines = [line.strip() for line in q.splitlines() if line.strip()]
            if len(lines) < 3:
                continue
            
            question_text = ""
            options: Dict[str, str] = {}
            correct_answer = ""
            explanation = ""
            
            # Find the line starting with "Question:"
            question_index = -1
            for i, line in enumerate(lines):
                if line.lower().startswith("question:"):
                    question_index = i
                    break
                    
            if question_index != -1:
                # Remove the "Question:" label (case insensitive)
                question_text = re.sub(r'(?i)^question\s*\d*\s*:\s*', '', lines[question_index]).strip()
                if not question_text and question_index + 1 < len(lines):
                    question_text = lines[question_index + 1]
            else:
                continue
            
            # Extract options that start with a pattern like "(A)" etc.
            seen_options = set()
            for i, line in enumerate(lines):
                if i > question_index and line.startswith("(") and ")" in line:
                    option_letter = line[1:line.index(")")].strip().upper()
                    option_text = line[line.index(")") + 1:].strip()
                    if option_letter in seen_options:
                        continue
                    seen_options.add(option_letter)
                    options[option_letter] = option_text
            
            # Look for the correct answer
            for line in lines:
                if line.lower().startswith("correct answer:"):
                    answer_match = re.search(r'\(([A-D])\)', line, re.IGNORECASE)
                    if answer_match:
                        correct_answer = f"({answer_match.group(1).upper()})"
                    break
                    
            # Look for explanation
            for line in lines:
                if line.lower().startswith("explanation:"):
                    explanation = line.replace("Explanation:", "").strip()
                    break
            
            # Ensure we have options for A, B, C, D
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


def generate_mcq(sentence: str) -> Union[Dict[str, Any], None]:
    """
    Generate an MCQ from a single sentence using a rule-based approach.
    Example pattern: "Name was born in YYYY."
    Transforms into: "In which year was Name born?"
    """
    pattern = r"^(.*) was born in (\d{4})\.$"
    match = re.match(pattern, sentence.strip())
    if match:
        name = match.group(1).strip()
        year = match.group(2)
        question_text = f"In which year was {name} born?"
        correct_answer = f"({year})"
        # For distractors, you may implement dynamic selection.
        # Here we simply hard-code three alternatives.
        distractors = ["(1959)", "(1965)", "(1970)"]
        options = {
            "A": correct_answer,
            "B": distractors[0],
            "C": distractors[1],
            "D": distractors[2]
        }
        explanation = f"{name} was born in {year}."
        return {
            "question": question_text,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": explanation
        }
    else:
        return None


class MCQGenerator:
    def __init__(self, api_key: str, qdrant_url: str, qdrant_collection: str, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)
        # The original Groq client is no longer used; we rely on our NLP methods.
        # self.groq_client = Groq(api_key=api_key)
        self.qdrant_client = qdrant_client.QdrantClient(qdrant_url)
        self.qdrant_collection = qdrant_collection
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
        self.quiz_parser = QuizParser()
    
    def search_transcript_in_qdrant(self, query: str, top_k: int = 3) -> str:
        """
        Searches for relevant transcript content in Qdrant.
        """
        query_embedding = self.embedding_model.encode(query).tolist()
        search_results = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_embedding,
            limit=top_k
        )
        retrieved_texts = [hit.payload["text"] for hit in search_results]
        return " ".join(retrieved_texts)
    
    def generate_mcqs_nlp(self, query: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
        """
        Generates multiple-choice questions (MCQs) using an in-house NLP method.
        It retrieves transcript content, splits it into sentences via spaCy,
        and applies rule-based MCQ generation on each sentence.
        """
        relevant_content = self.search_transcript_in_qdrant(query)
        if not relevant_content.strip():
            self.logger.error("No relevant content found for quiz generation.")
            return {"status": "error", "message": "No relevant content found for quiz generation."}
        
        # Use spaCy to split the retrieved content into sentences
        doc = nlp(relevant_content)
        sentences = list(doc.sents)
        
        generated_quiz = []
        for sent in sentences:
            mcq = generate_mcq(str(sent))
            if mcq:
                generated_quiz.append(mcq)
            if len(generated_quiz) >= num_questions:
                break
        
        if not generated_quiz:
            self.logger.error("No MCQs could be generated from the content.")
            return {"status": "error", "message": "No MCQs could be generated from the content."}
        
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "num_questions": len(generated_quiz)
        }
        return {"status": "success", "quiz": generated_quiz, "metadata": metadata}
    
    def generate_mcqs(self, query: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
        # Now use our NLP-based MCQ generation method instead of the LLM (Groq)
        return self.generate_mcqs_nlp(query, num_questions)


# Example usage:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Replace with your actual configuration.
    API_KEY = "your_api_key_here"
    QDRANT_URL = "http://localhost:6333"
    QDRANT_COLLECTION = "course_83c94b40-9dc0-4253-b83c-b82218156493"
    
    mcq_generator = MCQGenerator(API_KEY, QDRANT_URL, QDRANT_COLLECTION)
    sample_query = "Cloud Computing"
    result = mcq_generator.generate_mcqs(sample_query, num_questions=5)
    
    if result["status"] == "success":
        print("Generated MCQs:")
        print(json.dumps(result, indent=4))
    else:
        print("Error:", result["message"])
