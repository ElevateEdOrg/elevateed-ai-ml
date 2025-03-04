import re
import logging
import json
import random
import numpy as np
import nltk
from datetime import datetime
from typing import Any, Dict, List, Union
from groq import Groq
import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords

nltk.download('punkt')
nltk.download('stopwords')

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
        self.logger = logger or logging.getLogger(__name__)
        self.groq_client = Groq(api_key=api_key)
        self.qdrant_client = QdrantClient(qdrant_url)
        self.qdrant_collection = qdrant_collection
        self.embedding_model = SentenceTransformer("all-mpnet-base-v2")
        self.quiz_parser = QuizParser()
    
    def search_transcript_in_qdrant(self, query: str, top_k: int = 3) -> str:
        query_embedding = self.embedding_model.encode(query).tolist()
        search_results = self.qdrant_client.search(
            collection_name=self.qdrant_collection,
            query_vector=query_embedding,
            limit=top_k
        )
        
        retrieved_texts = [hit.payload["text"] for hit in search_results]
        return " ".join(retrieved_texts)
    
    def preprocess_text(self, text: str) -> str:
        return text.strip()
    
    def extract_sentences(self, text: str) -> List[str]:
        return sent_tokenize(text)
    
    def compute_tfidf(self, sentences: List[str]):
        vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(sentences)
        feature_names = vectorizer.get_feature_names_out()
        return tfidf_matrix, feature_names, vectorizer
    
    def generate_mcqs(self, query: str, num_questions: int = 5) -> Dict[str, Union[str, List[Dict[str, Any]]]]:
        relevant_content = self.search_transcript_in_qdrant(query)
        if not relevant_content.strip():
            self.logger.error("No relevant content found for quiz generation.")
            return {"status": "error", "message": "No relevant content found for quiz generation."}
        
        sentences = self.extract_sentences(relevant_content)
        tfidf_matrix, feature_names, _ = self.compute_tfidf(sentences)
        
        tfidf_sum = np.squeeze(np.asarray(tfidf_matrix.sum(axis=0)))
        keywords_scores = list(zip(feature_names, tfidf_sum))
        keywords_scores.sort(key=lambda x: x[1], reverse=True)
        top_keywords = [kw for kw, score in keywords_scores[:10]]
        
        mcqs = []
        for i, sentence in enumerate(sentences):
            row = tfidf_matrix[i].toarray().flatten()
            if row.max() == 0:
                continue
            max_index = row.argmax()
            correct_keyword = feature_names[max_index]
            if correct_keyword.lower() not in sentence.lower():
                continue
            
            question_text = sentence.replace(correct_keyword, "______", 1)
            correct_answer = correct_keyword
            
            distractor_pool = [kw for kw in top_keywords if kw.lower() != correct_keyword.lower()]
            if len(distractor_pool) < 3:
                continue
            distractors = random.sample(distractor_pool, 3)
            
            options = [correct_answer] + distractors
            random.shuffle(options)
            option_labels = ['A', 'B', 'C', 'D']
            options_dict = {label: opt for label, opt in zip(option_labels, options)}
            correct_label = [label for label, opt in options_dict.items() if opt == correct_answer][0]
            
            mcq = {
                "question": question_text,
                "options": options_dict,
                "correct_answer": correct_label,
                "explanation": f"The blank was filled by the keyword '{correct_answer}', extracted using TF-IDF."
            }
            mcqs.append(mcq)
            if len(mcqs) >= num_questions:
                break
        
        return {"status": "success", "quiz": mcqs, "metadata": {"generated_at": datetime.now().isoformat()}}
