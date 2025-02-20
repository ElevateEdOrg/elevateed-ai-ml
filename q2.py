import groq
from config import Config
from vector_db import QdrantClient
from typing import Dict, List, Union
import random
import json
import time
from datetime import datetime

class AutomatedMCQGenerator:
    def __init__(self, api_key: str, collection_name: str):
        """
        Initialize the Automated MCQ Generator.
        
        Args:
            api_key (str): Groq API key for authentication.
            collection_name (str): Name of the Qdrant collection to use.
        """
        self.groq_client = groq.Client(api_key=api_key)
        self.qdrant_client = QdrantClient()
        self.collection_name = collection_name
        
    def get_random_documents(self, num_docs: int = 3) -> List[Dict]:
        """
        Retrieve random documents from the collection.
        
        Returns:
            List[Dict]: List of document payloads.
        """
        try:
            all_docs = self.qdrant_client.list_documents(self.collection_name)
            if not all_docs:
                return []
            return random.sample(all_docs, min(num_docs, len(all_docs)))
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []

    def get_topic_based_documents(self, topic: str, num_docs: int = 3) -> List[Dict]:
        """
        Retrieve documents related to a specific topic.
        
        Args:
            topic (str): Topic to filter documents by.
            
        Returns:
            List[Dict]: List of relevant document payloads.
        """
        try:
            return self.qdrant_client.search_by_topic(
                self.collection_name, 
                topic=topic, 
                limit=num_docs
            )
        except Exception as e:
            print(f"Error retrieving topic-based documents: {str(e)}")
            return []

    def build_mcq_prompt(self, content: str, num_questions: int = 5) -> str:
        """Build prompt for MCQ generation."""
        return f"""
Generate {num_questions} diverse multiple-choice questions (MCQs) based on the following content.
Ensure questions:
- Cover different aspects of the content.
- Vary in difficulty (easy, medium, hard).
- Test both factual recall and conceptual understanding.

Content:
{content}

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

    def generate_automated_quiz(
        self,
        topic: str = None,
        num_questions: int = 5,
        num_docs: int = 3
    ) -> Dict[str, Union[str, List[Dict]]]:
        """
        Generate MCQs automatically from collection content.
        
        Args:
            topic (str, optional): Specific topic to generate questions for.
            num_questions (int): Number of questions to generate.
            num_docs (int): Number of documents to use.
            
        Returns:
            dict: Generated quiz with metadata.
        """
        try:
            documents = self.get_topic_based_documents(topic, num_docs) if topic else self.get_random_documents(num_docs)
            
            if not documents:
                return {"status": "error", "message": "No documents found in collection."}
            
            combined_content = " ".join(
                doc["metadata"].get("text", "") for doc in documents
            ).strip()
            
            if not combined_content:
                return {"status": "error", "message": "Retrieved documents contain no valid content."}
            
            prompt = self.build_mcq_prompt(combined_content, num_questions)
            response = self.groq_client.chat_completion(
                messages=[{"role": "system", "content": "You are an AI trained to generate high-quality MCQs."},
                          {"role": "user", "content": prompt}],
                model="mixtral"
            )
            
            if not response or "choices" not in response or not response["choices"]:
                return {"status": "error", "message": "Failed to generate MCQs."}
            
            quiz_text = response["choices"][0]["message"]["content"]
            
            quiz_metadata = {
                "generated_at": datetime.now().isoformat(),
                "topic": topic if topic else "Random Selection",
                "num_documents_used": len(documents),
                "document_ids": [doc.get("id") for doc in documents if doc.get("id")]
            }
            
            return {"status": "success", "quiz": quiz_text, "metadata": quiz_metadata}
            
        except Exception as e:
            return {"status": "error", "message": f"Quiz generation failed: {str(e)}"}

    def save_quiz(self, quiz: Dict) -> None:
        """
        Save generated quiz to storage.
        """
        if quiz.get("status") == "success":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"quiz_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(quiz, f, indent=4)
        else:
            print("Quiz not generated successfully. Nothing to save.")

# Example usage
if __name__ == "__main__":
    quiz_generator = AutomatedMCQGenerator(
        api_key=Config.GROQ_API_KEY,
        collection_name=Config.COLLECTION_NAME
    )
    
    quiz = quiz_generator.generate_automated_quiz(topic="Machine Learning", num_questions=5)
    print(quiz)
